from __future__ import annotations

import argparse
import json
from pathlib import Path

from trestle_project import load_parameters, output_path


def _support_reactions(stations_m: list[float], line_load_kn_m: float) -> list[dict[str, float | int]]:
    reactions: list[dict[str, float | int]] = []
    for index, station in enumerate(stations_m):
        left = station - stations_m[index - 1] if index > 0 else 0.0
        right = stations_m[index + 1] - station if index < len(stations_m) - 1 else 0.0
        reactions.append(
            {
                "support": index + 1,
                "station_m": station,
                "tributary_length_m": (left + right) / 2.0,
                "reaction_kn": line_load_kn_m * (left + right) / 2.0,
            }
        )
    return reactions


def load_summary(
    area_load_kn_m2: float,
    equipment_load_kn_m: float,
    self_weight_load_kn_m: float,
    load_factor: float,
    elastic_modulus_gpa: float,
    effective_inertia_m4: float,
) -> dict[str, object]:
    params = load_parameters()
    stations_m = [station / 1000.0 for station in params.support_stations]
    total_length_m = stations_m[-1] if stations_m else 0.0
    deck_width_m = params.support_width / 1000.0
    elastic_modulus_kpa = elastic_modulus_gpa * 1_000_000.0
    area_line_load_kn_m = area_load_kn_m2 * deck_width_m
    average_line_load_kn_m = (area_line_load_kn_m + equipment_load_kn_m + self_weight_load_kn_m) * load_factor
    total_vertical_load_kn = average_line_load_kn_m * total_length_m
    spans = []
    for index in range(max(0, len(stations_m) - 1)):
        span_length = stations_m[index + 1] - stations_m[index]
        spans.append(
            {
                "span": index + 1,
                "start_m": stations_m[index],
                "end_m": stations_m[index + 1],
                "length_m": span_length,
                "simple_span_max_deflection_m": 5 * average_line_load_kn_m * span_length**4 / (384 * elastic_modulus_kpa * effective_inertia_m4),
            }
        )
    controlling_span = max(spans, key=lambda span: float(span["length_m"]), default={"span": 0, "start_m": 0.0, "end_m": 0.0, "length_m": 0.0})
    controlling_length = float(controlling_span["length_m"])
    reactions = _support_reactions(stations_m, average_line_load_kn_m)

    return {
        "assumptions": {
            "analysis_level": "conceptual_uniform_vertical_load",
            "area_load_kn_m2": area_load_kn_m2,
            "equipment_line_load_kn_m": equipment_load_kn_m,
            "self_weight_line_load_kn_m": self_weight_load_kn_m,
            "load_factor": load_factor,
            "elastic_modulus_gpa": elastic_modulus_gpa,
            "effective_inertia_m4": effective_inertia_m4,
            "deck_width_m": deck_width_m,
            "total_length_m": total_length_m,
        },
        "results": {
            "area_line_load_kn_m": area_line_load_kn_m,
            "average_line_load_kn_m": average_line_load_kn_m,
            "average_area_load_kn_m2": average_line_load_kn_m / deck_width_m if deck_width_m else 0.0,
            "total_vertical_load_kn": total_vertical_load_kn,
            "average_support_reaction_kn": total_vertical_load_kn / len(reactions) if reactions else 0.0,
            "controlling_span": controlling_span,
            "simple_span_max_moment_kn_m": average_line_load_kn_m * controlling_length**2 / 8.0,
            "simple_span_max_shear_kn": average_line_load_kn_m * controlling_length / 2.0,
            "simple_span_max_deflection_m": max((float(span["simple_span_max_deflection_m"]) for span in spans), default=0.0),
        },
        "support_reactions": reactions,
        "limitations": [
            "Uniform vertical load approximation only.",
            "Support reactions use tributary lengths.",
            "Controlling span moment, shear, and deflection use a simply supported beam estimate.",
            "Wind, seismic, dynamic effects, connection design, second-order effects, and code capacity checks are not included.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export conceptual top-load analysis for the Zhongjian8 trestle.")
    parser.add_argument("--area-load", type=float, default=3.5, help="Top area load in kN/m^2.")
    parser.add_argument("--equipment-load", type=float, default=2.0, help="Equipment line load in kN/m.")
    parser.add_argument("--self-weight-load", type=float, default=1.2, help="Structural self-weight line load in kN/m.")
    parser.add_argument("--load-factor", type=float, default=1.0, help="Load combination factor.")
    parser.add_argument("--elastic-modulus", type=float, default=206.0, help="Elastic modulus in GPa.")
    parser.add_argument("--effective-inertia", type=float, default=0.06, help="Effective vertical bending inertia in m^4.")
    parser.add_argument("--out", default=str(output_path("trestle_structural_loads.json")))
    args = parser.parse_args(argv)

    summary = load_summary(args.area_load, args.equipment_load, args.self_weight_load, args.load_factor, args.elastic_modulus, args.effective_inertia)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
