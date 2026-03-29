#!/usr/bin/env python3
"""列出「体配对」未在词表中覆盖的样本动词（仅文档/维护用）。

自 v2 起，_find_aspect_pair 已关闭前缀启发式，配对只来自：
  app/data/ru_verb_aspect_pairs.json + morph_service 内 RU_VERB_IMPERF_TO_PERF_INFINITIVE 等手工表。

本脚本用于发现「仍缺条目的常用词」，便于补 JSON 或手工表——不再模拟启发式误配。

用法：在项目根目录执行  python scripts/scan_ru_aspect_heuristic_risks.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "app" / "data" / "ru_verb_aspect_pairs.json"

# 与 morph_service.RU_VERB_IMPERF_TO_PERF_INFINITIVE 保持同步（维护时一并改）
MANUAL_IMP_TO_PERF: dict[str, str] = {
    "помогать": "помочь",
    "знать": "узнать",
    "жить": "прожить",
}

SAMPLE: tuple[str, ...] = (
    "быть",
    "есть",
    "дать",
    "жить",
    "знать",
    "идти",
    "лить",
    "вить",
)


def main() -> int:
    if not JSON_PATH.is_file():
        print("缺少", JSON_PATH, file=sys.stderr)
        return 1
    with JSON_PATH.open("r", encoding="utf-8") as f:
        imp_map = json.load(f).get("imperf_to_perf") or {}
    covered = {str(k).lower() for k in imp_map.keys()} | {str(k).lower() for k in MANUAL_IMP_TO_PERF.keys()}
    print("体配对仅来自 JSON + 手工表；下列样本是否已覆盖：\n")
    for w in SAMPLE:
        if w.lower() in covered:
            v = imp_map.get(w.lower()) or MANUAL_IMP_TO_PERF.get(w.lower())
            print(f"  {w:12} 已覆盖 -> {v}")
        else:
            print(f"  {w:12} 未覆盖（接口将返回 aspect_pair=null）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
