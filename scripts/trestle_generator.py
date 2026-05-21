from __future__ import annotations

from build123d import Box, Color, Compound, Location, Plane, Vector

from trestle_core import SECTION_SIZES, BaselineMember, build_members, compute_segment_ranges
from trestle_project import load_parameters


COLOR_BY_CATEGORY = {
    "deck_main_beam": Color(0.15, 0.36, 0.72),
    "deck_cross_beam": Color(0.15, 0.36, 0.72),
    "deck_secondary_beam": Color(0.12, 0.55, 0.42),
    "cantilever_edge_beam": Color(0.12, 0.55, 0.42),
    "platform_brace": Color(0.88, 0.28, 0.20),
    "column": Color(0.55, 0.56, 0.58),
    "transverse_column_brace": Color(0.88, 0.28, 0.20),
    "longitudinal_support_brace": Color(0.88, 0.28, 0.20),
    "truss_upper_chord": Color(0.62, 0.32, 0.78),
    "truss_lower_chord": Color(0.62, 0.32, 0.78),
    "truss_vertical": Color(0.62, 0.32, 0.78),
    "truss_diagonal": Color(0.62, 0.32, 0.78),
}


PARAMS = load_parameters()


def _member_solid(member: BaselineMember):
    start = Vector(member.start)
    end = Vector(member.end)
    direction = end - start
    length = direction.length
    if length <= 1e-6:
        raise ValueError(f"Zero-length member in {member.category}: {member.start}")

    z_axis = direction.normalized()
    up_hint = Vector(0, 0, 1)
    if abs(z_axis.dot(up_hint)) > 0.95:
        up_hint = Vector(0, 1, 0)
    x_axis = up_hint.cross(z_axis).normalized()
    center = (start + end) * 0.5
    width, depth = SECTION_SIZES[member.section]
    part = Box(width, depth, length).move(Location(Plane(origin=center, x_dir=x_axis, z_dir=z_axis)))
    part.label = f"{member.category}:{member.id}"
    part.color = COLOR_BY_CATEGORY.get(member.category, Color(0.35, 0.35, 0.35))
    return part


def _splice_marker_solids(station: float, index: int):
    top_z = PARAMS.start_elevation + __import__("math").tan(__import__("math").radians(PARAMS.slope_deg)) * station
    width = PARAMS.support_width + 1200.0
    height = top_z + 3200.0
    y0 = PARAMS.y_origin - width / 2.0
    y1 = PARAMS.y_origin + width / 2.0
    pieces = [
        Box(130.0, 120.0, height).move(Location((station, y0, height / 2.0))),
        Box(130.0, 120.0, height).move(Location((station, y1, height / 2.0))),
        Box(130.0, width + 120.0, 120.0).move(Location((station, PARAMS.y_origin, height))),
    ]
    for piece_index, piece in enumerate(pieces, start=1):
        piece.label = f"splice_marker:P{index}/P{index + 1}:{piece_index}"
        piece.color = Color(1.0, 0.1, 0.05)
    return pieces


def gen_step():
    members = build_members(PARAMS)
    solids = [_member_solid(member) for member in members]
    for index, (_start, end) in enumerate(compute_segment_ranges(PARAMS)[:-1], start=1):
        solids.extend(_splice_marker_solids(end, index))
    return Compound(children=solids, label="zhongjian8_tutorial_style_trestle")


if __name__ == "__main__":
    members = build_members(PARAMS)
    print(f"Generated {len(members)} tutorial-style baseline members")
