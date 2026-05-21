from __future__ import annotations

import html
import json
from pathlib import Path

from trestle_core import build_members, compute_segment_ranges, summarize_members
from trestle_project import load_parameters, output_path


OUT = output_path("trestle_parametric_preview.html")


def _member_payload():
    params = load_parameters()
    members = build_members(params)
    return {
        "params": params.to_dict(),
        "members": [member.as_row() for member in members],
        "summary": summarize_members(members),
        "segments": compute_segment_ranges(params),
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload_data = _member_payload()
    default_slope = float(payload_data["params"]["slope_deg"])
    default_segments = ",".join(str(int(value) if float(value).is_integer() else value) for value in payload_data["params"]["segment_spans"])
    total_station = int(round(payload_data["params"]["support_stations"][-1]))
    payload = json.dumps(payload_data, ensure_ascii=False)
    OUT.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>中建八局栈桥参数化复刻预览</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202124;
      --muted: #5f6368;
      --line: #d8dee6;
      --main: #1c7ed6;
      --secondary: #2f9e44;
      --brace: #d62222;
      --truss: #7048e8;
      --column: #6c757d;
      --splice: #d6b422;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      background: #eef1f5;
      color: var(--ink);
    }}
    header {{
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      background: #fff;
      border-bottom: 1px solid var(--line);
    }}
    header strong {{ font-size: 17px; }}
    header span {{ color: var(--muted); font-size: 13px; }}
    main {{
      display: grid;
      grid-template-columns: 320px 1fr;
      min-height: calc(100vh - 56px);
    }}
    aside {{
      background: #fff;
      border-right: 1px solid var(--line);
      padding: 18px;
      overflow: auto;
    }}
    .field {{ margin-bottom: 16px; }}
    label {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    input[type="range"], input[type="text"] {{ width: 100%; }}
    input[type="text"] {{
      border: 1px solid #cfd4da;
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 13px;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 16px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      min-height: 58px;
    }}
    .stat small {{ color: var(--muted); display: block; margin-bottom: 6px; }}
    .stat b {{ font-size: 16px; }}
    .legend {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 12px;
      margin-top: 18px;
      font-size: 13px;
    }}
    .swatch {{
      display: inline-block;
      width: 18px;
      height: 3px;
      vertical-align: middle;
      margin-right: 6px;
    }}
    section.viewer {{
      padding: 18px;
      overflow: auto;
    }}
    .sheet {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 10px 28px rgba(30, 41, 59, .12);
      min-width: 980px;
      padding: 12px;
    }}
    svg {{
      display: block;
      width: 100%;
      height: auto;
      background: #fbfcfe;
      border: 1px solid #e6eaf0;
    }}
    .member-main {{ stroke: var(--main); }}
    .member-secondary {{ stroke: var(--secondary); }}
    .member-brace {{ stroke: var(--brace); }}
    .member-truss {{ stroke: var(--truss); }}
    .member-column {{ stroke: var(--column); }}
    .splice {{ stroke: var(--splice); stroke-width: 2.2; stroke-dasharray: 6 5; }}
    .grid {{ stroke: #edf0f5; stroke-width: 1; }}
    .axis {{ stroke: #adb5bd; stroke-width: 1; stroke-dasharray: 4 4; }}
    .label {{ fill: #343a40; font-size: 12px; }}
    .title {{ fill: #111827; font-size: 15px; font-weight: 700; }}
    .dim {{ fill: #495057; font-size: 12px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 18px;
      font-size: 12px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 6px 4px;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <strong>工业皮带机栈桥参数化复刻预览</strong>
    <span>项目参数：平台宽 {int(payload_data["params"]["support_width"])} | 起点标高 {int(payload_data["params"]["start_elevation"])} | 支架总里程 {total_station}</span>
  </header>
  <main>
    <aside>
      <div class="field">
        <label for="slope"><span>平台倾角</span><b id="slopeValue">{default_slope:.1f}°</b></label>
        <input id="slope" type="range" min="-2" max="8" step="0.1" value="{default_slope:g}">
      </div>
      <div class="field">
        <label for="segments"><span>拼接分段长度</span><b>mm</b></label>
        <input id="segments" type="text" value="{default_segments}">
      </div>
      <div class="stat-grid">
        <div class="stat"><small>构件数</small><b id="memberCount">-</b></div>
        <div class="stat"><small>拼接段</small><b id="segmentCount">-</b></div>
        <div class="stat"><small>末端标高</small><b id="endElevation">-</b></div>
        <div class="stat"><small>总长度</small><b id="totalLength">{total_station}</b></div>
      </div>
      <div class="legend">
        <span><i class="swatch" style="background:var(--main)"></i>主梁/横梁</span>
        <span><i class="swatch" style="background:var(--secondary)"></i>次梁/外挑</span>
        <span><i class="swatch" style="background:var(--brace)"></i>支撑</span>
        <span><i class="swatch" style="background:var(--truss)"></i>桁架</span>
        <span><i class="swatch" style="background:var(--column)"></i>柱</span>
        <span><i class="swatch" style="background:var(--splice)"></i>拼接缝</span>
      </div>
      <table>
        <thead><tr><th>类别</th><th>数量</th><th>总长</th></tr></thead>
        <tbody id="summaryRows"></tbody>
      </table>
    </aside>
    <section class="viewer">
      <div class="sheet">
        <svg id="canvas" viewBox="0 0 1320 760" aria-label="参数化栈桥线框预览"></svg>
      </div>
    </section>
  </main>
  <script>
    const data = {payload};
    const svg = document.getElementById("canvas");
    const slopeInput = document.getElementById("slope");
    const segmentsInput = document.getElementById("segments");
    const stations = data.params.support_stations;
    const startElevation = data.params.start_elevation;
    const total = stations[stations.length - 1];
    const scaleX = 1100 / total;
    const scaleZ = 500 / 25000;
    const scaleY = 210 / 8000;

    function parseSegments() {{
      return segmentsInput.value.split(/[,，;；\\s]+/).map(Number).filter(v => Number.isFinite(v) && v > 0);
    }}

    function segmentRanges() {{
      const values = parseSegments();
      if (!values.length) return [[0, total]];
      const ranges = [];
      let cursor = 0;
      for (const span of values) {{
        const end = Math.min(total, cursor + span);
        ranges.push([cursor, end]);
        cursor = end;
        if (cursor >= total - 1e-6) break;
      }}
      if (ranges[ranges.length - 1][1] < total - 1e-6) ranges.push([cursor, total]);
      return ranges;
    }}

    function projectedZ(x, storedZ) {{
      if (Math.abs(storedZ) < 1e-6) return 0;
      return startElevation + Math.tan(Number(slopeInput.value) * Math.PI / 180) * x + (storedZ - startElevation);
    }}

    function projectedMemberZ(member, prefix) {{
      const x = Number(member[`${{prefix}}_x`]);
      const storedZ = Number(member[`${{prefix}}_z`]);
      if (Math.abs(storedZ) < 1e-6) return 0;
      if (member.category === "column") return projectedZ(x, startElevation) * (storedZ / startElevation);
      return projectedZ(x, storedZ);
    }}

    function memberClass(category) {{
      if (category.includes("truss")) return "member-truss";
      if (category.includes("brace")) return "member-brace";
      if (category === "column") return "member-column";
      if (category.includes("secondary") || category.includes("cantilever")) return "member-secondary";
      return "member-main";
    }}

    function line(x1, y1, x2, y2, cls, width = 1.1) {{
      const item = document.createElementNS("http://www.w3.org/2000/svg", "line");
      item.setAttribute("x1", x1.toFixed(2));
      item.setAttribute("y1", y1.toFixed(2));
      item.setAttribute("x2", x2.toFixed(2));
      item.setAttribute("y2", y2.toFixed(2));
      item.setAttribute("class", cls);
      item.setAttribute("stroke-width", width);
      item.setAttribute("fill", "none");
      svg.appendChild(item);
    }}

    function text(x, y, value, cls = "label", anchor = "start") {{
      const item = document.createElementNS("http://www.w3.org/2000/svg", "text");
      item.setAttribute("x", x.toFixed(2));
      item.setAttribute("y", y.toFixed(2));
      item.setAttribute("class", cls);
      item.setAttribute("text-anchor", anchor);
      item.textContent = value;
      svg.appendChild(item);
    }}

    function drawGrid(originX, originY, width, height, step) {{
      for (let x = originX; x <= originX + width; x += step) line(x, originY, x, originY - height, "grid", 0.8);
      for (let y = originY; y >= originY - height; y -= step) line(originX, y, originX + width, y, "grid", 0.8);
      line(originX, originY, originX + width, originY, "axis", 1);
    }}

    function drawElevation() {{
      const ox = 90, oy = 330;
      drawGrid(ox, oy, 1100, 270, 55);
      text(ox, 42, "立面图：倾角调整后空间点整体重算", "title");
      for (const member of data.members) {{
        const sx = member.start_x;
        const ex = member.end_x;
        const sy = ox + sx * scaleX;
        const ey = ox + ex * scaleX;
        const sz = oy - projectedMemberZ(member, "start") * scaleZ;
        const ez = oy - projectedMemberZ(member, "end") * scaleZ;
        line(sy, sz, ey, ez, memberClass(member.category));
      }}
      for (const station of stations) {{
        const x = ox + station * scaleX;
        line(x, oy + 6, x, oy + 18, "axis", 0.8);
      }}
      segmentRanges().slice(0, -1).forEach((range, idx) => {{
        const x = ox + range[1] * scaleX;
        line(x, oy + 24, x, 46, "splice", 2.2);
        text(x + 5, 62, `P${{idx + 1}}/P${{idx + 2}}`, "dim");
      }});
      text(ox, oy + 42, `总长 ${{Math.round(total)}} mm`, "dim");
    }}

    function drawPlan() {{
      const ox = 90, oy = 610;
      drawGrid(ox, oy, 1100, 120, 55);
      text(ox, 455, "平面图：拼接分段与平台外挑", "title");
      for (const member of data.members) {{
        if (member.category === "column" || member.category === "transverse_column_brace" || member.category === "longitudinal_support_brace") continue;
        const sx = ox + member.start_x * scaleX;
        const ex = ox + member.end_x * scaleX;
        const sy = oy - member.start_y * scaleY;
        const ey = oy - member.end_y * scaleY;
        line(sx, sy, ex, ey, memberClass(member.category));
      }}
      segmentRanges().slice(0, -1).forEach((range, idx) => {{
        const x = ox + range[1] * scaleX;
        line(x, oy + 38, x, oy - 90, "splice", 2.2);
        text(x + 5, oy - 96, `分缝${{idx + 1}}`, "dim");
      }});
      text(ox, oy + 62, `平台宽约 ${{Math.round(data.params.equipment_width + data.params.left_cantilever + data.params.right_cantilever)}} mm`, "dim");
    }}

    function render() {{
      svg.replaceChildren();
      document.getElementById("slopeValue").textContent = `${{Number(slopeInput.value).toFixed(1)}}°`;
      document.getElementById("memberCount").textContent = data.members.length;
      document.getElementById("segmentCount").textContent = segmentRanges().length;
      document.getElementById("endElevation").textContent = Math.round(projectedZ(total, startElevation));
      const rows = data.summary.map(row => `<tr><td>${{row.role}}</td><td>${{row.count}}</td><td>${{Math.round(row.total_length)}}</td></tr>`).join("");
      document.getElementById("summaryRows").innerHTML = rows;
      drawElevation();
      drawPlan();
    }}

    slopeInput.addEventListener("input", render);
    segmentsInput.addEventListener("input", render);
    slopeInput.value = String(data.params.slope_deg);
    segmentsInput.value = (data.params.segment_spans || []).join(",");
    render();
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
