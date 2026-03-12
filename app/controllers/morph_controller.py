from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse, DeclensionResponse,
    AdjectiveDeclensionResponse, VerbConjugationResponse, ComprehensiveChangesResponse,
    PosTaggingResponse, StemAndLexemeResponse, SpellCheckResponse, NormalFormsResponse,
    NumeralAnalysisResponse, AdverbAnalysisResponse, TextAnalysisResponse, BatchAnalysisResponse,
    WordGenerationResponse, GrammarCheckResponse, SmartAnalysisResponse, RootAndAspectAnalysisResponse
)
from app.bindings.providers import get_morphology_service
from app.services.morph_service import MorphologyService

router = APIRouter()


@router.get("/analyze", response_model=AnalyzeResponse)
async def analyze_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
    grammemes: Optional[List[str]] = Query(
        default=None,
        title="grammemes",
        description="可选，目标语法标签，支持多值：?grammemes=nomn&grammemes=sing",
    ),
    limit: int = Query(5, ge=1, le=32),
) -> AnalyzeResponse:
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.analyze(word=word, grammemes=grammemes, limit=limit)
        return AnalyzeResponse(**result)
    except Exception as exc:
        # 统一错误兜底，便于生产环境排查（避免 500 无细节）
        raise HTTPException(status_code=500, detail={"code": "ANALYZE_FAILED", "message": str(exc)})


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_post(
    payload: AnalyzeRequest,
) -> AnalyzeResponse:
    try:
        if not payload.word or not payload.word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(payload.language)
        result = service.analyze(
            word=payload.word,
            grammemes=payload.grammemes,
            limit=payload.limit,
        )
        return AnalyzeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "ANALYZE_FAILED", "message": str(exc)})


@router.get("/declension", response_model=DeclensionResponse)
async def declension_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> DeclensionResponse:
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.build_declension(word)
        return DeclensionResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "DECLENSION_FAILED", "message": str(exc)})


@router.get("/adjective-declension", response_model=AdjectiveDeclensionResponse)
async def adjective_declension_get(
    word: str = Query(..., min_length=1, description="输入形容词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> AdjectiveDeclensionResponse:
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.build_adjective_declension(word)
        return AdjectiveDeclensionResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "ADJECTIVE_DECLENSION_FAILED", "message": str(exc)})


@router.get("/verb-conjugation", response_model=VerbConjugationResponse)
async def verb_conjugation_get(
    word: str = Query(..., min_length=1, description="输入动词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> VerbConjugationResponse:
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.build_verb_conjugation(word)
        return VerbConjugationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "VERB_CONJUGATION_FAILED", "message": str(exc)})


@router.get("/comprehensive-changes", response_model=ComprehensiveChangesResponse)
async def comprehensive_changes_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> ComprehensiveChangesResponse:
    """获取单词的全面词形变化（名词变格+形容词变格+动词变位）。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.get_comprehensive_changes(word)
        return ComprehensiveChangesResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "COMPREHENSIVE_CHANGES_FAILED", "message": str(exc)})


# ---- 词性标注和词干提取 ----
@router.get("/pos-tagging", response_model=PosTaggingResponse)
async def pos_tagging_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> PosTaggingResponse:
    """获取单词的词性标注信息。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.get_pos_tagging(word)
        return PosTaggingResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "POS_TAGGING_FAILED", "message": str(exc)})


@router.get("/stem-lexeme", response_model=StemAndLexemeResponse)
async def stem_lexeme_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> StemAndLexemeResponse:
    """获取单词的词干和词族信息。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.get_stem_and_lexeme(word)
        return StemAndLexemeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "STEM_LEXEME_FAILED", "message": str(exc)})


# ---- 拼写校正和相似词查找 ----
@router.get("/spell-check", response_model=SpellCheckResponse)
async def spell_check_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> SpellCheckResponse:
    """拼写校正和相似词查找。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.spell_check(word)
        return SpellCheckResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "SPELL_CHECK_FAILED", "message": str(exc)})


@router.get("/normal-forms", response_model=NormalFormsResponse)
async def normal_forms_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> NormalFormsResponse:
    """获取单词的所有可能原形。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.get_normal_forms(word)
        return NormalFormsResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "NORMAL_FORMS_FAILED", "message": str(exc)})


# ---- 数词和副词形态分析 ----
@router.get("/numeral-analysis", response_model=NumeralAnalysisResponse)
async def numeral_analysis_get(
    word: str = Query(..., min_length=1, description="输入数词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> NumeralAnalysisResponse:
    """分析数词的形态变化。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.analyze_numeral(word)
        return NumeralAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "NUMERAL_ANALYSIS_FAILED", "message": str(exc)})


@router.get("/adverb-analysis", response_model=AdverbAnalysisResponse)
async def adverb_analysis_get(
    word: str = Query(..., min_length=1, description="输入副词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> AdverbAnalysisResponse:
    """分析副词的形态变化。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.analyze_adverb(word)
        return AdverbAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "ADVERB_ANALYSIS_FAILED", "message": str(exc)})


# ---- 批量处理和文本分析 ----
@router.post("/text-analysis", response_model=TextAnalysisResponse)
async def text_analysis_post(
    text: str = Query(..., min_length=1, description="输入文本"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> TextAnalysisResponse:
    """分析文本中的所有单词。"""
    try:
        if not text.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEXT", "message": "text 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.analyze_text(text)
        return TextAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "TEXT_ANALYSIS_FAILED", "message": str(exc)})


@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_post(
    words: List[str] = Query(..., description="输入单词列表"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> BatchAnalysisResponse:
    """批量分析多个单词。"""
    try:
        if not words or not any(word.strip() for word in words):
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORDS", "message": "words 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.batch_analyze(words)
        return BatchAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "BATCH_ANALYSIS_FAILED", "message": str(exc)})


# ---- 词形生成和语法检查 ----
@router.post("/generate-forms", response_model=WordGenerationResponse)
async def generate_forms_post(
    word: str = Query(..., min_length=1, description="输入单词"),
    target_grammemes: List[str] = Query(..., description="目标语法特征列表"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> WordGenerationResponse:
    """根据目标语法特征生成词形。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        if not target_grammemes:
            raise HTTPException(status_code=422, detail={"code": "INVALID_GRAMMEMES", "message": "target_grammemes 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.generate_word_forms(word, target_grammemes)
        return WordGenerationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "GENERATE_FORMS_FAILED", "message": str(exc)})


@router.post("/grammar-check", response_model=GrammarCheckResponse)
async def grammar_check_post(
    word: str = Query(..., min_length=1, description="输入单词"),
    context_grammemes: List[str] = Query(..., description="上下文语法特征列表"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> GrammarCheckResponse:
    """语法检查：检查单词是否符合上下文语法要求。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        if not context_grammemes:
            raise HTTPException(status_code=422, detail={"code": "INVALID_GRAMMEMES", "message": "context_grammemes 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.grammar_check(word, context_grammemes)
        return GrammarCheckResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "GRAMMAR_CHECK_FAILED", "message": str(exc)})


# ---- 智能分析 ----
@router.get("/smart-analysis", response_model=SmartAnalysisResponse)
async def smart_analysis_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> SmartAnalysisResponse:
    """智能分析：自动推断词性并展示所有相关的词形变化。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.get_smart_analysis(word)
        return SmartAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "SMART_ANALYSIS_FAILED", "message": str(exc)})


# ---- 词根分析和动词体标注 ----
@router.get("/root-aspect-analysis", response_model=RootAndAspectAnalysisResponse)
async def root_aspect_analysis_get(
    word: str = Query(..., min_length=1, description="输入单词"),
    language: str = Query("ru", pattern="^(ru|uk)$", description="语言：ru/uk"),
) -> RootAndAspectAnalysisResponse:
    """词根分析和动词体标注：分析单词的词根，并标注动词的完成体和未完成体。"""
    try:
        if not word.strip():
            raise HTTPException(status_code=422, detail={"code": "INVALID_WORD", "message": "word 不能为空"})
        service: MorphologyService = get_morphology_service(language)
        result = service.analyze_root_and_aspect(word)
        return RootAndAspectAnalysisResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"code": "ROOT_ASPECT_ANALYSIS_FAILED", "message": str(exc)})
