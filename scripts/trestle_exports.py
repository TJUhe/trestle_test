from __future__ import annotations

import argparse
import json
from pathlib import Path

from trestle_core import (
    TrestleParameters,
    build_members,
    create_sample_parameter_csv,
    create_sample_parameter_xlsx,
    export_3d_baseline_dxf,
    export_baseline_csv,
    export_parameters_json,
    export_segment_joints_dxf,
    export_segment_summary_csv,
    export_summary_csv,
    optimize_concept,
    parse_float_list,
    split_members_by_segment,
    tutorial_sample_parameters,
)


def _params_from_path(path: str | None) -> TrestleParameters:
    if not path:
        return TrestleParameters()
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return TrestleParameters.from_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return TrestleParameters.from_xlsx(path)
    if suffix == ".json":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        fields = TrestleParameters.__dataclass_fields__
        return TrestleParameters(**{key: value for key, value in data.items() if key in fields})
    raise ValueError(f"Unsupported parameter file: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Zhongjian8 tutorial-style trestle baseline artifacts.")
    parser.add_argument("--params", help="Optional CSV/XLSX parameter table.")
    parser.add_argument("--out-dir", default="D:/code/test/zhongjian8/outputs")
    parser.add_argument("--sample-inputs", action="store_true", help="Also write sample CSV/XLSX parameter tables.")
    parser.add_argument("--tutorial-sample", action="store_true", help="Use parameter values visible in the tutorial screenshots.")
    parser.add_argument("--slope", type=float, help="Override platform slope in degrees.")
    parser.add_argument("--slope-variants", default="", help="Comma-separated slope variants to export, e.g. 0,2,4.")
    parser.add_argument("--segment-spans", default="", help="Override splice segment lengths, e.g. 39000,38520,42000.")
    parser.add_argument("--split-segments", action="store_true", help="Export one DXF/CSV pair per splice segment.")
    args = parser.parse_args(argv)

    params = tutorial_sample_parameters() if args.tutorial_sample else _params_from_path(args.params)
    if args.slope is not None:
        params.slope_deg = args.slope
    if args.segment_spans:
        params.segment_spans = parse_float_list(args.segment_spans)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    members = build_members(params)

    paths = {
        "baseline_csv": export_baseline_csv(members, out_dir / "trestle_member_baselines.csv"),
        "summary_csv": export_summary_csv(members, out_dir / "trestle_member_summary.csv"),
        "segment_summary_csv": export_segment_summary_csv(members, params, out_dir / "trestle_segment_summary.csv"),
        "baseline_dxf": export_3d_baseline_dxf(members, out_dir / "trestle_3d_baselines.dxf"),
        "tutorial_replica_dxf": export_3d_baseline_dxf(members, out_dir / "trestle_tutorial_replica.dxf", params=params, include_splices=True),
        "splice_dxf": export_segment_joints_dxf(params, out_dir / "trestle_splice_joints.dxf"),
        "parameters_json": export_parameters_json(params, out_dir / "trestle_parameters.json"),
    }
    if args.split_segments:
        segment_dir = out_dir / "segments"
        for label, segment_members in split_members_by_segment(members, params).items():
            paths[f"{label}_csv"] = export_baseline_csv(segment_members, segment_dir / f"{label}_member_baselines.csv")
            paths[f"{label}_dxf"] = export_3d_baseline_dxf(segment_members, segment_dir / f"{label}_3d_baselines.dxf")
    if args.sample_inputs:
        paths["sample_csv"] = create_sample_parameter_csv(out_dir / "sample_parameters.csv", params)
        paths["sample_xlsx"] = create_sample_parameter_xlsx(out_dir / "sample_parameters.xlsx", params)
    optimization = optimize_concept(params)
    (out_dir / "trestle_concept_optimization.json").write_text(
        __import__("json").dumps(optimization, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths["optimization_json"] = out_dir / "trestle_concept_optimization.json"

    if args.slope_variants:
        for raw in args.slope_variants.split(","):
            slope = float(raw.strip())
            variant = tutorial_sample_parameters(slope_deg=slope) if args.tutorial_sample else TrestleParameters(**{**params.__dict__, "slope_deg": slope})
            if args.segment_spans:
                variant.segment_spans = parse_float_list(args.segment_spans)
            variant_members = build_members(variant)
            slug = str(slope).replace(".", "p").replace("-", "m")
            paths[f"slope_{slug}_dxf"] = export_3d_baseline_dxf(variant_members, out_dir / f"trestle_3d_baselines_slope_{slug}.dxf", params=variant, include_splices=True)
            paths[f"slope_{slug}_params"] = export_parameters_json(variant, out_dir / f"trestle_parameters_slope_{slug}.json")

    print(f"members: {len(members)}")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
