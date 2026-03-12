from functools import lru_cache
from typing import Generator

from app.services.morph_service import MorphologyService


@lru_cache(maxsize=2)
def _get_service_ru() -> MorphologyService:
    return MorphologyService(language="ru")


@lru_cache(maxsize=2)
def _get_service_uk() -> MorphologyService:
    return MorphologyService(language="uk")


def get_morphology_service(language: str = "ru") -> MorphologyService:
    """Binding: 根据语言提供对应的服务实例。
    通过 FastAPI Depends 使用，可视为 GetX Binding 的等价注入点。
    """
    if language == "uk":
        return _get_service_uk()
    return _get_service_ru()
