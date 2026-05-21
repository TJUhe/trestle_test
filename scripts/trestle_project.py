from __future__ import annotations

import json
import os
from pathlib import Path

from trestle_core import TrestleParameters, parse_float_list


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARAMS = ROOT / "data" / "trestle_parameters.csv"
DEFAULT_OUT_DIR = ROOT / "outputs"


def load_parameters(path: str | Path | None = None) -> TrestleParameters:
    source = Path(os.environ.get("ZJ8_PARAMS") or path or DEFAULT_PARAMS)
    if source.suffix.lower() == ".csv":
        params = TrestleParameters.from_csv(source)
    elif source.suffix.lower() in {".xlsx", ".xlsm"}:
        params = TrestleParameters.from_xlsx(source)
    elif source.suffix.lower() == ".json":
        data = json.loads(source.read_text(encoding="utf-8"))
        fields = TrestleParameters.__dataclass_fields__
        params = TrestleParameters(**{key: value for key, value in data.items() if key in fields})
    else:
        raise ValueError(f"Unsupported Zhongjian8 parameter file: {source}")

    if os.environ.get("ZJ8_SLOPE_DEG"):
        params.slope_deg = float(os.environ["ZJ8_SLOPE_DEG"])
    if os.environ.get("ZJ8_SEGMENT_SPANS"):
        params.segment_spans = parse_float_list(os.environ["ZJ8_SEGMENT_SPANS"])
    return params


def output_path(filename: str) -> Path:
    return Path(os.environ.get("ZJ8_OUT_DIR") or DEFAULT_OUT_DIR) / filename
