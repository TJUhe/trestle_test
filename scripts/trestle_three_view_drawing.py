from __future__ import annotations

import sys
from pathlib import Path

from drawing2d import Drawing

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from trestle_core import build_members, compute_segment_ranges, summarize_members
from trestle_project import load_parameters


SCALE = 250.0
PARAMS = load_parameters()
MEMBERS = build_members(PARAMS)


def _mm(value: float) -> float:
    return value / SCALE


def _view_title(d: Drawing, x: float, y: float, title: str) -> None:
    d.text(x, y, title, height=5.0, layer="title")
    d.line((x, y - 2.0), (x + 118.0, y - 2.0), layer="title")


def _elevation_at(station: float) -> float:
    return PARAMS.start_elevation + __import__("math").tan(__import__("math").radians(PARAMS.slope_deg)) * station


def _project_elevation(point):
    return point[0], point[2]


def _project_plan(point):
    return point[0], point[1]


def _project_end(point):
    return point[1], point[2]


def _draw_projected_members(d: Drawing, origin, members, projector, layer_map, scale=SCALE) -> None:
    ox, oy = origin
    for member in members:
        x0, y0 = projector(member.start)
        x1, y1 = projector(member.end)
        layer = layer_map.get(member.category, "visible")
        d.line((ox + x0 / scale, oy + y0 / scale), (ox + x1 / scale, oy + y1 / scale), layer=layer)


def _draw_elevation(d: Drawing, origin) -> None:
    ox, oy = origin
    layer_map = {
        "deck_main_beam": "main",
        "deck_cross_beam": "secondary",
        "deck_secondary_beam": "secondary",
        "cantilever_edge_beam": "secondary",
        "platform_brace": "brace",
        "column": "column",
        "transverse_column_brace": "brace",
        "longitudinal_support_brace": "brace",
        "truss_upper_chord": "truss",
        "truss_lower_chord": "truss",
        "truss_vertical": "truss",
        "truss_diagonal": "truss",
    }
    _draw_projected_members(d, origin, MEMBERS, _project_elevation, layer_map)
    stations = PARAMS.support_stations
    d.line((ox, oy), (ox + _mm(stations[-1]), oy), layer="center")
    d.linear_dimension((ox + _mm(stations[0]), oy), (ox + _mm(stations[-1]), oy), offset=-18, text=f"总长 {int(stations[-1])}")
    dim_y = oy + _mm(max(_elevation_at(x) for x in stations)) + 10
    for a, b in zip(stations[:-1], stations[1:]):
        d.linear_dimension((ox + _mm(a), dim_y), (ox + _mm(b), dim_y), offset=6, text=f"{int(b - a)}")
    for index, station in enumerate(stations, start=1):
        d.text(ox + _mm(station) - 5, oy - 9, f"Z{index}\\n{int(station)}", height=2.6, layer="annotation")
    for segment_index, (_start, end) in enumerate(compute_segment_ranges(PARAMS)[:-1], start=1):
        x = ox + _mm(end)
        d.line((x, oy - 8), (x, oy + _mm(_elevation_at(end)) + 20), layer="standard")
        d.text(x + 2, oy + _mm(_elevation_at(end)) + 23, f"拼接缝 P{segment_index}/P{segment_index + 1}", height=2.8, layer="standard")
    d.linear_dimension((ox + _mm(stations[-1]) + 18, oy), (ox + _mm(stations[-1]) + 18, oy + _mm(_elevation_at(stations[-1]))), offset=9, text=f"端部标高 {int(round(_elevation_at(stations[-1])))}")
    d.text(ox + 8, dim_y + 18, f"立面：支架里程参数；倾角 {PARAMS.slope_deg} deg；拼接段 {len(compute_segment_ranges(PARAMS))} 段", height=3.0, layer="annotation")


def _draw_plan(d: Drawing, origin) -> None:
    ox, oy = origin
    layer_map = {
        "deck_main_beam": "main",
        "deck_cross_beam": "main",
        "deck_secondary_beam": "secondary",
        "cantilever_edge_beam": "secondary",
        "platform_brace": "brace",
        "truss_upper_chord": "truss",
        "truss_lower_chord": "truss",
        "truss_diagonal": "truss",
    }
    deck_members = [m for m in MEMBERS if m.category not in {"column", "transverse_column_brace", "longitudinal_support_brace", "truss_vertical"}]
    _draw_projected_members(d, origin, deck_members, _project_plan, layer_map)
    stations = PARAMS.support_stations
    y_min = min(min(m.start[1], m.end[1]) for m in deck_members)
    y_max = max(max(m.start[1], m.end[1]) for m in deck_members)
    d.line((ox, oy), (ox + _mm(stations[-1]), oy), layer="center")
    d.linear_dimension((ox, oy + _mm(y_min)), (ox + _mm(stations[-1]), oy + _mm(y_min)), offset=-15, text=f"总长 {int(stations[-1])}")
    d.linear_dimension((ox + _mm(stations[-1]) + 15, oy + _mm(y_min)), (ox + _mm(stations[-1]) + 15, oy + _mm(y_max)), offset=8, text=f"平台总宽 {int(y_max - y_min)}")
    for segment_index, (_start, end) in enumerate(compute_segment_ranges(PARAMS)[:-1], start=1):
        x = ox + _mm(end)
        d.line((x, oy + _mm(y_min) - 5), (x, oy + _mm(y_max) + 5), layer="standard")
        d.text(x + 2, oy + _mm(y_max) + 8, f"P{segment_index}|P{segment_index + 1}", height=2.8, layer="standard")
    d.text(ox + 8, oy + _mm(y_max) + 18, f"平面：设备宽 {int(PARAMS.equipment_width)}；左/右悬挑 {int(PARAMS.left_cantilever)}/{int(PARAMS.right_cantilever)}；平台分格 <= {int(PARAMS.platform_segment_limit)}", height=3.0, layer="annotation")


def _draw_end_view(d: Drawing, origin, station: float) -> None:
    ox, oy = origin
    near = [m for m in MEMBERS if abs(m.start[0] - station) < 1e-6 and abs(m.end[0] - station) < 1e-6]
    layer_map = {
        "deck_cross_beam": "main",
        "column": "column",
        "transverse_column_brace": "brace",
        "truss_vertical": "truss",
    }
    _draw_projected_members(d, origin, near, _project_end, layer_map)
    y_min = min(min(m.start[1], m.end[1]) for m in near)
    y_max = max(max(m.start[1], m.end[1]) for m in near)
    z_max = max(max(m.start[2], m.end[2]) for m in near)
    d.linear_dimension((ox + _mm(y_min), oy), (ox + _mm(y_max), oy), offset=-14, text=f"{int(y_max - y_min)}")
    d.linear_dimension((ox + _mm(y_max) + 15, oy), (ox + _mm(y_max) + 15, oy + _mm(z_max)), offset=9, text=f"支架高 {int(round(z_max))}")
    d.text(ox + _mm(y_min), oy + _mm(z_max) + 10, f"端视：Z{len(PARAMS.support_stations)} / X={int(station)}", height=3.0, layer="annotation")


def _draw_statistics(d: Drawing, x: float, y: float) -> None:
    d.text(x, y, "构件统计（由同一基线表生成）", height=4.2, layer="title")
    y -= 8
    for row in summarize_members(MEMBERS)[:12]:
        text = f"{row['role']} | {row['cad_layer']} | {row['count']} 根 | 总长 {row['total_length']:.0f}"
        d.text(x, y, text, height=2.8, layer="annotation")
        y -= 5.8


def _draw_notes(d: Drawing, x: float, y: float) -> None:
    notes = [
        "教程映射：Excel/参数表 -> 定位点 -> 空间点 -> 杆件基线 -> CAD 图层/3D3S 基线。",
        "本图、STEP、3D DXF、CSV 统计均由 trestle_core.py 的同一成员基线生成。",
        "方案器：platform_scheme / brace_scheme / truss_scheme 可替换平台、支撑、桁架策略。",
        "优化器：当前为概念评分占位，不替代 YJK/3D3S 结构计算。",
        "施工图深化：截面、节点、基础、焊缝、螺栓、防腐、防火需经正式设计校核。",
    ]
    for i, note in enumerate(notes):
        d.text(x, y - i * 6.5, note, height=3.0, layer="annotation")


def gen_drawing():
    d = Drawing(
        title="工业皮带机栈桥参数化三视图",
        sheet="A0",
        orientation="landscape",
        scale="1:250",
        author="Codex / zhongjian8",
        revision="C",
    )
    d.layer("main", color=4)
    d.layer("secondary", color=3)
    d.layer("brace", color=1)
    d.layer("column", color=8)
    d.layer("truss", color=5)
    d.layer("standard", color=2)

    _view_title(d, 35, 780, "A-A 立面图")
    _draw_elevation(d, (45, 650))

    _view_title(d, 35, 470, "B-B 平面图")
    _draw_plan(d, (45, 405))

    _view_title(d, 590, 780, "C-C 端视图")
    _draw_end_view(d, (605, 650), PARAMS.support_stations[-1])

    _view_title(d, 590, 470, "基线统计与说明")
    _draw_statistics(d, 590, 450)
    _draw_notes(d, 590, 360)

    d.text(35, 65, "图例：蓝=主梁/横梁，绿=次梁/外挑，红=支撑，紫=桁架，灰=柱。尺寸单位 mm。", height=3.0, layer="annotation")
    d.title_block(project="zhongjian8 conveyor trestle", drawing_no="ZJ8-TRESTLE-2D-001")
    return d
