#!/usr/bin/env python3
"""从 CoreRussianVerbs CSV 生成俄语动词体配对 JSON（未完成体↔完成体）。

数据源：https://github.com/StorkST/CoreRussianVerbs （RussianVerbsClassification.csv）
列「Пара аспектов」格式为：未完成体/完成体（如 понимать/понять）。

同一未完成体若出现多行配对，**先出现的行优先**（避免后行覆盖为错误项，如 говорить/сказать 须优先于 говорить/поговорить）。
仅当 pymorphy2 能确认左为 impf INFN、右为 perf INFN 时才收录；否则丢弃该行。
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from pymorphy2 import MorphAnalyzer

    _analyzer: Optional[MorphAnalyzer] = MorphAnalyzer()
except Exception:
    _analyzer = None

DEFAULT_CSV_URL = (
    "https://raw.githubusercontent.com/StorkST/CoreRussianVerbs/master/"
    "RussianVerbsClassification.csv"
)


def _infn_aspect(word: str) -> Optional[str]:
    if not _analyzer or not word:
        return None
    for prs in _analyzer.parse(word):
        pos_t = str(prs.tag.POS) if hasattr(prs.tag, "POS") and prs.tag.POS else ""
        if pos_t != "INFN":
            continue
        g = {str(x) for x in prs.tag.grammemes}
        if "impf" in g:
            return "impf"
        if "perf" in g:
            return "perf"
    return None


def _normalize_pair_strict(left: str, right: str) -> Optional[Tuple[str, str]]:
    """仅接受「未完成体 INFN ↔ 完成体 INFN」；与 pymorphy 不一致则丢弃。"""
    a, b = left.strip().lower(), right.strip().lower()
    if not a or not b:
        return None
    ai, bi = _infn_aspect(a), _infn_aspect(b)
    if ai == "impf" and bi == "perf":
        return (a, b)
    if ai == "perf" and bi == "impf":
        return (b, a)
    return None


def parse_csv_rows(csv_path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    imp_to_perf: Dict[str, str] = {}
    perf_to_imp: Dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        if not header:
            return imp_to_perf, perf_to_imp
        try:
            idx_pair = header.index("Пара аспектов")
        except ValueError:
            idx_pair = 12
        for row in reader:
            if len(row) <= idx_pair:
                continue
            raw = (row[idx_pair] or "").strip()
            if not raw or "/" not in raw:
                continue
            parts = raw.split("/", 1)
            if len(parts) != 2:
                continue
            left, right = parts[0].strip(), parts[1].strip()
            if not left or not right:
                continue
            pair = _normalize_pair_strict(left, right)
            if not pair:
                continue
            i_lemma, p_lemma = pair
            if i_lemma in imp_to_perf:
                continue
            imp_to_perf[i_lemma] = p_lemma
    for i_lemma, p_lemma in imp_to_perf.items():
        if p_lemma in perf_to_imp:
            continue
        perf_to_imp[p_lemma] = i_lemma
    return imp_to_perf, perf_to_imp


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out_path = root / "app" / "data" / "ru_verb_aspect_pairs.json"
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if csv_arg:
        csv_path = Path(csv_arg)
    else:
        csv_path = root / "scripts" / "RussianVerbsClassification.csv"
        if not csv_path.is_file():
            print(f"下载 CSV -> {csv_path}", file=sys.stderr)
            urllib.request.urlretrieve(DEFAULT_CSV_URL, csv_path)
    imp_to_perf, perf_to_imp = parse_csv_rows(csv_path)
    payload = {
        "source": "CoreRussianVerbs / RussianVerbsClassification.csv",
        "source_url": "https://github.com/StorkST/CoreRussianVerbs",
        "license_note": "教学用动词分类数据；使用时请保留来源说明。",
        "imperf_to_perf": dict(sorted(imp_to_perf.items())),
        "perf_to_imperf": dict(sorted(perf_to_imp.items())),
        "pair_count": len(imp_to_perf),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    out_path.write_text(blob, encoding="utf-8")
    print(f"写入 {out_path}，共 {len(imp_to_perf)} 对（严格校验 + 未完成体首次出现优先）。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
