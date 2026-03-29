from typing import List, Optional, Dict, Any, Tuple
import json
import os
from pathlib import Path

from pymorphy2 import MorphAnalyzer

# OpenCorpora 将 метать 与 метить 的现在时混在同一词族中，「метаю」类标准形标为 Infr，inflect 默认落到 мечу 词干。
RU_VERB_LEMMA_LEXEME_PREFER_INFR: frozenset = frozenset({"метать"})

# 体配对仅来自词表；以下为少量手工项，合并时覆盖 JSON 中同名键。
RU_VERB_IMPERF_TO_PERF_INFINITIVE: Dict[str, str] = {
    "помогать": "помочь",
    "знать": "узнать",
    "жить": "прожить",
}


def _ru_infn_aspect_from_analyzer(analyzer: MorphAnalyzer, word: str) -> Optional[str]:
    """返回不定式在 OpenCorpora 中的体：impf / perf；非 INFN 或无定体则 None。"""
    for prs in analyzer.parse(word):
        pos_t = str(prs.tag.POS) if hasattr(prs.tag, "POS") and prs.tag.POS else ""
        if pos_t != "INFN":
            continue
        grammemes = {str(g) for g in prs.tag.grammemes}
        if "impf" in grammemes:
            return "impf"
        if "perf" in grammemes:
            return "perf"
    return None


def _filter_ru_aspect_pair_maps_strict(
    imp_to_perf: Dict[str, str], analyzer: MorphAnalyzer
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """丢弃 pymorphy 无法确认为「未完成体 INFN → 完成体 INFN」的项；反向表由通过项唯一生成，避免 JSON 与校验不一致。"""
    good_imp: Dict[str, str] = {}
    for i_lemma, p_lemma in imp_to_perf.items():
        if _ru_infn_aspect_from_analyzer(analyzer, i_lemma) != "impf":
            continue
        if _ru_infn_aspect_from_analyzer(analyzer, p_lemma) != "perf":
            continue
        good_imp[i_lemma] = p_lemma
    good_perf: Dict[str, str] = {}
    for i_lemma, p_lemma in good_imp.items():
        if p_lemma in good_perf:
            continue
        good_perf[p_lemma] = i_lemma
    return good_imp, good_perf


def _load_ru_verb_aspect_pair_json() -> Dict[str, str]:
    """从 app/data/ru_verb_aspect_pairs.json 读取 imperf→perf；反向表仅由校验后的正向表生成。"""
    data_path = Path(__file__).resolve().parent.parent / "data" / "ru_verb_aspect_pairs.json"
    if not data_path.is_file():
        return {}
    try:
        with data_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        raw_imp = payload.get("imperf_to_perf") or {}
        if not isinstance(raw_imp, dict):
            return {}
        return {str(k).lower(): str(v).lower() for k, v in raw_imp.items()}
    except Exception:
        return {}


_JSON_IMP_TO_PERF = _load_ru_verb_aspect_pair_json()
# 合并手工表后做严格校验；宁可丢条目也不返回体标签矛盾的配对。
_ASPECT_VALIDATOR = MorphAnalyzer()
_MERGED_IMP_BEFORE_VALIDATE: Dict[str, str] = {**_JSON_IMP_TO_PERF, **RU_VERB_IMPERF_TO_PERF_INFINITIVE}
RU_VERB_ASPECT_IMP_TO_PERF, RU_VERB_ASPECT_PERF_TO_IMP = _filter_ru_aspect_pair_maps_strict(
    _MERGED_IMP_BEFORE_VALIDATE, _ASPECT_VALIDATOR
)

PROPER_NOUN_PENALTY: float = 0.45
ANIMATE_PENALTY: float = 0.05
INANIMATE_BONUS: float = 0.03
NORMAL_FORM_BONUS: float = 0.08
VERB_BONUS: float = 0.15  # 动词优先权重

# 俄语名词不规则复数纠正表（pymorphy2 词典中部分词给出错误复数，此处覆盖）
# 键：原形（normal_form）；值：复数六格形式 nomn, gent, datv, accs, ablt, loct
RU_NOUN_PLURAL_OVERRIDES: Dict[str, Dict[str, str]] = {
    "стул": {"nomn": "стулья", "gent": "стульев", "datv": "стульям", "accs": "стулья", "ablt": "стульями", "loct": "стульях"},
    "дерево": {"nomn": "деревья", "gent": "деревьев", "datv": "деревьям", "accs": "деревья", "ablt": "деревьями", "loct": "деревьях"},
    "брат": {"nomn": "братья", "gent": "братьев", "datv": "братьям", "accs": "братьев", "ablt": "братьями", "loct": "братьях"},
    "друг": {"nomn": "друзья", "gent": "друзей", "datv": "друзьям", "accs": "друзей", "ablt": "друзьями", "loct": "друзьях"},
    "сын": {"nomn": "сыновья", "gent": "сыновей", "datv": "сыновьям", "accs": "сыновей", "ablt": "сыновьями", "loct": "сыновьях"},
    "крыло": {"nomn": "крылья", "gent": "крыльев", "datv": "крыльям", "accs": "крылья", "ablt": "крыльями", "loct": "крыльях"},
    "лист": {"nomn": "листья", "gent": "листьев", "datv": "листьям", "accs": "листья", "ablt": "листьями", "loct": "листьях"},
    "муж": {"nomn": "мужья", "gent": "мужей", "datv": "мужьям", "accs": "мужей", "ablt": "мужьями", "loct": "мужьях"},
    "перо": {"nomn": "перья", "gent": "перьев", "datv": "перьям", "accs": "перья", "ablt": "перьями", "loct": "перьях"},
}


class MorphologyService:
    """词形分析服务（Service）。

    针对俄语（ru）与乌克兰语（uk）提供解析与变形，封装 pymorphy2。
    """

    def __init__(self, language: str = "ru") -> None:
        if language not in {"ru", "uk"}:
            raise ValueError("language must be 'ru' or 'uk'")
        self.language = language

        # 允许通过环境变量覆盖词典路径：
        # 优先 MORPH_RU_DICT_PATH / MORPH_UK_DICT_PATH；其次 MORPH_DICTS_DIR/<lang>
        dict_path: Optional[str] = None
        per_lang_env = os.getenv("MORPH_RU_DICT_PATH" if language == "ru" else "MORPH_UK_DICT_PATH")
        if per_lang_env and per_lang_env.strip():
            dict_path = per_lang_env.strip()
        else:
            base_dir = os.getenv("MORPH_DICTS_DIR")
            if base_dir and base_dir.strip():
                dict_path = os.path.join(base_dir.strip(), language)

        try:
            if dict_path:
                self.analyzer = MorphAnalyzer(lang=language, path=dict_path)
            else:
                self.analyzer = MorphAnalyzer(lang=language)
        except Exception as exc:
            # 抛出更清晰的异常，便于生产环境快速定位
            hint = (
                f"pymorphy2 词典加载失败 (lang={language}). "
                f"可设置环境变量 MORPH_{language.upper()}_DICT_PATH 指向词典目录，"
                f"或设置 MORPH_DICTS_DIR=<根目录>，其下包含 {language}/ 子目录。原始错误: {exc}"
            )
            raise RuntimeError(hint)

    def _select_best_parse(self, word: str, parses, prefer_verb: bool = False) -> Any:
        """根据启发式对 pymorphy2 解析结果加权，避免普通名词被人名覆盖。
        
        Args:
            word: 待分析的单词
            parses: pymorphy2 解析结果列表
            prefer_verb: 是否优先选择动词解析（用于动词变位等场景）
        """
        if not parses:
            raise ValueError("pymorphy2 解析结果为空，无法选择最佳词形")
        normalized_word: str = word.lower()
        is_lowercase_word: bool = word.islower()
        best_parse = parses[0]
        best_score: float = float("-inf")
        for parse in parses:
            weight: float = float(parse.score)
            grammemes = {str(g) for g in parse.tag.grammemes}
            pos = str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag)
            
            # 如果明确需要动词，优先选择动词解析
            if prefer_verb and pos in ["VERB", "INFN"]:
                weight += VERB_BONUS
            
            if is_lowercase_word and {"Name", "Surn", "Patr"} & grammemes:
                weight *= PROPER_NOUN_PENALTY
            if "anim" in grammemes:
                weight -= ANIMATE_PENALTY
            if "inan" in grammemes:
                weight += INANIMATE_BONUS
            if parse.normal_form.lower() == normalized_word:
                weight += NORMAL_FORM_BONUS
            if weight > best_score:
                best_score = weight
                best_parse = parse
        return best_parse

    def _ru_verb_present_indicative_from_lexeme_infr(self, parse: Any, person: str, number: str) -> Optional[str]:
        """俄语：对 RU_VERB_LEMMA_LEXEME_PREFER_INFR 从 lexeme 取带 Infr 的现在时陈述式，避免 inflect 命中错误词干。"""
        if self.language != "ru":
            return None
        if parse.normal_form.lower() not in RU_VERB_LEMMA_LEXEME_PREFER_INFR:
            return None
        try:
            for fp in parse.lexeme:
                g = {str(x) for x in fp.tag.grammemes}
                if not g >= {"VERB", "pres", "indc", person, number}:
                    continue
                if "impr" in g:
                    continue
                if "Infr" not in g:
                    continue
                return fp.word
        except Exception:
            pass
        return None

    def _ru_replace_inflected_with_infr_lexeme_twin(self, parse: Any, inflected: Any) -> Optional[str]:
        """与 inflect 结果语法标签一致且 lexeme 中存在带 Infr 的词条时，改用该形式（用于不定式按格生成形动词等）。"""
        if self.language != "ru":
            return None
        if parse.normal_form.lower() not in RU_VERB_LEMMA_LEXEME_PREFER_INFR:
            return None
        try:
            ig = {str(x) for x in inflected.tag.grammemes}
            for fp in parse.lexeme:
                fg = {str(x) for x in fp.tag.grammemes}
                if "Infr" not in fg:
                    continue
                if ig <= fg:
                    return fp.word
        except Exception:
            pass
        return None

    def analyze(
        self,
        word: str,
        grammemes: Optional[List[str]] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """解析并尝试按 grammemes 变形。"""
        parses = self.analyzer.parse(word)

        items: List[Dict[str, Any]] = []
        for p in parses[:limit]:
            item: Dict[str, Any] = {
                "normal_form": p.normal_form,
                "tag": str(p.tag),
                "score": float(p.score),
                "methods_stack": [str(m) for m in p.methods_stack],
                "grammemes": sorted([str(g) for g in p.tag.grammemes]),
            }
            if grammemes:
                try:
                    inflected = p.inflect(set(grammemes))
                except Exception:
                    inflected = None
                if inflected is not None:
                    item["inflected"] = {"word": inflected.word, "tag": str(inflected.tag)}
            items.append(item)

        return {"input": word, "language": self.language, "parses": items}

    # ---- declension ----
    def build_declension(self, word: str, preferred_parse: Optional[Any] = None) -> Dict[str, Any]:
        """生成名词的变格表（六格×单/复）。非名词将尽量给出同构标签的变形。
        
        对于名词（NOUN）和代词（NPRO），优先使用 lexeme 从词典获取所有形式，
        以正确呈现不规则复数（如 стул → стулья）；缺失的单元格再通过 inflect 补全。
        
        Args:
            word: 待分析的单词
            preferred_parse: 优先使用的解析（如果提供，将使用此解析而不是自动选择）
        """
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "normal_form": word,
                "pos": "UNKNOWN",
                "cells": [],
            }

        # 如果提供了 preferred_parse，使用它；否则优先选择 NOUN 或 NPRO 解析
        if preferred_parse:
            best = preferred_parse
        else:
            # 优先选择 NOUN 或 NPRO 解析
            noun_parse = next((p for p in parses if (hasattr(p.tag, "POS") and p.tag.POS in ["NOUN", "NPRO"]) or "NOUN" in str(p.tag) or "NPRO" in str(p.tag)), None)
            if noun_parse:
                best = noun_parse
            else:
                best = self._select_best_parse(word, parses)
        
        pos = str(best.tag.POS) if hasattr(best.tag, "POS") else str(best.tag)

        gender = None
        for g in ("masc", "femn", "neut"):
            if g in str(best.tag):
                gender = g
                break

        cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
        numbers = ["sing", "plur"]

        cells: List[Dict[str, Optional[str]]] = []
        
        # 需要跳过的特殊标记：古语变体（V-be/V-bi）、缩写（Abbr）、口语形式（Infr）
        # 这些形式不应出现在标准变格表中，否则会导致每格出现双倍条目（-ие/-ье 混淆等）
        SKIP_TAGS: frozenset = frozenset({"V-be", "V-bi", "Abbr", "Infr"})

        # 对于名词（NOUN）和代词（NPRO），优先使用 lexeme 从词典获取所有形式（含不规则复数，如 стул→стулья）
        if pos in ("NOUN", "NPRO"):
            try:
                lexeme = best.lexeme
                # 从 lexeme 中提取所有形式
                for form_parse in lexeme:
                    form_grammemes = {str(g) for g in form_parse.tag.grammemes}

                    # 跳过古语变体（V-be/V-bi）、缩写（Abbr）、口语（Infr）等非标准形式
                    # 根本原因之一：这些形式曾导致 настроение/понимание 复数每格出现 -ие/-ье 双条目
                    # 根本原因之二：год 的 lexeme 包含 гг（Abbr）、года复数（Infr）等污染数据
                    if form_grammemes & SKIP_TAGS:
                        continue

                    case = next((c for c in cases if c in form_grammemes), None)
                    number = next((n for n in numbers if n in form_grammemes), None)
                    form_gender = next((g for g in ["masc", "femn", "neut"] if g in form_grammemes), gender)

                    if case and number:
                        # 去重检测：
                        # - 单数：匹配 case + number + gender（三者均相同才算同一格）
                        # - 复数：只匹配 case + number（复数本身不分性，存储时 gender=None；
                        #   旧逻辑的 bug 正在此：复数 cell 存储 gender=None，但比较时
                        #   form_gender 为 "neut"，导致 None != "neut" → 每个变体都被当作新格）
                        existing = None
                        for c in cells:
                            case_match = c.get("case") == case
                            number_match = c.get("number") == number
                            if not (case_match and number_match):
                                continue
                            if number == "sing":
                                # 单数需检查性（gender）
                                gender_match = (
                                    c.get("gender") == form_gender
                                    or (c.get("gender") is None and form_gender is None)
                                )
                                if not gender_match:
                                    continue
                            # 找到匹配的已有单元格，不重复添加
                            existing = c
                            break

                        if not existing:
                            cells.append({
                                "case": case,
                                "number": number,
                                "gender": form_gender if number == "sing" else None,
                                "form": form_parse.word,
                            })
            except Exception:
                # 如果 lexeme 不可用，回退到标准方法
                pass
        
        # 标准方法：尝试生成所有格和数的组合
        for case in cases:
            for number in numbers:
                # 如果已经通过 lexeme 获取了该单元格，跳过
                existing = next((c for c in cells if c.get("case") == case and c.get("number") == number), None)
                if existing:
                    continue
                
                grammemes: List[str] = [case, number]
                if gender and number == "sing":
                    grammemes.append(gender)
                form = None
                try:
                    inflected = best.inflect(set(grammemes))
                except Exception:
                    inflected = None
                if inflected is not None:
                    form = inflected.word
                    twin = self._ru_replace_inflected_with_infr_lexeme_twin(best, inflected)
                    if twin is not None:
                        form = twin
                
                # 只有当 form 不为 None 时才添加，或者如果还没有该单元格则添加空单元格
                if form or not existing:
                    cells.append({
                    "case": case,
                    "number": number,
                    "gender": gender if number == "sing" else None,
                    "form": form,
                })

        # 应用俄语名词不规则复数纠正表（词典中部分词复数错误，如 стул→стулья）
        if self.language == "ru" and pos == "NOUN":
            nf_lower = best.normal_form.lower()
            if nf_lower in RU_NOUN_PLURAL_OVERRIDES:
                overrides = RU_NOUN_PLURAL_OVERRIDES[nf_lower]
                for cell in cells:
                    if cell.get("number") == "plur" and cell.get("case") in overrides:
                        cell["form"] = overrides[cell["case"]]

        return {
            "input": word,
            "language": self.language,
            "normal_form": best.normal_form,
            "pos": pos,
            "cells": cells,
        }

    def build_adjective_declension(self, word: str, preferred_parse: Optional[Any] = None) -> Dict[str, Any]:
        """生成形容词的变格表（六格×单/复×三性）。
        
        Args:
            word: 待分析的单词
            preferred_parse: 优先使用的解析（如果提供，将使用此解析而不是自动选择）
        """
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "normal_form": word,
                "pos": "UNKNOWN",
                "cells": [],
            }

        # 如果提供了 preferred_parse，使用它；否则优先选择 ADJF 或 ADJS 解析
        if preferred_parse:
            best = preferred_parse
        else:
            # 优先选择 ADJF 或 ADJS 解析
            adj_parse = next((p for p in parses if (hasattr(p.tag, "POS") and p.tag.POS in ["ADJF", "ADJS"]) or "ADJF" in str(p.tag) or "ADJS" in str(p.tag)), None)
            if adj_parse:
                best = adj_parse
            else:
                best = self._select_best_parse(word, parses)
        
        pos = str(best.tag.POS) if hasattr(best.tag, "POS") else str(best.tag)

        cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
        numbers = ["sing", "plur"]
        genders = ["masc", "femn", "neut"]

        cells: List[Dict[str, Optional[str]]] = []
        for case in cases:
            for number in numbers:
                # 复数不区分性（形容词复数对三性相同），只生成一次；
                # 单数需要分别生成三性。
                # 旧代码 bug：plur 也进入 gender 循环，导致每格生成 3 条相同记录。
                iter_genders = genders if number == "sing" else [None]
                for gender in iter_genders:
                    # 宾格需要区分有生/无生
                    if case == "accs":
                        # 单数阳性宾格 + 所有复数宾格：需要 anim/inan 两种形式
                        if (number == "sing" and gender == "masc") or number == "plur":
                            for animacy in ("anim", "inan"):
                                grammemes_a: List[str] = [case, number, animacy]
                                if number == "sing" and gender:
                                    grammemes_a.append(gender)
                                form_a = None
                                try:
                                    inf_a = best.inflect(set(grammemes_a))
                                except Exception:
                                    inf_a = None
                                if inf_a is not None:
                                    form_a = inf_a.word
                                if form_a:
                                    cells.append({
                                        "case": case,
                                        "number": number,
                                        "gender": gender,
                                        "animacy": animacy,
                                        "form": form_a,
                                    })
                        else:
                            # 单数阴性、中性宾格：不分有生/无生
                            grammemes: List[str] = [case, number]
                            if number == "sing" and gender:
                                grammemes.append(gender)
                            form = None
                            try:
                                inflected = best.inflect(set(grammemes))
                            except Exception:
                                inflected = None
                            if inflected is not None:
                                form = inflected.word
                            cells.append({
                                "case": case,
                                "number": number,
                                "gender": gender,
                                "form": form,
                            })
                    else:
                        # 非宾格：单数按性生成，复数只生成一次
                        grammemes: List[str] = [case, number]
                        if number == "sing" and gender:
                            grammemes.append(gender)
                        form = None
                        try:
                            inflected = best.inflect(set(grammemes))
                        except Exception:
                            inflected = None
                        if inflected is not None:
                            form = inflected.word
                        cells.append({
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "form": form,
                        })
        
        # 添加短尾形式和比较级（如果存在）
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                form_tag_str = str(form_parse.tag)
                
                # 检查是否是短尾形式
                if ("shrt" in form_grammemes or "PRTS" in form_grammemes or 
                    "ADJS" in form_tag_str or "shrt" in form_tag_str):
                    number = next((n for n in numbers if n in form_grammemes), "sing")
                    gender = next((g for g in genders if g in form_grammemes), None) if number == "sing" else None
                    
                    # 检查是否已存在
                    existing = next((c for c in cells if c.get("short") == True and 
                                    c.get("number") == number and c.get("gender") == gender), None)
                    if not existing:
                        cells.append({
                            "case": None,
                            "number": number,
                            "gender": gender,
                            "form": form_parse.word,
                            "short": True,
                        })
                
                # 检查是否是比较级
                if "COMP" in form_grammemes or "Cmp2" in form_grammemes:
                    # 检查是否已存在该比较级形式
                    existing = next((c for c in cells if c.get("comparative") == True and 
                                    c.get("form") == form_parse.word), None)
                    if not existing:
                        cells.append({
                            "case": None,
                            "number": None,
                            "gender": None,
                            "form": form_parse.word,
                            "comparative": True,
                        })
        except Exception:
            pass

        return {
            "input": word,
            "language": self.language,
            "normal_form": best.normal_form,
            "pos": pos,
            "cells": cells,
        }

    def build_verb_conjugation(self, word: str, preferred_parse: Optional[Any] = None) -> Dict[str, Any]:
        """生成动词的完整变位表（时态×人称×数 + 副动词 + 命令式 + 形动词）。
        
        Args:
            word: 待分析的单词
            preferred_parse: 优先使用的解析（如果提供，将使用此解析而不是自动选择）
        """
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "normal_form": word,
                "pos": "UNKNOWN",
                "cells": [],
            }

        # 如果提供了 preferred_parse，使用它；否则优先选择动词解析
        if preferred_parse:
            best = preferred_parse
        else:
            best = self._select_best_parse(word, parses, prefer_verb=True)
        pos = str(best.tag.POS) if hasattr(best.tag, "POS") else str(best.tag)

        # 检查原词是否是及物动词（tran），如果是，则带 -ся 的形式可能是被动语态
        best_grammemes = {str(g) for g in best.tag.grammemes}
        is_transitive = "tran" in best_grammemes
        
        # 检查原词是否本身就是反身动词（以 -ся 结尾，标签为 intr）
        is_reflexive_verb = "intr" in best_grammemes and (best.normal_form.endswith("ся") or best.normal_form.endswith("сь"))
        
        # 检查动词的体（aspect）：完成体（perf）或未完成体（impf）
        verb_aspect = None
        if "perf" in best_grammemes:
            verb_aspect = "perf"
        elif "impf" in best_grammemes:
            verb_aspect = "impf"
        
        # 对于及物动词，尝试获取被动语态形式（带 -ся）
        passive_lexeme = None
        if is_transitive:
            # 尝试解析被动语态不定式（原词 + ся）
            # 注意：如果原词已经是反身动词（以 -ся/-сь 结尾），不要重复添加
            try:
                if not best.normal_form.endswith(("ся", "сь")):
                    passive_infinitive = best.normal_form + "ся"
                    passive_parses = self.analyzer.parse(passive_infinitive)
                    if passive_parses:
                        passive_best = next((p for p in passive_parses if p.tag.POS in ["INFN", "VERB"]), passive_parses[0])
                        passive_lexeme = passive_best.lexeme
            except Exception:
                pass

        cells: List[Dict[str, Optional[str]]] = []
        
        # 1. 现在时/将来时变位（主动语态）
        persons = ["1per", "2per", "3per"]
        numbers = ["sing", "plur"]
        
        for person in persons:
            for number in numbers:
                # 现在时
                grammemes = ["pres", person, number]
                form = None
                try:
                    form = self._ru_verb_present_indicative_from_lexeme_infr(best, person, number)
                    if form is None:
                        inflected = best.inflect(set(grammemes))
                        if inflected is not None:
                            form = inflected.word
                except Exception:
                    pass
                
                # 如果原词本身就是反身动词（以 -ся 结尾），变位应该标记为反身动词
                voice_type = "rfle" if is_reflexive_verb else "actv"
                
                cells.append({
                    "type": "conjugation",
                    "tense": "pres",
                    "person": person,
                    "number": number,
                    "voice": voice_type,
                    "form": form,
                })

                # 将来时（仅完成体动词有将来时）
                grammemes = ["futr", person, number]
                form = None
                try:
                    inflected = best.inflect(set(grammemes))
                    if inflected is not None:
                        form = inflected.word
                except Exception:
                    pass
                
                if form:  # 只有能生成将来时才添加
                    # 如果原词本身就是反身动词（以 -ся 结尾），变位应该标记为反身动词
                    voice_type = "rfle" if is_reflexive_verb else "actv"
                    
                    cells.append({
                        "type": "conjugation",
                        "tense": "futr",
                        "person": person,
                        "number": number,
                        "voice": voice_type,
                        "form": form,
                    })
                
                # 反身动词现在时（带 -ся 的形式）
                # 对于及物动词，带 -ся 的形式通常是反身动词（reflexive），不是被动语态
                # 被动语态在俄语中主要通过被动形动词构成，而不是动词变位形式
                if passive_lexeme:
                    try:
                        for form_parse in passive_lexeme:
                            form_word = form_parse.word
                            form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                            # 检查是否是现在时变位
                            form_person = next((p for p in ["1per", "2per", "3per"] if p in form_grammemes), None)
                            form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                            if ("VERB" in form_grammemes and "pres" in form_grammemes and 
                                "impr" not in form_grammemes and
                                form_person == person and 
                                form_number == number):
                                # 检查是否是反身动词（intr）还是真正的被动语态（pssv）
                                # 大多数带 -ся 的形式是反身动词（intr），不是被动语态
                                voice_type = "rfle"  # 默认是反身动词
                                if "pssv" in form_grammemes:
                                    voice_type = "pssv"  # 真正的被动语态（很少见）
                                
                                cells.append({
                                    "type": "conjugation",
                                    "tense": "pres",
                                    "person": person,
                                    "number": number,
                                    "voice": voice_type,
                                    "form": form_word,
                                })
                                break
                    except Exception:
                        pass
                
                # 反身动词将来时（带 -ся 的形式，很少见，通常未完成体动词没有将来时）
                # 注意：大多数带 -ся 的形式是反身动词，不是被动语态
                if passive_lexeme:
                    try:
                        for form_parse in passive_lexeme:
                            form_word = form_parse.word
                            form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                            # 检查是否是将来时变位
                            form_person = next((p for p in ["1per", "2per", "3per"] if p in form_grammemes), None)
                            form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                            if ("VERB" in form_grammemes and "futr" in form_grammemes and 
                                "impr" not in form_grammemes and
                                form_person == person and 
                                form_number == number):
                                # 检查是否是反身动词（intr）还是真正的被动语态（pssv）
                                voice_type = "rfle"  # 默认是反身动词
                                if "pssv" in form_grammemes:
                                    voice_type = "pssv"  # 真正的被动语态（很少见）
                                
                                cells.append({
                                    "type": "conjugation",
                                    "tense": "futr",
                                    "person": person,
                                    "number": number,
                                    "voice": voice_type,
                                    "form": form_word,
                                })
                                break
                    except Exception:
                        pass

        # 2. 过去时变位（只有性和数）- 主动语态
        genders = ["masc", "femn", "neut"]
        for gender in genders:
            grammemes = ["past", gender, "sing"]
            form = None
            try:
                inflected = best.inflect(set(grammemes))
                if inflected is not None:
                    form = inflected.word
            except Exception:
                pass
            
            # 如果原词本身就是反身动词（以 -ся 结尾），变位应该标记为反身动词
            voice_type = "rfle" if is_reflexive_verb else "actv"
            
            cells.append({
                "type": "conjugation",
                "tense": "past",
                "person": None,
                "number": "sing",
                "gender": gender,
                "voice": voice_type,
                "form": form,
            })

            # 反身动词过去时（带 -ся 的形式）
            if passive_lexeme:
                try:
                    for form_parse in passive_lexeme:
                        form_word = form_parse.word
                        form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                        # 检查是否是过去时变位
                        form_gender = next((g for g in ["masc", "femn", "neut"] if g in form_grammemes), None)
                        form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                        if ("VERB" in form_grammemes and "past" in form_grammemes and 
                            form_gender == gender and 
                            form_number == "sing"):
                            # 检查是否是反身动词（intr）还是真正的被动语态（pssv）
                            voice_type = "rfle"  # 默认是反身动词
                            if "pssv" in form_grammemes:
                                voice_type = "pssv"  # 真正的被动语态（很少见）
                            
                            cells.append({
                                "type": "conjugation",
                                "tense": "past",
                                "person": None,
                                "number": "sing",
                                "gender": gender,
                                "voice": voice_type,
                                "form": form_word,
                            })
                            break
                except Exception:
                    pass

        # 过去时复数 - 主动语态
        grammemes = ["past", "plur"]
        form = None
        try:
            inflected = best.inflect(set(grammemes))
            if inflected is not None:
                form = inflected.word
        except Exception:
            pass
        
        # 如果原词本身就是反身动词（以 -ся 结尾），变位应该标记为反身动词
        voice_type = "rfle" if is_reflexive_verb else "actv"
        
        cells.append({
            "type": "conjugation",
            "tense": "past",
            "person": None,
            "number": "plur",
            "gender": None,
            "voice": voice_type,
            "form": form,
        })
        
        # 反身动词过去时复数（带 -ся 的形式）
        if passive_lexeme:
            try:
                for form_parse in passive_lexeme:
                    form_word = form_parse.word
                    form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                    # 检查是否是过去时复数变位
                    form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                    if ("VERB" in form_grammemes and "past" in form_grammemes and 
                        form_number == "plur"):
                        # 检查是否是反身动词（intr）还是真正的被动语态（pssv）
                        voice_type = "rfle"  # 默认是反身动词
                        if "pssv" in form_grammemes:
                            voice_type = "pssv"  # 真正的被动语态（很少见）
                        
                        cells.append({
                            "type": "conjugation",
                            "tense": "past",
                            "person": None,
                            "number": "plur",
                            "gender": None,
                            "voice": voice_type,
                            "form": form_word,
                        })
                        break
            except Exception:
                pass

        # 3. 副动词（деепричастие）- 通过 lexeme 获取
        # 标准形式（无 V-sh 标记）优先，非标准形式（V-sh 标记）作为变体
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是副动词
                if "GRND" in grammemes_set or "Ger" in str(form_parse.tag):
                    aspect = None
                    if "perf" in grammemes_set:
                        aspect = "perf"
                    elif "impf" in grammemes_set:
                        aspect = "impf"
                    
                    # 检查是否是非标准形式（V-sh 标记，如 продавши）
                    is_variant = "V-sh" in grammemes_set or "V-sh" in str(form_parse.tag)
                    
                    if aspect:
                        cells.append({
                            "type": "gerund",
                            "aspect": aspect,
                            "form": form_parse.word,
                            "variant": is_variant,  # True 表示非标准变体（如 продавши）
                        })
        except Exception:
            # 如果 lexeme 不可用，尝试直接生成
            for aspect in ["impf", "perf"]:
                try:
                    # 尝试使用不同的语法标签组合
                    grammemes = set(["impr"]) if aspect == "impf" else set(["perf"])
                    inflected = best.inflect(grammemes)
                    if inflected is not None:
                        grammemes_set = {str(g) for g in inflected.tag.grammemes}
                        if "GRND" in grammemes_set or "Ger" in str(inflected.tag):
                            cells.append({
                                "type": "gerund",
                                "aspect": aspect,
                                "form": inflected.word,
                            })
                except Exception:
                    pass

        # 4. 命令式（повелительное наклонение）- 只获取排除式（excl），不包含包含式（incl）
        # 包含式（如 продадим）不是真正的命令式，而是第一人称复数将来时
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是命令式（主动语态），且是排除式（excl），不是包含式（incl）
                if ("VERB" in form_grammemes and "impr" in form_grammemes and 
                    "pssv" not in form_grammemes and "incl" not in form_grammemes):
                    form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                    if form_number:
                        # 检查是否已存在该形式
                        existing = next((c for c in cells if 
                                        c.get("type") == "imperative" and 
                                        c.get("number") == form_number and 
                                        c.get("form") == form_parse.word and
                                        (c.get("voice") != "pssv" or not c.get("voice"))), None)
                        if not existing:
                            cells.append({
                                "type": "imperative",
                                "number": form_number,
                                "form": form_parse.word,
                            })
        except Exception:
            # 如果 lexeme 不可用，回退到 inflect 方法
            for number in numbers:
                grammemes = {"impr", number}
                form = None
                try:
                    inflected = best.inflect(grammemes)
                    if inflected is not None:
                        form = inflected.word
                except Exception:
                    pass
                
                if form:
                    cells.append({
                        "type": "imperative",
                        "number": number,
                        "form": form,
                    })
        
        # 4b. 反身动词命令式（повелительное наклонение, возвратный глагол）- 带 -ся 的形式
        # 只获取排除式（excl），不包含包含式（incl）
        # 注意：大多数带 -ся 的命令式是反身动词，不是被动语态
        if passive_lexeme:
            try:
                for form_parse in passive_lexeme:
                    form_word = form_parse.word
                    form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                    # 检查是否是命令式，且是排除式（excl），不是包含式（incl）
                    form_number = next((n for n in ["sing", "plur"] if n in form_grammemes), None)
                    if ("VERB" in form_grammemes and "impr" in form_grammemes and 
                        form_number and "incl" not in form_grammemes):
                        # 检查是否是反身动词（intr）还是真正的被动语态（pssv）
                        voice_type = "rfle"  # 默认是反身动词
                        if "pssv" in form_grammemes:
                            voice_type = "pssv"  # 真正的被动语态（很少见）
                        
                        cells.append({
                            "type": "imperative",
                            "number": form_number,
                            "voice": voice_type,
                            "form": form_word,
                        })
            except Exception:
                pass

        # 5. 现在时形动词（причастие настоящего времени）- 通过 lexeme 获取
        cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
        genders = ["masc", "femn", "neut"]
        numbers = ["sing", "plur"]
        
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是现在时主动形动词
                if ("PRTF" in grammemes_set or "Part" in str(form_parse.tag)) and "pres" in grammemes_set and "actv" in grammemes_set:
                    if (self.language == "ru" and best.normal_form.lower() in RU_VERB_LEMMA_LEXEME_PREFER_INFR
                            and "Infr" not in grammemes_set):
                        continue
                    case = next((c for c in cases if c in grammemes_set), None)
                    number = next((n for n in numbers if n in grammemes_set), None)
                    gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                    animacy = "anim" if "anim" in grammemes_set else ("inan" if "inan" in grammemes_set else None)
                    
                    if case and number:
                        cells.append({
                            "type": "participle",
                            "tense": "pres",
                            "voice": "actv",
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "animacy": animacy,
                            "form": form_parse.word,
                        })
        except Exception:
            # 如果 lexeme 不可用，尝试直接生成
            for case in cases:
                for number in numbers:
                    if number == "sing":
                        for gender in genders:
                            try:
                                grammemes = {case, number, gender, "pres", "actv"}
                                inflected = best.inflect(grammemes)
                                if inflected is not None:
                                    grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                    if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                        animacy = None
                                        if case == "accs":
                                            try:
                                                anim_grammemes = grammemes | {"anim"}
                                                anim_inflected = best.inflect(anim_grammemes)
                                                if anim_inflected and anim_inflected.word != inflected.word:
                                                    cells.append({
                                                        "type": "participle",
                                                        "tense": "pres",
                                                        "voice": "actv",
                                                        "case": case,
                                                        "number": number,
                                                        "gender": gender,
                                                        "animacy": "anim",
                                                        "form": anim_inflected.word,
                                                    })
                                                    animacy = "inan"
                                            except Exception:
                                                pass
                                        
                                        cells.append({
                                            "type": "participle",
                                            "tense": "pres",
                                            "voice": "actv",
                                            "case": case,
                                            "number": number,
                                            "gender": gender,
                                            "animacy": animacy,
                                            "form": inflected.word,
                                        })
                            except Exception:
                                pass
                    else:
                        try:
                            grammemes = {case, number, "pres", "actv"}
                            inflected = best.inflect(grammemes)
                            if inflected is not None:
                                grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                    animacy = None
                                    if case == "accs":
                                        try:
                                            anim_grammemes = grammemes | {"anim"}
                                            anim_inflected = best.inflect(anim_grammemes)
                                            if anim_inflected and anim_inflected.word != inflected.word:
                                                cells.append({
                                                    "type": "participle",
                                                    "tense": "pres",
                                                    "voice": "actv",
                                                    "case": case,
                                                    "number": number,
                                                    "animacy": "anim",
                                                    "form": anim_inflected.word,
                                                })
                                                animacy = "inan"
                                        except Exception:
                                            pass
                                    
                                    cells.append({
                                        "type": "participle",
                                        "tense": "pres",
                                        "voice": "actv",
                                        "case": case,
                                        "number": number,
                                        "animacy": animacy,
                                        "form": inflected.word,
                                    })
                        except Exception:
                            pass
        
        # 5b. 现在时被动形动词（причастие настоящего времени, страдательный залог）- 通过 lexeme 获取
        # 首先从被动语态 lexeme 中查找（带 -ся 的形式）
        if passive_lexeme:
            try:
                for form_parse in passive_lexeme:
                    grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                    form_word = form_parse.word
                    # 检查是否是现在时被动形动词（带 -ся 的形式）
                    if (("PRTF" in grammemes_set or "Part" in str(form_parse.tag)) and 
                        "pres" in grammemes_set):
                        case = next((c for c in cases if c in grammemes_set), None)
                        number = next((n for n in numbers if n in grammemes_set), None)
                        gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                        animacy = "anim" if "anim" in grammemes_set else ("inan" if "inan" in grammemes_set else None)
                        
                        if case and number:
                            cells.append({
                                "type": "participle",
                                "tense": "pres",
                                "voice": "pssv",
                                "case": case,
                                "number": number,
                                "gender": gender,
                                "animacy": animacy,
                                "form": form_word,
                            })
            except Exception:
                pass
        
        # 也从原 lexeme 中查找（带 pssv 标签的，不带 -ся）
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是现在时被动形动词（pssv 标签，不带 -ся）
                if ("PRTF" in grammemes_set or "Part" in str(form_parse.tag)) and "pres" in grammemes_set and "pssv" in grammemes_set:
                    case = next((c for c in cases if c in grammemes_set), None)
                    number = next((n for n in numbers if n in grammemes_set), None)
                    gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                    animacy = "anim" if "anim" in grammemes_set else ("inan" if "inan" in grammemes_set else None)
                    
                    if case and number:
                        cells.append({
                            "type": "participle",
                            "tense": "pres",
                            "voice": "pssv",
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "animacy": animacy,
                            "form": form_parse.word,
                        })
        except Exception:
            # 如果 lexeme 不可用，尝试直接生成
            for case in cases:
                for number in numbers:
                    if number == "sing":
                        for gender in genders:
                            try:
                                grammemes = {case, number, gender, "pres", "pssv"}
                                inflected = best.inflect(grammemes)
                                if inflected is not None:
                                    grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                    if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                        animacy = None
                                        if case == "accs":
                                            try:
                                                anim_grammemes = grammemes | {"anim"}
                                                anim_inflected = best.inflect(anim_grammemes)
                                                if anim_inflected and anim_inflected.word != inflected.word:
                                                    cells.append({
                                                        "type": "participle",
                                                        "tense": "pres",
                                                        "voice": "pssv",
                                                        "case": case,
                                                        "number": number,
                                                        "gender": gender,
                                                        "animacy": "anim",
                                                        "form": anim_inflected.word,
                                                    })
                                                    animacy = "inan"
                                            except Exception:
                                                pass
                                        
                                        cells.append({
                                            "type": "participle",
                                            "tense": "pres",
                                            "voice": "pssv",
                                            "case": case,
                                            "number": number,
                                            "gender": gender,
                                            "animacy": animacy,
                                            "form": inflected.word,
                                        })
                            except Exception:
                                pass
                    else:
                        try:
                            grammemes = {case, number, "pres", "pssv"}
                            inflected = best.inflect(grammemes)
                            if inflected is not None:
                                grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                    animacy = None
                                    if case == "accs":
                                        try:
                                            anim_grammemes = grammemes | {"anim"}
                                            anim_inflected = best.inflect(anim_grammemes)
                                            if anim_inflected and anim_inflected.word != inflected.word:
                                                cells.append({
                                                    "type": "participle",
                                                    "tense": "pres",
                                                    "voice": "pssv",
                                                    "case": case,
                                                    "number": number,
                                                    "animacy": "anim",
                                                    "form": anim_inflected.word,
                                                })
                                                animacy = "inan"
                                        except Exception:
                                            pass
                                    
                                    cells.append({
                                        "type": "participle",
                                        "tense": "pres",
                                        "voice": "pssv",
                                        "case": case,
                                        "number": number,
                                        "animacy": animacy,
                                        "form": inflected.word,
                                    })
                        except Exception:
                            pass

        # 6. 过去时形动词（причастие прошедшего времени）- 通过 lexeme 获取
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是过去时主动形动词
                if ("PRTF" in grammemes_set or "Part" in str(form_parse.tag)) and "past" in grammemes_set and "actv" in grammemes_set:
                    case = next((c for c in cases if c in grammemes_set), None)
                    number = next((n for n in numbers if n in grammemes_set), None)
                    gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                    animacy = "anim" if "anim" in grammemes_set else ("inan" if "inan" in grammemes_set else None)
                    
                    if case and number:
                        cells.append({
                            "type": "participle",
                            "tense": "past",
                            "voice": "actv",
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "animacy": animacy,
                            "form": form_parse.word,
                        })
        except Exception:
            # 如果 lexeme 不可用，尝试直接生成
            for case in cases:
                for number in numbers:
                    if number == "sing":
                        for gender in genders:
                            try:
                                grammemes = {case, number, gender, "past", "actv"}
                                inflected = best.inflect(grammemes)
                                if inflected is not None:
                                    grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                    if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                        animacy = None
                                        if case == "accs":
                                            try:
                                                anim_grammemes = grammemes | {"anim"}
                                                anim_inflected = best.inflect(anim_grammemes)
                                                if anim_inflected and anim_inflected.word != inflected.word:
                                                    cells.append({
                                                        "type": "participle",
                                                        "tense": "past",
                                                        "voice": "actv",
                                                        "case": case,
                                                        "number": number,
                                                        "gender": gender,
                                                        "animacy": "anim",
                                                        "form": anim_inflected.word,
                                                    })
                                                    animacy = "inan"
                                            except Exception:
                                                pass
                                        
                                        cells.append({
                                            "type": "participle",
                                            "tense": "past",
                                            "voice": "actv",
                                            "case": case,
                                            "number": number,
                                            "gender": gender,
                                            "animacy": animacy,
                                            "form": inflected.word,
                                        })
                            except Exception:
                                pass
                    else:
                        try:
                            grammemes = {case, number, "past", "actv"}
                            inflected = best.inflect(grammemes)
                            if inflected is not None:
                                grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                    animacy = None
                                    if case == "accs":
                                        try:
                                            anim_grammemes = grammemes | {"anim"}
                                            anim_inflected = best.inflect(anim_grammemes)
                                            if anim_inflected and anim_inflected.word != inflected.word:
                                                cells.append({
                                                    "type": "participle",
                                                    "tense": "past",
                                                    "voice": "actv",
                                                    "case": case,
                                                    "number": number,
                                                    "animacy": "anim",
                                                    "form": anim_inflected.word,
                                                })
                                                animacy = "inan"
                                        except Exception:
                                            pass
                                    
                                    cells.append({
                                        "type": "participle",
                                        "tense": "past",
                                        "voice": "actv",
                                        "case": case,
                                        "number": number,
                                        "animacy": animacy,
                                        "form": inflected.word,
                                    })
                        except Exception:
                            pass
        
        # 6b. 过去时被动形动词（причастие прошедшего времени, страдательный залог）- 通过 lexeme 获取
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是过去时被动形动词（pssv 标签）
                if ("PRTF" in grammemes_set or "Part" in str(form_parse.tag)) and "past" in grammemes_set and "pssv" in grammemes_set:
                    case = next((c for c in cases if c in grammemes_set), None)
                    number = next((n for n in numbers if n in grammemes_set), None)
                    gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                    animacy = "anim" if "anim" in grammemes_set else ("inan" if "inan" in grammemes_set else None)
                    
                    if case and number:
                        cells.append({
                            "type": "participle",
                            "tense": "past",
                            "voice": "pssv",
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "animacy": animacy,
                            "form": form_parse.word,
                        })
        except Exception:
            # 如果 lexeme 不可用，尝试直接生成
            for case in cases:
                for number in numbers:
                    if number == "sing":
                        for gender in genders:
                            try:
                                grammemes = {case, number, gender, "past", "pssv"}
                                inflected = best.inflect(grammemes)
                                if inflected is not None:
                                    grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                    if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                        animacy = None
                                        if case == "accs":
                                            try:
                                                anim_grammemes = grammemes | {"anim"}
                                                anim_inflected = best.inflect(anim_grammemes)
                                                if anim_inflected and anim_inflected.word != inflected.word:
                                                    cells.append({
                                                        "type": "participle",
                                                        "tense": "past",
                                                        "voice": "pssv",
                                                        "case": case,
                                                        "number": number,
                                                        "gender": gender,
                                                        "animacy": "anim",
                                                        "form": anim_inflected.word,
                                                    })
                                                    animacy = "inan"
                                            except Exception:
                                                pass
                                        
                                        cells.append({
                                            "type": "participle",
                                            "tense": "past",
                                            "voice": "pssv",
                                            "case": case,
                                            "number": number,
                                            "gender": gender,
                                            "animacy": animacy,
                                            "form": inflected.word,
                                        })
                            except Exception:
                                pass
                    else:
                        try:
                            grammemes = {case, number, "past", "pssv"}
                            inflected = best.inflect(grammemes)
                            if inflected is not None:
                                grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                    animacy = None
                                    if case == "accs":
                                        try:
                                            anim_grammemes = grammemes | {"anim"}
                                            anim_inflected = best.inflect(anim_grammemes)
                                            if anim_inflected and anim_inflected.word != inflected.word:
                                                cells.append({
                                                    "type": "participle",
                                                    "tense": "past",
                                                    "voice": "pssv",
                                                    "case": case,
                                                    "number": number,
                                                    "animacy": "anim",
                                                    "form": anim_inflected.word,
                                                })
                                                animacy = "inan"
                                        except Exception:
                                            pass
                                    
                                    cells.append({
                                        "type": "participle",
                                        "tense": "past",
                                        "voice": "pssv",
                                        "case": case,
                                        "number": number,
                                        "animacy": animacy,
                                        "form": inflected.word,
                                    })
                        except Exception:
                            pass
        
        # 6c. 被动形动词短尾形式（краткая форма страдательного причастия）
        try:
            lexeme = best.lexeme
            for form_parse in lexeme:
                grammemes_set = {str(g) for g in form_parse.tag.grammemes}
                # 检查是否是短尾被动形动词（PRTS 或 shrt 标签）
                if (("PRTS" in grammemes_set or "shrt" in grammemes_set) and "pssv" in grammemes_set):
                    number = next((n for n in numbers if n in grammemes_set), None)
                    gender = next((g for g in genders if g in grammemes_set), None) if number == "sing" else None
                    
                    if number:
                        cells.append({
                            "type": "participle",
                            "tense": "past",
                            "voice": "pssv",
                            "case": "nomn",
                            "number": number,
                            "gender": gender,
                            "short": True,
                            "form": form_parse.word,
                        })
        except Exception:
            # 尝试直接生成短尾形式
            for number in numbers:
                if number == "sing":
                    for gender in genders:
                        try:
                            grammemes = {"nomn", number, gender, "past", "pssv", "shrt"}
                            inflected = best.inflect(grammemes)
                            if inflected is not None:
                                grammemes_set = {str(g) for g in inflected.tag.grammemes}
                                if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                    cells.append({
                                        "type": "participle",
                                        "tense": "past",
                                        "voice": "pssv",
                                        "case": "nomn",
                                        "number": number,
                                        "gender": gender,
                                        "short": True,
                                        "form": inflected.word,
                                    })
                        except Exception:
                            pass
                else:
                    try:
                        grammemes = {"nomn", number, "past", "pssv", "shrt"}
                        inflected = best.inflect(grammemes)
                        if inflected is not None:
                            grammemes_set = {str(g) for g in inflected.tag.grammemes}
                            if "PRTF" in grammemes_set or "Part" in str(inflected.tag):
                                cells.append({
                                    "type": "participle",
                                    "tense": "past",
                                    "voice": "pssv",
                                    "case": "nomn",
                                    "number": number,
                                    "short": True,
                                    "form": inflected.word,
                                })
                    except Exception:
                        pass

        return {
            "input": word,
            "language": self.language,
            "normal_form": best.normal_form,
            "pos": pos,
            "aspect": verb_aspect,  # 添加动词的体信息（perf 或 impf）
            "cells": cells,
        }

    def get_comprehensive_changes(self, word: str) -> Dict[str, Any]:
        """获取单词的全面词形变化（名词变格+形容词变格+动词变位）。
        
        对于既是名词又是动词的词（如 мочь），会同时生成名词变格和动词变位。
        对于形动词和副动词，会返回其原形的动词变位数据。
        """
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "normal_form": word,
                "pos": "UNKNOWN",
                "noun_declension": {
                    "input": word,
                    "language": self.language,
                    "normal_form": word,
                    "pos": "UNKNOWN",
                    "cells": []
                },
                "adjective_declension": {
                    "input": word,
                    "language": self.language,
                    "normal_form": word,
                    "pos": "UNKNOWN",
                    "cells": []
                },
                "verb_conjugation": {
                    "input": word,
                    "language": self.language,
                    "normal_form": word,
                    "pos": "UNKNOWN",
                    "cells": []
                },
            }

        # 检查是否有多种词性
        pos_set = set()
        for parse in parses:
            pos = str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag)
            pos_set.add(pos)
        
        # 选择最佳解析作为主要词性
        best = self._select_best_parse(word, parses)
        pos = str(best.tag.POS) if hasattr(best.tag, "POS") and best.tag.POS else str(best.tag)
        
        # 如果输入是形动词（PRTF）或副动词（GRND），检查其原形是否是动词
        # 如果是，则将原形添加到 pos_set 中，以便生成动词变位
        # 注意：需要检查所有解析，因为主要词性可能不是 PRTF/GRND（如 читаемый 的主要词性是 ADJF）
        if pos in ["PRTF", "GRND", "PRTS"]:
            normal_form = best.normal_form
            if normal_form != word:
                # 检查原形是否是动词
                normal_parses = self.analyzer.parse(normal_form)
                for np in normal_parses:
                    np_pos = str(np.tag.POS) if hasattr(np.tag, "POS") and np.tag.POS else str(np.tag)
                    if np_pos in ["VERB", "INFN"]:
                        pos_set.add("VERB")
                        pos_set.add("INFN")
                        break
        
        # 即使主要词性不是 PRTF/GRND，也要检查是否有 PRTF/GRND 解析
        # 如果有，检查它们的原形是否是动词（如 читаемый 的主要词性是 ADJF，但有 PRTF 解析）
        for parse in parses:
            parse_pos = str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag)
            if parse_pos in ["PRTF", "GRND", "PRTS"]:
                normal_form = parse.normal_form
                if normal_form != word:
                    # 检查原形是否是动词
                    normal_parses = self.analyzer.parse(normal_form)
                    for np in normal_parses:
                        np_pos = str(np.tag.POS) if hasattr(np.tag, "POS") and np.tag.POS else str(np.tag)
                        if np_pos in ["VERB", "INFN"]:
                            pos_set.add("VERB")
                            pos_set.add("INFN")
                            break
        
        # 注意：不再自动从动名词推断动词
        # 动名词（如 расплавление）和动词（如 расплавить）是不同的词条
        # 派生关系 ≠ 形态关系，不应该自动生成不存在的动词形式
        # 如果用户需要动词变位，应该直接输入动词（如 расплавить）
        
        # 如果输入是形容词比较级（COMP），不应该生成原级的完整变格表
        # 比较级本身只有一种形式，不需要变格
        # 但我们可以返回比较级形式本身
        is_comparative_input = (pos == "COMP")

        result = {
            "input": word,
            "language": self.language,
            "normal_form": best.normal_form,
            "pos": pos,
            "noun_declension": {
                "input": word,
                "language": self.language,
                "normal_form": best.normal_form,
                "pos": pos,
                "cells": []
            },
            "adjective_declension": {
                "input": word,
                "language": self.language,
                "normal_form": best.normal_form,
                "pos": pos,
                "cells": []
            },
            "verb_conjugation": {
                "input": word,
                "language": self.language,
                "normal_form": best.normal_form,
                "pos": pos,
                "cells": []
            },
        }

        # 如果存在名词解析，生成名词变格
        if "NOUN" in pos_set or "NPRO" in pos_set:
            noun_parse = next((p for p in parses if (hasattr(p.tag, "POS") and p.tag.POS in ["NOUN", "NPRO"]) or "NOUN" in str(p.tag) or "NPRO" in str(p.tag)), None)
            if noun_parse:
                try:
                    noun_result = self.build_declension(word, preferred_parse=noun_parse)
                    if noun_result and noun_result.get("cells") and len(noun_result.get("cells", [])) > 0:
                        result["noun_declension"] = noun_result
                except Exception:
                    pass
        
        # 如果存在形容词解析，生成形容词变格
        # 但如果输入本身就是比较级（COMP），不应该生成原级的完整变格表
        if ("ADJF" in pos_set or "ADJS" in pos_set) and not is_comparative_input:
            adj_parse = next((p for p in parses if (hasattr(p.tag, "POS") and p.tag.POS in ["ADJF", "ADJS"]) or "ADJF" in str(p.tag) or "ADJS" in str(p.tag)), None)
            if adj_parse:
                try:
                    adj_result = self.build_adjective_declension(word, preferred_parse=adj_parse)
                    if adj_result and adj_result.get("cells") and len(adj_result.get("cells", [])) > 0:
                        result["adjective_declension"] = adj_result
                except Exception:
                    pass
        
        # 如果输入是比较级，只返回比较级形式本身（不返回原级的完整变格表）
        if is_comparative_input:
            try:
                # 从 lexeme 中提取所有比较级形式
                lexeme = best.lexeme
                comp_cells = []
                for form_parse in lexeme:
                    form_grammemes = {str(g) for g in form_parse.tag.grammemes}
                    if "COMP" in form_grammemes or "Cmp2" in form_grammemes:
                        existing = next((c for c in comp_cells if c.get("form") == form_parse.word), None)
                        if not existing:
                            comp_cells.append({
                                "case": None,
                                "number": None,
                                "gender": None,
                                "form": form_parse.word,
                                "short": None,
                                "comparative": True,
                            })
                
                if comp_cells:
                    result["adjective_declension"] = {
                        "input": word,
                        "language": self.language,
                        "normal_form": best.normal_form,
                        "pos": pos,
                        "cells": comp_cells,
                    }
            except Exception:
                pass
        
        # 如果存在动词解析，生成动词变位
        if "VERB" in pos_set or "INFN" in pos_set:
            verb_parse = next((p for p in parses if (hasattr(p.tag, "POS") and p.tag.POS in ["VERB", "INFN"]) or "VERB" in str(p.tag) or "INFN" in str(p.tag)), None)
            
            # 如果没有找到动词解析，但 pos_set 中有 VERB/INFN，可能是从 PRTF/GRND 的原形添加的，或者是从动名词找到的
            # 需要从原形查找动词解析
            verb_word = word
            if not verb_parse:
                # 首先检查是否是 PRTF/GRND 的原形
                for parse in parses:
                    parse_pos = str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag)
                    if parse_pos in ["PRTF", "GRND", "PRTS"]:
                        normal_form = parse.normal_form
                        if normal_form != word:
                            normal_parses = self.analyzer.parse(normal_form)
                            verb_parse = next((p for p in normal_parses if (hasattr(p.tag, "POS") and p.tag.POS in ["VERB", "INFN"]) or "VERB" in str(p.tag) or "INFN" in str(p.tag)), None)
                            if verb_parse:
                                verb_word = normal_form  # 使用原形生成动词变位
                                break
                
                # 注意：不再从动名词自动推断动词
                # 动名词和动词是不同的词条，不应该自动生成
                # 如果用户需要动词变位，应该直接输入动词
            
            if verb_parse:
                try:
                    verb_result = self.build_verb_conjugation(verb_word, preferred_parse=verb_parse)
                    if verb_result and verb_result.get("cells") and len(verb_result.get("cells", [])) > 0:
                        result["verb_conjugation"] = verb_result
                except Exception as e:
                    # 如果生成失败，继续尝试其他方法
                    pass
        
        # 如果主要词性是名词/形容词/动词，但还没有生成对应的变化，则生成
        if pos in ["NOUN", "NPRO"] and len(result["noun_declension"]["cells"]) == 0:
            try:
                noun_result = self.build_declension(word)
                if noun_result and noun_result.get("cells") and len(noun_result.get("cells", [])) > 0:
                    result["noun_declension"] = noun_result
            except Exception:
                pass
        elif pos in ["ADJF", "ADJS"] and len(result["adjective_declension"]["cells"]) == 0 and not is_comparative_input:
            try:
                adj_result = self.build_adjective_declension(word)
                if adj_result and adj_result.get("cells") and len(adj_result.get("cells", [])) > 0:
                    result["adjective_declension"] = adj_result
            except Exception:
                pass
        elif pos in ["VERB", "INFN"] and len(result["verb_conjugation"]["cells"]) == 0:
            try:
                verb_result = self.build_verb_conjugation(word)
                if verb_result and verb_result.get("cells") and len(verb_result.get("cells", [])) > 0:
                    result["verb_conjugation"] = verb_result
            except Exception:
                pass
        elif pos == "NUMR" and len(result["noun_declension"]["cells"]) == 0:
            # 数词变格：将数词变格数据放在 noun_declension 中
            try:
                numeral_result = self.analyze_numeral(word)
                numeral_forms = numeral_result.get("numeral_forms", [])
                if numeral_forms:
                    # 取第一个数词形式（通常只有一个）
                    first_numeral = numeral_forms[0]
                    case_forms = first_numeral.get("case_forms", [])
                    if case_forms:
                        # 将数词变格转换为名词变格格式
                        cells = []
                        for cf in case_forms:
                            cells.append({
                                "case": cf.get("case"),
                                "number": "sing",  # 数词通常用单数形式
                                "gender": None,  # 数词通常没有性别
                                "form": cf.get("form"),
                            })
                        if cells:
                            result["noun_declension"] = {
                                "input": word,
                                "language": self.language,
                                "normal_form": first_numeral.get("normal_form", word),
                                "pos": "NUMR",
                                "cells": cells,
                            }
            except Exception:
                pass
        else:
            # 如果主要词性不明确，尝试生成所有类型的变化（但只在确实存在对应词性时）
            # 检查是否真的存在名词解析
            if "NOUN" in pos_set or "NPRO" in pos_set:
                if len(result["noun_declension"]["cells"]) == 0:
                    try:
                        noun_result = self.build_declension(word)
                        if noun_result and noun_result.get("cells") and len(noun_result.get("cells", [])) > 0:
                            result["noun_declension"] = noun_result
                    except Exception:
                        pass
            # 检查是否真的存在形容词解析
            if "ADJF" in pos_set or "ADJS" in pos_set:
                if len(result["adjective_declension"]["cells"]) == 0:
                    try:
                        adj_result = self.build_adjective_declension(word)
                        if adj_result and adj_result.get("cells") and len(adj_result.get("cells", [])) > 0:
                            result["adjective_declension"] = adj_result
                    except Exception:
                        pass
            # 检查是否真的存在数词解析
            if "NUMR" in pos_set:
                if len(result["noun_declension"]["cells"]) == 0:
                    try:
                        numeral_result = self.analyze_numeral(word)
                        numeral_forms = numeral_result.get("numeral_forms", [])
                        if numeral_forms:
                            first_numeral = numeral_forms[0]
                            case_forms = first_numeral.get("case_forms", [])
                            if case_forms:
                                cells = []
                                for cf in case_forms:
                                    cells.append({
                                        "case": cf.get("case"),
                                        "number": "sing",
                                        "gender": None,
                                        "form": cf.get("form"),
                                    })
                                if cells:
                                    result["noun_declension"] = {
                                        "input": word,
                                        "language": self.language,
                                        "normal_form": first_numeral.get("normal_form", word),
                                        "pos": "NUMR",
                                        "cells": cells,
                                    }
                    except Exception:
                        pass
            # 检查是否真的存在动词解析
            if "VERB" in pos_set or "INFN" in pos_set:
                if len(result["verb_conjugation"]["cells"]) == 0:
                    try:
                        verb_result = self.build_verb_conjugation(word)
                        if verb_result and verb_result.get("cells") and len(verb_result.get("cells", [])) > 0:
                            result["verb_conjugation"] = verb_result
                    except Exception:
                        pass

        return result

    # ---- 词性标注和词干提取 ----
    def get_pos_tagging(self, word: str) -> Dict[str, Any]:
        """获取单词的词性标注信息。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "pos_tags": [],
                "is_known": False,
            }

        pos_tags = []
        for parse in parses:
            tag_info = {
                "word": parse.word,
                "normal_form": parse.normal_form,
                "pos": str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag),
                "tag": str(parse.tag),
                "score": float(parse.score),
                "is_known": parse.is_known,
                "grammemes": sorted([str(g) for g in parse.tag.grammemes]),
                "cyr_grammemes": sorted([str(g) for g in parse.tag.grammemes_cyr]),
            }
            
            # 从 grammemes 中提取常见的语法特征
            grammemes_set = set(str(g) for g in parse.tag.grammemes)
            
            # 提取格
            cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
            tag_info["case"] = next((c for c in cases if c in grammemes_set), None)
            
            # 提取性
            genders = ["masc", "femn", "neut", "Ms-f"]
            tag_info["gender"] = next((g for g in genders if g in grammemes_set), None)
            
            # 提取数
            numbers = ["sing", "plur"]
            tag_info["number"] = next((n for n in numbers if n in grammemes_set), None)
            
            # 提取人称
            persons = ["1per", "2per", "3per"]
            tag_info["person"] = next((p for p in persons if p in grammemes_set), None)
            
            # 提取时态
            tenses = ["pres", "past", "futr"]
            tag_info["tense"] = next((t for t in tenses if t in grammemes_set), None)
            
            # 提取体
            aspects = ["perf", "impf"]
            tag_info["aspect"] = next((a for a in aspects if a in grammemes_set), None)
            
            # 提取语态
            voices = ["actv", "pssv"]
            tag_info["voice"] = next((v for v in voices if v in grammemes_set), None)
            
            # 提取式
            moods = ["indc", "impr"]
            tag_info["mood"] = next((m for m in moods if m in grammemes_set), None)
            
            # 提取有生性
            animacies = ["anim", "inan"]
            tag_info["animacy"] = next((a for a in animacies if a in grammemes_set), None)
                
            pos_tags.append(tag_info)

        return {
            "input": word,
            "language": self.language,
            "pos_tags": pos_tags,
            "is_known": any(p.is_known for p in parses),
        }

    def get_stem_and_lexeme(self, word: str) -> Dict[str, Any]:
        """获取单词的词干和词族信息。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "stems": [],
                "lexemes": [],
            }

        stems = []
        lexemes = []
        
        for parse in parses:
            # 获取词干（通过 normal_form）
            stem_info = {
                "word": parse.word,
                "stem": parse.normal_form,
                "pos": str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag),
                "score": float(parse.score),
            }
            stems.append(stem_info)
            
            # 获取词族（lexeme）
            try:
                lexeme = parse.lexeme
                lexeme_forms = []
                for form in lexeme:
                    lexeme_forms.append({
                        "word": form.word,
                        "tag": str(form.tag),
                        "grammemes": sorted([str(g) for g in form.tag.grammemes]),
                    })
                
                lexeme_info = {
                    "word": parse.word,
                    "lexeme_forms": lexeme_forms,
                    "total_forms": len(lexeme_forms),
                }
                lexemes.append(lexeme_info)
            except Exception:
                # 某些词可能没有完整的词族信息
                pass

        return {
            "input": word,
            "language": self.language,
            "stems": stems,
            "lexemes": lexemes,
        }

    # ---- 拼写校正和相似词查找 ----
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算两个字符串之间的编辑距离（Levenshtein distance）"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _find_similar_words(self, word: str, max_distance: int = 2, max_suggestions: int = 10) -> List[Dict[str, Any]]:
        """查找与输入词相似的已知词（基于编辑距离和常见拼写错误模式）"""
        suggestions = []
        
        # 获取输入词的所有解析
        parses = self.analyzer.parse(word)
        
        # 获取所有可能的原形
        normal_forms = set()
        if parses:
            for parse in parses:
                normal_forms.add(parse.normal_form)
        
        # 生成可能的变体（基于常见拼写错误模式）
        variants = []
        word_len = len(word)
        
        # 1. 替换最后两个字母（常见错误：за -> нт, 等）
        if word_len >= 2:
            # 常见替换模式（基于实际观察到的错误）
            suffix_replacements = {
                'за': ['нт', 'з', 'за', 'та', 'на'],  # мутаза -> мутант
                'та': ['т', 'та', 'нт', 'за'],
                'на': ['н', 'на', 'нт'],
                'нт': ['за', 'та', 'нт'],
            }
            
            for suffix, replacements in suffix_replacements.items():
                if word.endswith(suffix):
                    for replacement in replacements:
                        variant = word[:-len(suffix)] + replacement
                        if variant != word:
                            variants.append(variant)
                    # 不 break，继续执行特殊处理
            
            # 特殊处理：对于以 'за' 结尾的词，确保尝试 'нт' 替换
            # мутаза -> мутант
            if word.endswith('за'):
                # 直接尝试：мутаза -> мутант（如果还没有在列表中）
                variant1 = word[:-2] + 'нт'  # мутаза -> мутант
                if variant1 != word and variant1 not in variants:
                    variants.append(variant1)
                
                # 通过中间步骤：мутаза -> мутаз -> мутант
                variant2 = word[:-1]  # мутаза -> мутаз
                if variant2 != word and variant2 not in variants:
                    variants.append(variant2)
                    # 然后从 мутаз 生成 мутант
                    variant3 = variant2[:-1] + 'нт'  # мутаз -> мутант
                    if variant3 != word and variant3 not in variants:
                        variants.append(variant3)
        
        # 2. 替换最后一个字母
        if word_len > 1:
            # 只尝试常见的替换（避免生成太多候选）
            common_replacements = {
                'а': ['т', 'н', 'з', 'д', 'я'],
                'з': ['т', 'н', 'з', 'с'],
                'т': ['т', 'д', 'з', 'н'],
                'н': ['н', 'м', 'т', 'з'],
            }
            last_char = word[-1]
            if last_char in common_replacements:
                for char in common_replacements[last_char]:
                    variant = word[:-1] + char
                    if variant != word:
                        variants.append(variant)
        
        # 3. 替换倒数第二个字母（对于 мутаза -> мутант 这种情况很重要）
        if word_len >= 2:
            second_last_char = word[-2]
            # 常见替换：з -> н, а -> т 等
            second_last_replacements = {
                'з': ['н', 'т', 'з', 'с'],
                'а': ['т', 'н', 'а', 'я'],
                'т': ['з', 'н', 'т', 'д'],
                'н': ['з', 'т', 'н', 'м'],
            }
            if second_last_char in second_last_replacements:
                for char in second_last_replacements[second_last_char]:
                    variant = word[:-2] + char + word[-1]
                    if variant != word:
                        variants.append(variant)
        
        # 4. 插入/删除字母（简化：只检查删除最后一个字母）
        if word_len > 3:
            variant = word[:-1]
            variants.append(variant)
        
        # 检查变体
        checked = set()
        for variant in variants:
            if variant in checked:
                continue
            
            candidate_parses = self.analyzer.parse(variant)
            if candidate_parses:
                for parse in candidate_parses:
                    normal_form = parse.normal_form
                    if normal_form not in normal_forms:  # 避免建议原词本身
                        # 使用 (variant, normal_form) 作为唯一标识，避免重复
                        key = (variant, normal_form)
                        if key not in checked:
                            checked.add(key)
                            # 同时将 variant 和 normal_form 添加到 checked（如果不同）
                            if variant != normal_form:
                                checked.add(variant)
                                checked.add(normal_form)
                            
                            distance = self._levenshtein_distance(word, normal_form)
                            if distance <= max_distance:
                                suggestions.append({
                                    "word": variant,
                                    "normal_form": normal_form,
                                    "tag": str(parse.tag),
                                    "score": float(parse.score),
                                    "distance": distance,
                                })
        
        # 按距离和置信度排序
        suggestions.sort(key=lambda x: (x.get("distance", 999), -x.get("score", 0)))
        
        return suggestions[:max_suggestions]
    
    def spell_check(self, word: str) -> Dict[str, Any]:
        """拼写校正和相似词查找。"""
        # 检查单词是否已知
        is_known = self.analyzer.word_is_known(word)
        
        suggestions = []
        
        # 获取输入词的解析，检查置信度
        parses = self.analyzer.parse(word)
        if parses:
            best = parses[0]
            confidence = float(best.score)
            
            # 如果置信度较低（< 50%），或者词不在词典中，提供相似词建议
            if not is_known or confidence < 0.5:
                # 首先尝试使用 pymorphy2 的词典查找相似词
                try:
                    known_parses = list(self.analyzer.iter_known_word_parses(word))
                    for parse in known_parses[:10]:  # 限制建议数量
                        suggestions.append({
                            "word": parse.word,
                            "normal_form": parse.normal_form,
                            "tag": str(parse.tag),
                            "score": float(parse.score),
                        })
                except Exception:
                    pass
                
                # 如果 pymorphy2 没有提供建议，使用编辑距离查找
                if not suggestions:
                    suggestions = self._find_similar_words(word, max_distance=2, max_suggestions=10)

        return {
            "input": word,
            "language": self.language,
            "is_known": is_known,
            "suggestions": suggestions,
        }

    def get_normal_forms(self, word: str) -> Dict[str, Any]:
        """获取单词的所有可能原形。"""
        try:
            normal_forms = self.analyzer.normal_forms(word)
            return {
                "input": word,
                "language": self.language,
                "normal_forms": list(normal_forms),
                "count": len(normal_forms),
            }
        except Exception as exc:
            return {
                "input": word,
                "language": self.language,
                "normal_forms": [],
                "count": 0,
                "error": str(exc),
            }

    # ---- 数词和副词形态分析 ----
    def analyze_numeral(self, word: str) -> Dict[str, Any]:
        """分析数词的形态变化。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "numeral_forms": [],
            }

        numeral_forms = []
        for parse in parses:
            if "NUMR" in str(parse.tag):  # 数词
                # 数词的特殊变格
                cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
                forms = []
                
                for case in cases:
                    try:
                        inflected = parse.inflect({case})
                        if inflected:
                            forms.append({
                                "case": case,
                                "form": inflected.word,
                                "tag": str(inflected.tag),
                            })
                    except Exception:
                        pass
                
                numeral_info = {
                    "word": parse.word,
                    "normal_form": parse.normal_form,
                    "tag": str(parse.tag),
                    "score": float(parse.score),
                    "case_forms": forms,
                }
                numeral_forms.append(numeral_info)

        return {
            "input": word,
            "language": self.language,
            "numeral_forms": numeral_forms,
        }

    def analyze_adverb(self, word: str) -> Dict[str, Any]:
        """分析副词的形态变化。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "adverb_forms": [],
            }

        adverb_forms = []
        for parse in parses:
            if "ADVB" in str(parse.tag):  # 副词
                # 副词通常没有变格，但可能有比较级
                forms = []
                
                # 尝试生成比较级
                try:
                    comparative = parse.inflect({"comp"})
                    if comparative:
                        forms.append({
                            "type": "comparative",
                            "form": comparative.word,
                            "tag": str(comparative.tag),
                        })
                except Exception:
                    pass
                
                # 尝试生成最高级
                try:
                    superlative = parse.inflect({"supr"})
                    if superlative:
                        forms.append({
                            "type": "superlative",
                            "form": superlative.word,
                            "tag": str(superlative.tag),
                        })
                except Exception:
                    pass
                
                adverb_info = {
                    "word": parse.word,
                    "normal_form": parse.normal_form,
                    "tag": str(parse.tag),
                    "score": float(parse.score),
                    "degree_forms": forms,
                }
                adverb_forms.append(adverb_info)

        return {
            "input": word,
            "language": self.language,
            "adverb_forms": adverb_forms,
        }

    # ---- 批量处理和文本分析 ----
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """分析文本中的所有单词。"""
        import re
        
        # 简单的分词（按空格和标点符号分割）
        words = re.findall(r'\b\w+\b', text)
        
        results = {
            "input": text,
            "language": self.language,
            "word_count": len(words),
            "unique_words": len(set(words)),
            "word_analysis": [],
        }
        
        for word in words:
            if word.strip():
                word_analysis = {
                    "word": word,
                    "pos_tagging": self.get_pos_tagging(word),
                    "is_known": self.analyzer.word_is_known(word),
                }
                results["word_analysis"].append(word_analysis)
        
        return results

    def batch_analyze(self, words: List[str]) -> Dict[str, Any]:
        """批量分析多个单词。"""
        results = {
            "language": self.language,
            "total_words": len(words),
            "analysis_results": [],
        }
        
        for word in words:
            if word.strip():
                analysis = {
                    "word": word,
                    "pos_tagging": self.get_pos_tagging(word),
                    "normal_forms": self.get_normal_forms(word),
                    "is_known": self.analyzer.word_is_known(word),
                }
                results["analysis_results"].append(analysis)
        
        return results

    # ---- 词形生成和语法检查 ----
    def generate_word_forms(self, word: str, target_grammemes: List[str]) -> Dict[str, Any]:
        """根据目标语法特征生成词形。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "target_grammemes": target_grammemes,
                "generated_forms": [],
            }

        generated_forms = []
        for parse in parses:
            try:
                inflected = parse.inflect(set(target_grammemes))
                if inflected:
                    generated_forms.append({
                        "original_word": parse.word,
                        "generated_word": inflected.word,
                        "original_tag": str(parse.tag),
                        "generated_tag": str(inflected.tag),
                        "target_grammemes": target_grammemes,
                        "score": float(parse.score),
                    })
            except Exception as exc:
                generated_forms.append({
                    "original_word": parse.word,
                    "error": str(exc),
                    "target_grammemes": target_grammemes,
                })

        return {
            "input": word,
            "language": self.language,
            "target_grammemes": target_grammemes,
            "generated_forms": generated_forms,
        }

    def grammar_check(self, word: str, context_grammemes: List[str]) -> Dict[str, Any]:
        """语法检查：检查单词是否符合上下文语法要求。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "context_grammemes": context_grammemes,
                "is_grammatically_correct": False,
                "suggestions": [],
            }

        correct_parses = []
        suggestions = []
        
        for parse in parses:
            # 检查是否包含所有必需的语法特征
            parse_grammemes = set(str(g) for g in parse.tag.grammemes)
            context_set = set(context_grammemes)
            
            if context_set.issubset(parse_grammemes):
                correct_parses.append({
                    "word": parse.word,
                    "tag": str(parse.tag),
                    "grammemes": sorted([str(g) for g in parse.tag.grammemes]),
                    "score": float(parse.score),
                })
            else:
                # 尝试生成符合语法的形式
                try:
                    inflected = parse.inflect(context_set)
                    if inflected:
                        suggestions.append({
                            "suggested_word": inflected.word,
                            "suggested_tag": str(inflected.tag),
                            "original_word": parse.word,
                            "original_tag": str(parse.tag),
                        })
                except Exception:
                    pass

        return {
            "input": word,
            "language": self.language,
            "context_grammemes": context_grammemes,
            "is_grammatically_correct": len(correct_parses) > 0,
            "correct_parses": correct_parses,
            "suggestions": suggestions,
        }

    def get_smart_analysis(self, word: str) -> Dict[str, Any]:
        """智能分析：自动推断词性并展示所有相关的词形变化。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "is_known": False,
                "analysis": {
                    "pos_tagging": {"pos_tags": [], "is_known": False},
                    "comprehensive_changes": {
                        "noun_declension": {"cells": []},
                        "adjective_declension": {"cells": []},
                        "verb_conjugation": {"cells": []},
                    },
                    "stem_lexeme": {"stems": [], "lexemes": []},
                    "normal_forms": {"normal_forms": [], "count": 0},
                    "spell_check": {"is_known": False, "suggestions": []},
                }
            }

        best = self._select_best_parse(word, parses)
        pos = str(best.tag.POS) if hasattr(best.tag, "POS") and best.tag.POS else str(best.tag)

        # 获取词性标注
        try:
            pos_tagging = self.get_pos_tagging(word)
        except Exception:
            pos_tagging = {"pos_tags": [], "is_known": False}
        
        # 获取全面变化
        try:
            comprehensive_changes = self.get_comprehensive_changes(word)
        except Exception:
            comprehensive_changes = {
                "noun_declension": {"cells": []},
                "adjective_declension": {"cells": []},
                "verb_conjugation": {"cells": []},
            }
        
        # 获取词干词族
        try:
            stem_lexeme = self.get_stem_and_lexeme(word)
        except Exception:
            stem_lexeme = {"stems": [], "lexemes": []}
        
        # 获取原形
        try:
            normal_forms = self.get_normal_forms(word)
        except Exception:
            normal_forms = {"normal_forms": [], "count": 0}
        
        # 获取拼写检查
        try:
            spell_check = self.spell_check(word)
        except Exception:
            spell_check = {"is_known": False, "suggestions": []}

        return {
            "input": word,
            "language": self.language,
            "is_known": any(p.is_known for p in parses),
            "primary_pos": pos,
            "confidence": float(best.score),
            "analysis": {
                "pos_tagging": pos_tagging,
                "comprehensive_changes": comprehensive_changes,
                "stem_lexeme": stem_lexeme,
                "normal_forms": normal_forms,
                "spell_check": spell_check,
            }
        }

    def _extract_root(self, normal_form: str, pos: str) -> str:
        """提取词根（简化版，基于normal_form）。"""
        # 这是一个简化的词根提取逻辑
        # 对于动词，去掉常见后缀
        if pos in ["VERB", "INFN"]:
            # 俄语动词不定式后缀：-ть, -ти, -чь
            for suffix in ["ть", "ти", "чь"]:
                if normal_form.endswith(suffix):
                    return normal_form[:-len(suffix)]
        
        # 对于名词，直接使用normal_form作为词根
        return normal_form

    def _find_aspect_pair(self, word: str, current_aspect: str, current_normal_form: str) -> Optional[Dict[str, Any]]:
        """查找动词的配对体（完成体/未完成体）。

        仅使用 app/data/ru_verb_aspect_pairs.json 与 RU_VERB_IMPERF_TO_PERF_INFINITIVE 等手工表，
        经 pymorphy2 校验体标签。已关闭「加/去前缀」类启发式，避免系统性误配；词表未收录则返回 None。
        """
        cnf = current_normal_form.lower()
        if self.language != "ru":
            return None
        if current_aspect == "impf" and cnf in RU_VERB_ASPECT_IMP_TO_PERF:
            target_word = RU_VERB_ASPECT_IMP_TO_PERF[cnf]
            for p in self.analyzer.parse(target_word):
                pos_t = str(p.tag.POS) if hasattr(p.tag, "POS") and p.tag.POS else ""
                if pos_t != "INFN":
                    continue
                grammemes = {str(g) for g in p.tag.grammemes}
                if "perf" not in grammemes:
                    continue
                return {
                    "aspect": "perf",
                    "word": p.normal_form,
                    "tag": str(p.tag),
                    "score": float(p.score),
                }
        if current_aspect == "perf" and cnf in RU_VERB_ASPECT_PERF_TO_IMP:
            target_word = RU_VERB_ASPECT_PERF_TO_IMP[cnf]
            for p in self.analyzer.parse(target_word):
                pos_t = str(p.tag.POS) if hasattr(p.tag, "POS") and p.tag.POS else ""
                if pos_t != "INFN":
                    continue
                grammemes = {str(g) for g in p.tag.grammemes}
                if "impf" not in grammemes:
                    continue
                return {
                    "aspect": "impf",
                    "word": p.normal_form,
                    "tag": str(p.tag),
                    "score": float(p.score),
                }
        return None

    def analyze_root_and_aspect(self, word: str) -> Dict[str, Any]:
        """分析词根和动词体。"""
        parses = self.analyzer.parse(word)
        if not parses:
            return {
                "input": word,
                "language": self.language,
                "is_known": False,
                "root_analysis": [],
            }

        root_analysis = []
        for parse in parses:
            pos = str(parse.tag.POS) if hasattr(parse.tag, "POS") and parse.tag.POS else str(parse.tag)
            grammemes_set = set(str(g) for g in parse.tag.grammemes)
            
            # 提取词根
            root = self._extract_root(parse.normal_form, pos)
            
            # 提取语法特征
            cases = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
            case = next((c for c in cases if c in grammemes_set), None)
            
            genders = ["masc", "femn", "neut", "Ms-f"]
            gender = next((g for g in genders if g in grammemes_set), None)
            
            numbers = ["sing", "plur"]
            number = next((n for n in numbers if n in grammemes_set), None)
            
            tenses = ["pres", "past", "futr"]
            tense = next((t for t in tenses if t in grammemes_set), None)
            
            persons = ["1per", "2per", "3per"]
            person = next((p for p in persons if p in grammemes_set), None)
            
            # 提取动词体
            aspects = ["perf", "impf"]
            aspect = next((a for a in aspects if a in grammemes_set), None)
            
            # 构建分析信息
            info: Dict[str, Any] = {
                "word": parse.word,
                "normal_form": parse.normal_form,
                "pos": pos,
                "tag": str(parse.tag),
                "score": float(parse.score),
                "is_known": parse.is_known,
                "root": root,
                "stem": parse.normal_form,  # 词干使用normal_form
                "aspect": aspect,
                "grammemes": sorted([str(g) for g in parse.tag.grammemes]),
                "case": case,
                "gender": gender,
                "number": number,
                "tense": tense,
                "person": person,
            }
            
            # 如果是动词，尝试查找配对体
            if aspect and pos in ["VERB", "INFN"]:
                try:
                    aspect_pair = self._find_aspect_pair(word, aspect, parse.normal_form)
                    info["aspect_pair"] = aspect_pair
                except Exception:
                    info["aspect_pair"] = None
            else:
                info["aspect_pair"] = None
            
            root_analysis.append(info)

        return {
            "input": word,
            "language": self.language,
            "is_known": any(p.is_known for p in parses),
            "root_analysis": root_analysis,
        }
