from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """请求模型：查询词形与（可选）目标语法特征。"""
    word: str = Field(..., description="输入的俄语/乌克兰语单词")
    language: Literal["ru", "uk"] = Field("ru", description="语言：ru 或 uk")
    grammemes: Optional[List[str]] = Field(
        default=None,
        description="可选：需要尝试变形到的语法标签集合（如: nomn, sing, masc）",
    )
    limit: int = Field(5, ge=1, le=32, description="返回候选解析数量上限")


class ParseItem(BaseModel):
    """单个候选的解析以及可选的变形结果。"""
    normal_form: str
    tag: str
    score: float
    methods_stack: List[str]
    grammemes: List[str]
    inflected: Optional[Dict[str, Any]] = None  # 包含 word 与 tag


class AnalyzeResponse(BaseModel):
    """响应模型：原词、语言、解析列表。"""
    input: str
    language: Literal["ru", "uk"]
    parses: List[ParseItem]


class DeclensionCell(BaseModel):
    case: str
    number: str
    gender: Optional[str] = None
    form: Optional[str] = None


class DeclensionResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    normal_form: str
    pos: str
    cells: List[DeclensionCell]


class AdjectiveDeclensionCell(BaseModel):
    case: Optional[str] = None  # 格（用于完整变格），None 表示短尾形式或比较级
    number: str
    gender: Optional[str] = None
    form: Optional[str] = None
    short: Optional[bool] = None  # True 表示短尾形式
    comparative: Optional[bool] = None  # True 表示比较级形式


class AdjectiveDeclensionResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    normal_form: str
    pos: str
    cells: List[AdjectiveDeclensionCell]


class VerbConjugationCell(BaseModel):
    """动词变位单元格，支持多种动词形式"""
    # 基础字段
    type: Optional[str] = None  # "conjugation"（变位）, "gerund"（副动词）, "imperative"（命令式）, "participle"（形动词）
    tense: Optional[str] = None  # "pres", "past", "futr"
    person: Optional[str] = None  # "1per", "2per", "3per"
    number: Optional[str] = None  # "sing", "plur"
    gender: Optional[str] = None  # "masc", "femn", "neut"
    form: Optional[str] = None  # 词形
    
    # 副动词相关字段
    aspect: Optional[str] = None  # "perf", "impf"（用于副动词）
    
    # 形动词相关字段
    voice: Optional[str] = None  # "actv"（主动）, "pssv"（被动）, "rfle"（反身）
    case: Optional[str] = None  # "nomn", "gent", "datv", "accs", "ablt", "loct"（用于形动词）
    animacy: Optional[str] = None  # "anim", "inan"（用于形动词四格）
    short: Optional[bool] = None  # True 表示短尾形式（用于被动形动词）


class VerbConjugationResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    normal_form: str
    pos: str
    aspect: Optional[str] = None  # "perf"（完成体）或 "impf"（未完成体），用于前端判断时态标签
    cells: List[VerbConjugationCell]


class ComprehensiveChangesResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    normal_form: str
    pos: str
    noun_declension: DeclensionResponse
    adjective_declension: AdjectiveDeclensionResponse
    verb_conjugation: VerbConjugationResponse


# ---- 词性标注和词干提取 ----
class PosTagInfo(BaseModel):
    word: str
    normal_form: str
    pos: str
    tag: str
    score: float
    is_known: bool
    grammemes: List[str]
    cyr_grammemes: List[str]
    case: Optional[str] = None
    gender: Optional[str] = None
    number: Optional[str] = None
    person: Optional[str] = None
    tense: Optional[str] = None
    aspect: Optional[str] = None
    voice: Optional[str] = None
    mood: Optional[str] = None
    animacy: Optional[str] = None


class PosTaggingResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    pos_tags: List[PosTagInfo]
    is_known: bool


class StemInfo(BaseModel):
    word: str
    stem: str
    pos: str
    score: float


class LexemeForm(BaseModel):
    word: str
    tag: str
    grammemes: List[str]


class LexemeInfo(BaseModel):
    word: str
    lexeme_forms: List[LexemeForm]
    total_forms: int


class StemAndLexemeResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    stems: List[StemInfo]
    lexemes: List[LexemeInfo]


# ---- 拼写校正和相似词查找 ----
class SpellSuggestion(BaseModel):
    word: str
    normal_form: str
    tag: str
    score: float


class SpellCheckResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    is_known: bool
    suggestions: List[SpellSuggestion]


class NormalFormsResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    normal_forms: List[str]
    count: int
    error: Optional[str] = None


# ---- 数词和副词形态分析 ----
class NumeralCaseForm(BaseModel):
    case: str
    form: str
    tag: str


class NumeralForm(BaseModel):
    word: str
    normal_form: str
    tag: str
    score: float
    case_forms: List[NumeralCaseForm]


class NumeralAnalysisResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    numeral_forms: List[NumeralForm]


class AdverbDegreeForm(BaseModel):
    type: str  # "comparative" or "superlative"
    form: str
    tag: str


class AdverbForm(BaseModel):
    word: str
    normal_form: str
    tag: str
    score: float
    degree_forms: List[AdverbDegreeForm]


class AdverbAnalysisResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    adverb_forms: List[AdverbForm]


# ---- 批量处理和文本分析 ----
class WordAnalysis(BaseModel):
    word: str
    pos_tagging: PosTaggingResponse
    is_known: bool


class TextAnalysisResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    word_count: int
    unique_words: int
    word_analysis: List[WordAnalysis]


class BatchAnalysisItem(BaseModel):
    word: str
    pos_tagging: PosTaggingResponse
    normal_forms: NormalFormsResponse
    is_known: bool


class BatchAnalysisResponse(BaseModel):
    language: Literal["ru", "uk"]
    total_words: int
    analysis_results: List[BatchAnalysisItem]


# ---- 词形生成和语法检查 ----
class GeneratedForm(BaseModel):
    original_word: str
    generated_word: Optional[str] = None
    original_tag: str
    generated_tag: Optional[str] = None
    target_grammemes: List[str]
    score: float
    error: Optional[str] = None


class WordGenerationResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    target_grammemes: List[str]
    generated_forms: List[GeneratedForm]


class GrammarSuggestion(BaseModel):
    suggested_word: str
    suggested_tag: str
    original_word: str
    original_tag: str


class GrammarCheckResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    context_grammemes: List[str]
    is_grammatically_correct: bool
    correct_parses: List[PosTagInfo]
    suggestions: List[GrammarSuggestion]


# ---- 智能分析 ----
class SmartAnalysisResponse(BaseModel):
    input: str
    language: Literal["ru", "uk"]
    is_known: bool
    primary_pos: str
    confidence: float
    analysis: Dict[str, Any]


# ---- 词根分析和动词体标注 ----
class VerbAspectPair(BaseModel):
    """动词体配对信息（完成体和未完成体）"""
    aspect: str  # "perf" 或 "impf"
    word: str
    tag: str
    score: float


class RootAnalysisInfo(BaseModel):
    """词根分析详细信息"""
    word: str
    normal_form: str
    pos: str
    tag: str
    score: float
    is_known: bool
    
    # 词根相关
    root: str  # 词根（通过normal_form提取）
    stem: str  # 词干
    
    # 动词体信息（仅动词有效）
    aspect: Optional[str] = None  # "perf" 或 "impf"
    aspect_pair: Optional[VerbAspectPair] = None  # 配对的另一个体
    
    # 语法特征
    grammemes: List[str]
    case: Optional[str] = None
    gender: Optional[str] = None
    number: Optional[str] = None
    tense: Optional[str] = None
    person: Optional[str] = None


class RootAndAspectAnalysisResponse(BaseModel):
    """词根和动词体分析响应"""
    input: str
    language: Literal["ru", "uk"]
    is_known: bool
    root_analysis: List[RootAnalysisInfo]
