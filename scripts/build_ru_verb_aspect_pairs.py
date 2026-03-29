#!/usr/bin/env python3
"""从 CoreRussianVerbs CSV 生成俄语动词体配对 JSON（未完成体↔完成体）。

数据源：https://github.com/StorkST/CoreRussianVerbs （RussianVerbsClassification.csv）
列「Пара аспектов」格式为：未完成体/完成体（如 понимать/понять）。
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

# 与运行时代码使用相同校验逻辑时可选用 pymorphy2；无则仅按 CSV 顺序写入
try:
    from pymorphy2 import MorphAnalyzer

    _analyzer: Optional[MorphAnalyzer] = MorphAnalyzer()
except Exception:
    _analyzer = None

DEFAULT_CSV_URL = (
    "https://raw.githubusercontent.com/StorkST/CoreRussianVerbs/master/"
    "RussianVerbsClassification.csv"
)


def _aspect_of_word(word: str) -> Optional[str]:
    if not _analyzer or not word:
        return None
    best = _analyzer.parse(word)[0]
    g = {str(x) for x in best.tag.grammemes}
    if "impf" in g:
        return "impf"
    if "perf" in g:
        return "perf"
    return None


def _normalize_pair(impf: str, perf: str) -> Optional[Tuple[str, str]]:
    """若 pymorphy 与 CSV 左右相反则对调；无法识别时信任 CSV 顺序。"""
    impf, perf = impf.strip().lower(), perf.strip().lower()
    if not impf or not perf:
        return None
    ai, ap = _aspect_of_word(impf), _aspect_of_word(perf)
    if ai == "impf" and ap == "perf":
        return (impf, perf)
    if ai == "perf" and ap == "impf":
        return (perf, impf)
    return (impf, perf)


def parse_csv_rows(csv_path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    imp_to_perf: Dict[str, str] = {}
    perf_to_imp: Dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        if not header:
            return imp_to_perf, perf_to_imp
        # 列名定位（避免硬编码索引漂移）
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
            pair = _normalize_pair(left, right)
            if not pair:
                continue
            i, p = pair
            imp_to_perf[i] = p
            perf_to_imp[p] = i
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
    # 紧凑单行，避免 app/data 下 JSON 体积过大、行数爆炸（仓库约定单文件不宜过长）
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    out_path.write_text(blob, encoding="utf-8")
    print(f"写入 {out_path}，共 {len(imp_to_perf)} 对。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
