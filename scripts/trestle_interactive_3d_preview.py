from __future__ import annotations

import json
import shutil
from pathlib import Path

from trestle_core import build_members, compute_segment_ranges, summarize_members
from trestle_project import load_parameters, output_path


OUT = output_path("trestle_parametric_3d_preview.html")
VENDOR = OUT.parent / "vendor" / "three"
THREE_ROOT = Path("C:/Users/Lenovo/.codex/skills/cad-explorer/scripts/explorer/node_modules/three")


def _copy_three_assets() -> tuple[str, str]:
    VENDOR.mkdir(parents=True, exist_ok=True)
    build_dir = VENDOR / "build"
    controls_dir = VENDOR / "examples" / "jsm" / "controls"
    build_dir.mkdir(parents=True, exist_ok=True)
    controls_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(THREE_ROOT / "build" / "three.module.min.js", build_dir / "three.module.min.js")
    shutil.copyfile(THREE_ROOT / "examples" / "jsm" / "controls" / "OrbitControls.js", controls_dir / "OrbitControls.js")
    package = {
        "imports": {
            "three": "./build/three.module.min.js",
            "three/addons/": "./examples/jsm/",
        }
    }
    (VENDOR / "package.json").write_text(json.dumps(package, indent=2), encoding="utf-8")
    return "./vendor/three/build/three.module.min.js", "./vendor/three/examples/jsm/controls/OrbitControls.js"


def _payload() -> dict[str, object]:
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
    three_url, controls_url = _copy_three_assets()
    payload_data = _payload()
    default_slope = float(payload_data["params"]["slope_deg"])
    default_segments = ",".join(str(int(value) if float(value).is_integer() else value) for value in payload_data["params"]["segment_spans"])
    initial_api_url = "http://127.0.0.1:8888/api/rebuild-step"
    payload = json.dumps(payload_data, ensure_ascii=False)
    OUT.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>中建八局栈桥三维参数化预览</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1f2933;
      --muted: #607086;
      --line: #d7dee8;
      --panel: #ffffff;
      --bg: #eef3f8;
      --main: #1f6fd1;
      --secondary: #209b68;
      --brace: #d64531;
      --truss: #7552cc;
      --column: #707a86;
      --splice: #e1a500;
      --plate: #f59f00;
      --load: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--bg);
      overflow: hidden;
    }}
    header {{
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    header strong {{ font-size: 17px; }}
    header span {{ color: var(--muted); font-size: 13px; }}
    main {{
      height: calc(100vh - 56px);
      display: grid;
      grid-template-columns: 336px 1fr;
    }}
    aside {{
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 18px;
      overflow: auto;
    }}
    #stage {{
      position: relative;
      height: 100%;
      min-width: 0;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 100%;
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
    input[type="range"], input[type="text"], input[type="number"] {{ width: 100%; }}
    input[type="text"], input[type="number"] {{
      border: 1px solid #c9d2df;
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 13px;
      color: var(--ink);
    }}
    .toggle {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 9px 10px;
      margin-bottom: 10px;
      color: var(--ink);
      font-size: 13px;
    }}
    .toggle input {{ width: 18px; height: 18px; }}
    .download-link {{
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      border: 1px solid var(--main);
      border-radius: 7px;
      color: var(--main);
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      margin-top: 10px;
    }}
    .download-link:hover {{
      background: #eef6ff;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 16px 0;
    }}
    .analysis-panel {{
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      padding: 14px 0 12px;
      margin: 14px 0;
    }}
    .section-title {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .section-title strong {{
      font-size: 15px;
    }}
    .section-title span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .input-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .input-grid .field {{
      margin-bottom: 0;
    }}
    .analysis-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 10px 0;
    }}
    .analysis-stat {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 9px;
      min-height: 58px;
      background: #fbfcfe;
    }}
    .analysis-stat small {{
      color: var(--muted);
      display: block;
      margin-bottom: 5px;
    }}
    .analysis-stat b {{
      font-size: 15px;
    }}
    .analysis-note {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      margin-top: 8px;
    }}
    .support-table {{
      max-height: 150px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 7px;
      margin-top: 10px;
    }}
    .support-table table {{
      margin-top: 0;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      min-height: 58px;
    }}
    .stat small {{ color: var(--muted); display: block; margin-bottom: 6px; }}
    .stat b {{ font-size: 16px; }}
    .legend {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 12px;
      margin-top: 16px;
      font-size: 13px;
    }}
    .swatch {{
      display: inline-block;
      width: 18px;
      height: 3px;
      vertical-align: middle;
      margin-right: 6px;
    }}
    .note {{
      margin-top: 16px;
      padding: 10px;
      border-left: 3px solid var(--splice);
      background: #fff8db;
      color: #5b4a00;
      font-size: 13px;
      line-height: 1.55;
    }}
    .hud {{
      position: absolute;
      left: 16px;
      bottom: 16px;
      background: rgba(255,255,255,.92);
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 9px 11px;
      color: var(--muted);
      font-size: 12px;
      pointer-events: none;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      font-size: 12px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 6px 4px;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    @media (max-width: 760px) {{
      body {{
        overflow: auto;
      }}
      header {{
        height: auto;
        min-height: 56px;
        align-items: flex-start;
        flex-direction: column;
        gap: 4px;
        padding: 10px 14px;
      }}
      header strong {{
        font-size: 15px;
      }}
      header span {{
        font-size: 12px;
        line-height: 1.4;
      }}
      main {{
        height: auto;
        min-height: calc(100vh - 76px);
        grid-template-columns: 1fr;
        grid-template-rows: minmax(420px, 62vh) auto;
        grid-template-areas:
          "stage"
          "controls";
      }}
      aside {{
        grid-area: controls;
        border-right: 0;
        border-top: 1px solid var(--line);
        padding: 12px;
        overflow: visible;
      }}
      #stage {{
        grid-area: stage;
        height: 62vh;
        min-height: 420px;
      }}
      .field {{
        margin-bottom: 12px;
      }}
      .stat-grid {{
        grid-template-columns: repeat(4, minmax(68px, 1fr));
        gap: 6px;
      }}
      .analysis-grid {{
        grid-template-columns: repeat(2, minmax(120px, 1fr));
      }}
      .stat {{
        min-height: 52px;
        padding: 8px;
      }}
      .stat b {{
        font-size: 14px;
      }}
      .legend {{
        grid-template-columns: 1fr 1fr;
        gap: 7px;
      }}
      .note {{
        font-size: 12px;
      }}
      .hud {{
        left: 10px;
        right: 10px;
        bottom: 10px;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <strong>工业皮带机栈桥三维参数化预览</strong>
    <span>拖拽旋转 | 滚轮缩放 | 同一杆件基线驱动</span>
  </header>
  <main autocomplete="off">
    <aside>
      <div class="field">
        <label for="slope"><span>平台倾角</span><b id="slopeValue">{default_slope:.1f}°</b></label>
        <input id="slope" type="range" min="-2" max="8" step="0.1" value="{default_slope:g}" autocomplete="off">
      </div>
      <div class="field">
        <label for="segments"><span>拼接分段长度</span><b>mm</b></label>
        <input id="segments" type="text" value="{default_segments}" autocomplete="off">
      </div>
      <label class="toggle"><span>显示拼接标记</span><input id="showSplice" type="checkbox" checked autocomplete="off"></label>
      <label class="toggle"><span>显示概念拼接板</span><input id="showPlates" type="checkbox" autocomplete="off"></label>
      <div class="stat-grid">
        <div class="stat"><small>构件数</small><b id="memberCount">-</b></div>
        <div class="stat"><small>拼接段</small><b id="segmentCount">-</b></div>
        <div class="stat"><small>末端标高</small><b id="endElevation">-</b></div>
        <div class="stat"><small>模型总长</small><b id="totalLength">-</b></div>
      </div>
      <section class="analysis-panel" aria-label="结构受力分析">
        <div class="section-title">
          <strong>结构受力分析</strong>
          <span>概念级均布竖向荷载</span>
        </div>
        <div class="input-grid">
          <div class="field">
            <label for="areaLoad"><span>顶部面荷载</span><b>kN/m²</b></label>
            <input id="areaLoad" type="number" min="0" step="0.1" value="3.5" autocomplete="off">
          </div>
          <div class="field">
            <label for="equipmentLoad"><span>设备线荷载</span><b>kN/m</b></label>
            <input id="equipmentLoad" type="number" min="0" step="0.1" value="2.0" autocomplete="off">
          </div>
          <div class="field">
            <label for="selfWeightLoad"><span>结构自重线荷载</span><b>kN/m</b></label>
            <input id="selfWeightLoad" type="number" min="0" step="0.1" value="1.2" autocomplete="off">
          </div>
          <div class="field">
            <label for="loadFactor"><span>组合系数</span><b>×</b></label>
            <input id="loadFactor" type="number" min="0.1" step="0.05" value="1.0" autocomplete="off">
          </div>
          <div class="field">
            <label for="elasticModulus"><span>弹性模量 E</span><b>GPa</b></label>
            <input id="elasticModulus" type="number" min="1" step="1" value="206" autocomplete="off">
          </div>
          <div class="field">
            <label for="effectiveInertia"><span>等效惯性矩 I</span><b>m⁴</b></label>
            <input id="effectiveInertia" type="number" min="0.00001" step="0.001" value="0.06" autocomplete="off">
          </div>
          <div class="field">
            <label for="deformScale"><span>变形放大倍数</span><b id="deformScaleValue">40×</b></label>
            <input id="deformScale" type="range" min="0" max="200" step="5" value="40" autocomplete="off">
          </div>
        </div>
        <label class="toggle"><span>显示顶部荷载箭头</span><input id="showLoads" type="checkbox" checked autocomplete="off"></label>
        <label class="toggle"><span>荷载驱动变形</span><input id="showDeformation" type="checkbox" checked autocomplete="off"></label>
        <div class="analysis-grid">
          <div class="analysis-stat"><small>平均线荷载</small><b id="avgLineLoad">-</b></div>
          <div class="analysis-stat"><small>总竖向荷载</small><b id="totalVerticalLoad">-</b></div>
          <div class="analysis-stat"><small>平均支座反力</small><b id="avgSupportReaction">-</b></div>
          <div class="analysis-stat"><small>控制跨弯矩</small><b id="maxSpanMoment">-</b></div>
          <div class="analysis-stat"><small>控制跨剪力</small><b id="maxSpanShear">-</b></div>
          <div class="analysis-stat"><small>平均面荷载</small><b id="avgAreaLoad">-</b></div>
          <div class="analysis-stat"><small>最大计算挠度</small><b id="maxDeflection">-</b></div>
          <div class="analysis-stat"><small>显示下挠量</small><b id="shownDeflection">-</b></div>
        </div>
        <div class="support-table">
          <table>
            <thead><tr><th>支座</th><th>里程 m</th><th>反力 kN</th></tr></thead>
            <tbody id="supportRows"></tbody>
          </table>
        </div>
        <div class="analysis-note">采用顶部均布荷载折算为沿栈桥方向的线荷载，并按相邻跨一半分摊到支座；控制跨弯矩/剪力按简支跨估算。模型标注中绿色为支撑点 0 mm，橙色为各跨跨中计算/显示下挠；显示经过放大，用于方案阶段快速判断，未包含真实连续梁刚度、桁架节点、基础沉降、风、地震、动力和规范承载力验算。</div>
      </section>
      <div class="legend">
        <span><i class="swatch" style="background:var(--main)"></i>主梁/横梁</span>
        <span><i class="swatch" style="background:var(--secondary)"></i>次梁/外挑</span>
        <span><i class="swatch" style="background:var(--brace)"></i>支撑</span>
        <span><i class="swatch" style="background:var(--truss)"></i>桁架</span>
        <span><i class="swatch" style="background:var(--column)"></i>柱</span>
        <span><i class="swatch" style="background:var(--splice)"></i>分缝位置</span>
        <span><i class="swatch" style="background:var(--load)"></i>顶部荷载</span>
      </div>
      <div class="note">柱脚和支撑脚固定在 Z=0。倾角变化时，平台/桁架升降，柱段按新柱高重分配，斜撑长度随端点变化。分缝标记不是结构连接板；概念拼接板只用于方案沟通。</div>
      <table>
        <thead><tr><th>类别</th><th>数量</th><th>总长</th></tr></thead>
        <tbody id="summaryRows"></tbody>
      </table>
      <div class="field" style="margin-top:16px;">
        <label><span>STEP 自动同步</span><b id="syncState">等待参数变化</b></label>
        <a class="download-link" href="trestle.step" data-dynamic-step="true">下载当前 STEP</a>
      </div>
    </aside>
    <section id="stage">
      <div class="hud">鼠标左键旋转，右键平移，滚轮缩放</div>
    </section>
  </main>
  <script type="importmap">
    {{ "imports": {{ "three": "{three_url}", "three/addons/": "./vendor/three/examples/jsm/" }} }}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from '{controls_url}';

    let data = {payload};
    const stage = document.getElementById('stage');
    const slopeInput = document.getElementById('slope');
    const segmentsInput = document.getElementById('segments');
    const showSpliceInput = document.getElementById('showSplice');
    const showPlatesInput = document.getElementById('showPlates');
    const areaLoadInput = document.getElementById('areaLoad');
    const equipmentLoadInput = document.getElementById('equipmentLoad');
    const selfWeightLoadInput = document.getElementById('selfWeightLoad');
    const loadFactorInput = document.getElementById('loadFactor');
    const elasticModulusInput = document.getElementById('elasticModulus');
    const effectiveInertiaInput = document.getElementById('effectiveInertia');
    const deformScaleInput = document.getElementById('deformScale');
    const showLoadsInput = document.getElementById('showLoads');
    const showDeformationInput = document.getElementById('showDeformation');
    const syncState = document.getElementById('syncState');
    const total = data.params.support_stations[data.params.support_stations.length - 1];
    const startElevation = data.params.start_elevation;
    let baselineSlope = Number(data.params.slope_deg);
    const worldScale = 0.001;
    const apiUrl = window.location.protocol.startsWith('http')
      ? new URL('/api/rebuild-step', window.location.origin).toString()
      : '{initial_api_url}';
    let syncTimer = null;
    let syncBusy = false;
    let latestStepUrl = 'trestle.step';
    let latestStepSynced = false;
    let lastPayload = '';
    const initialPayloadKey = JSON.stringify({{
      slope_deg: Number(data.params.slope_deg),
      segment_spans: data.params.segment_spans,
    }});

    const colors = {{
      main: 0x1f6fd1,
      secondary: 0x209b68,
      brace: 0xd64531,
      truss: 0x7552cc,
      column: 0x707a86,
      splice: 0xe1a500,
      plate: 0xf59f00,
      load: 0xb45309,
      floor: 0xf2f5f8,
      grid: 0xc8d1dd,
    }};

    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0xeef3f8, 1);
    stage.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xeef3f8, 140, 280);
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
    camera.position.set(70, -95, 58);
    camera.up.set(0, 0, 1);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(58, 0, 9);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa7b3, 1.2));
    const sun = new THREE.DirectionalLight(0xffffff, 1.8);
    sun.position.set(45, -70, 85);
    scene.add(sun);

    const grid = new THREE.GridHelper(140, 28, colors.grid, 0xdde5ee);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(total * worldScale / 2, 0, -0.02);
    scene.add(grid);

    const modelGroup = new THREE.Group();
    scene.add(modelGroup);
    const spliceGroup = new THREE.Group();
    scene.add(spliceGroup);
    const plateGroup = new THREE.Group();
    scene.add(plateGroup);
    const loadGroup = new THREE.Group();
    scene.add(loadGroup);
    const labelGroup = new THREE.Group();
    scene.add(labelGroup);

    const materials = {{
      main: new THREE.MeshStandardMaterial({{ color: colors.main, roughness: 0.58, metalness: 0.16 }}),
      secondary: new THREE.MeshStandardMaterial({{ color: colors.secondary, roughness: 0.62, metalness: 0.12 }}),
      brace: new THREE.MeshStandardMaterial({{ color: colors.brace, roughness: 0.6, metalness: 0.1 }}),
      truss: new THREE.MeshStandardMaterial({{ color: colors.truss, roughness: 0.58, metalness: 0.16 }}),
      column: new THREE.MeshStandardMaterial({{ color: colors.column, roughness: 0.68, metalness: 0.12 }}),
      splice: new THREE.MeshStandardMaterial({{ color: colors.splice, roughness: 0.45, metalness: 0.08 }}),
      plate: new THREE.MeshStandardMaterial({{ color: colors.plate, transparent: true, opacity: 0.42, roughness: 0.5, side: THREE.DoubleSide }}),
      load: new THREE.MeshStandardMaterial({{ color: colors.load, roughness: 0.5, metalness: 0.05 }}),
    }};

    const sectionSize = {{
      'HM-220x220': [0.22, 0.22],
      'HN-180x180': [0.18, 0.18],
      'HN-120x120': [0.12, 0.12],
      'HM-240x240': [0.24, 0.24],
      'L90x90': [0.09, 0.09],
    }};

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
      if (ranges.length === 0 || ranges[ranges.length - 1][1] < total - 1e-6) ranges.push([cursor, total]);
      return ranges;
    }}

    function deckZAt(x) {{
      const slope = Number(slopeInput.value) * Math.PI / 180;
      return startElevation + Math.tan(slope) * x;
    }}

    function numericInput(input, fallback = 0) {{
      const value = Number(input.value);
      return Number.isFinite(value) ? value : fallback;
    }}

    function formatNumber(value, digits = 1) {{
      if (!Number.isFinite(value)) return '-';
      return value.toLocaleString('zh-CN', {{
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      }});
    }}

    function structuralLoadSummary() {{
      const deckWidth = Number(data.params.support_width) / 1000;
      const modelLength = total / 1000;
      const areaLoad = Math.max(0, numericInput(areaLoadInput));
      const equipmentLineLoad = Math.max(0, numericInput(equipmentLoadInput));
      const selfWeightLineLoad = Math.max(0, numericInput(selfWeightLoadInput));
      const factor = Math.max(0, numericInput(loadFactorInput, 1));
      const elasticModulusGpa = Math.max(1, numericInput(elasticModulusInput, 206));
      const effectiveInertia = Math.max(1e-6, numericInput(effectiveInertiaInput, 0.06));
      const elasticModulusKpa = elasticModulusGpa * 1000000;
      const areaLineLoad = areaLoad * deckWidth;
      const lineLoad = (areaLineLoad + equipmentLineLoad + selfWeightLineLoad) * factor;
      const totalLoad = lineLoad * modelLength;
      const stations = data.params.support_stations.map(value => Number(value) / 1000);
      const spans = [];
      for (let index = 0; index < stations.length - 1; index += 1) {{
        const span = Math.max(0, stations[index + 1] - stations[index]);
        if (span > 1e-6) {{
          const maxDeflection = 5 * lineLoad * span ** 4 / (384 * elasticModulusKpa * effectiveInertia);
          spans.push({{ index, start: stations[index], end: stations[index + 1], span, maxDeflection }});
        }}
      }}
      const reactions = stations.map((station, index) => {{
        const left = index > 0 ? Math.max(0, station - stations[index - 1]) : 0;
        const right = index < stations.length - 1 ? Math.max(0, stations[index + 1] - station) : 0;
        return {{
          index: index + 1,
          station,
          reaction: lineLoad * (left + right) / 2,
        }};
      }});
      const controllingSpan = spans.reduce((best, span) => span.span > best.span ? span : best, {{ index: 0, start: 0, end: 0, span: 0 }});
      const maxMoment = lineLoad * controllingSpan.span * controllingSpan.span / 8;
      const maxShear = lineLoad * controllingSpan.span / 2;
      const maxDeflection = spans.reduce((best, span) => Math.max(best, span.maxDeflection), 0);
      return {{
        deckWidth,
        modelLength,
        areaLoad,
        areaLineLoad,
        lineLoad,
        totalLoad,
        elasticModulusGpa,
        effectiveInertia,
        stations,
        avgAreaLoad: deckWidth > 0 ? lineLoad / deckWidth : 0,
        avgSupportReaction: reactions.length ? totalLoad / reactions.length : 0,
        spans,
        reactions,
        controllingSpan,
        maxMoment,
        maxShear,
        maxDeflection,
      }};
    }}

    function spanDeflectionAt(span, stationM, loadSummary) {{
      if (!span || span.span <= 1e-6) return 0;
      const localX = Math.min(Math.max(stationM - span.start, 0), span.span);
      const elasticModulusKpa = loadSummary.elasticModulusGpa * 1000000;
      const denominator = 24 * elasticModulusKpa * loadSummary.effectiveInertia;
      return loadSummary.lineLoad * localX * (span.span ** 3 - 2 * span.span * localX ** 2 + localX ** 3) / denominator;
    }}

    function supportSpanAt(stationM, loadSummary) {{
      const stations = loadSummary?.stations || [];
      if (stations.length < 2) return null;
      for (let index = 0; index < stations.length - 1; index += 1) {{
        const start = stations[index];
        const end = stations[index + 1];
        if (stationM >= start - 1e-9 && stationM <= end + 1e-9) {{
          return {{ index, start, end, span: end - start }};
        }}
      }}
      return null;
    }}

    function actualDeflectionAtStation(xMm, loadSummary) {{
      const stationM = xMm / 1000;
      const span = supportSpanAt(stationM, loadSummary);
      if (!span) return 0;
      return spanDeflectionAt(span, stationM, loadSummary) * 1000;
    }}

    function displayBoostAtStation(xMm, loadSummary) {{
      const stationM = xMm / 1000;
      const span = supportSpanAt(stationM, loadSummary);
      if (!span || span.span <= 1e-6) return 0;
      const controllingSpan = Math.max(loadSummary?.controllingSpan?.span || span.span, 1e-6);
      const localT = Math.min(Math.max((stationM - span.start) / span.span, 0), 1);
      const spanShape = Math.sin(Math.PI * localT);
      if (spanShape <= 1e-9) return 0;
      const maxShown = loadSummary.maxDeflection * 1000 * numericInput(deformScaleInput, 0);
      return maxShown * 0.06 * Math.sqrt(Math.min(1, span.span / controllingSpan)) * spanShape;
    }}

    function deflectionAtStation(xMm, loadSummary) {{
      if (!showDeformationInput.checked || numericInput(deformScaleInput, 0) <= 0) return 0;
      const actualShown = actualDeflectionAtStation(xMm, loadSummary) * numericInput(deformScaleInput, 0);
      if (actualShown <= 0) return 0;
      return Math.max(actualShown, displayBoostAtStation(xMm, loadSummary));
    }}

    function makeTextSprite(text, options = {{}}) {{
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const fontSize = options.fontSize || 34;
      context.font = `700 ${{fontSize * ratio}}px "Microsoft YaHei", "Segoe UI", sans-serif`;
      const paddingX = 18 * ratio;
      const paddingY = 10 * ratio;
      const metrics = context.measureText(text);
      canvas.width = Math.ceil(metrics.width + paddingX * 2);
      canvas.height = Math.ceil(fontSize * ratio + paddingY * 2);
      context.font = `700 ${{fontSize * ratio}}px "Microsoft YaHei", "Segoe UI", sans-serif`;
      context.textBaseline = 'middle';
      context.fillStyle = options.background || 'rgba(255, 255, 255, 0.88)';
      context.strokeStyle = options.border || 'rgba(41, 53, 65, 0.25)';
      context.lineWidth = 2 * ratio;
      const radius = 8 * ratio;
      const w = canvas.width;
      const h = canvas.height;
      context.beginPath();
      context.moveTo(radius, 0);
      context.lineTo(w - radius, 0);
      context.quadraticCurveTo(w, 0, w, radius);
      context.lineTo(w, h - radius);
      context.quadraticCurveTo(w, h, w - radius, h);
      context.lineTo(radius, h);
      context.quadraticCurveTo(0, h, 0, h - radius);
      context.lineTo(0, radius);
      context.quadraticCurveTo(0, 0, radius, 0);
      context.closePath();
      context.fill();
      context.stroke();
      context.fillStyle = options.color || '#1f2933';
      context.fillText(text, paddingX, h / 2);
      const texture = new THREE.CanvasTexture(canvas);
      texture.colorSpace = THREE.SRGBColorSpace;
      const material = new THREE.SpriteMaterial({{ map: texture, transparent: true, depthTest: false }});
      const sprite = new THREE.Sprite(material);
      const width = (canvas.width / ratio) * 0.018;
      const height = (canvas.height / ratio) * 0.018;
      sprite.scale.set(width, height, 1);
      sprite.userData = {{ texture }};
      return sprite;
    }}

    function makeLabelAnchor(xMm, yMm, zMm, text, options = {{}}) {{
      const group = new THREE.Group();
      const x = xMm * worldScale;
      const y = yMm * worldScale;
      const z = zMm * worldScale;
      const verticalOffset = options.offset || 1.9;
      const color = options.colorValue || 0x1f8f5f;
      const marker = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 12), new THREE.MeshStandardMaterial({{ color, roughness: 0.45 }}));
      marker.position.set(x, y, z);
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x, y, z), new THREE.Vector3(x, y, z + verticalOffset)]),
        new THREE.LineBasicMaterial({{ color }})
      );
      const sprite = makeTextSprite(text, options);
      sprite.position.set(x, y, z + verticalOffset + 0.45);
      group.add(marker);
      group.add(line);
      group.add(sprite);
      return group;
    }}

    function rebuildDeformationLabels(loadSummary) {{
      clearGroup(labelGroup, true);
      if (!showDeformationInput.checked) return;
      const labelY = -data.params.support_width * 0.5 - 760;
      for (const reaction of loadSummary.reactions) {{
        const xMm = reaction.station * 1000;
        const zMm = deckZAt(xMm) - deflectionAtStation(xMm, loadSummary) + 1350;
        labelGroup.add(makeLabelAnchor(
          xMm,
          labelY,
          zMm,
          `Z${{reaction.index}} 0 mm`,
          {{ color: '#0f6b46', background: 'rgba(232, 247, 239, 0.92)', border: 'rgba(15, 107, 70, 0.34)', colorValue: 0x15804f, fontSize: 30, offset: 1.35 }}
        ));
      }}
      for (const span of loadSummary.spans) {{
        const xMm = (span.start + span.span / 2) * 1000;
        const actualMm = actualDeflectionAtStation(xMm, loadSummary);
        const shownMm = deflectionAtStation(xMm, loadSummary);
        const zMm = deckZAt(xMm) - shownMm + 1850;
        labelGroup.add(makeLabelAnchor(
          xMm,
          -labelY,
          zMm,
          `Z${{span.index + 1}}-Z${{span.index + 2}} 算${{formatNumber(actualMm, 3)}} / 显${{formatNumber(shownMm, 0)}} mm`,
          {{ color: '#8a3b04', background: 'rgba(255, 244, 226, 0.94)', border: 'rgba(180, 83, 9, 0.36)', colorValue: 0xb45309, fontSize: 28, offset: 1.55 }}
        ));
      }}
    }}

    function makeLoadArrow(station, y, deckZ, maxArrowHeight) {{
      const shaftHeight = maxArrowHeight * 0.72;
      const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, shaftHeight, 10), materials.load);
      shaft.rotation.x = -Math.PI / 2;
      shaft.position.set(station, y, deckZ + shaftHeight / 2 + 0.55);
      const head = new THREE.Mesh(new THREE.ConeGeometry(0.16, maxArrowHeight * 0.28, 16), materials.load);
      head.rotation.x = -Math.PI / 2;
      head.position.set(station, y, deckZ + 0.24);
      const group = new THREE.Group();
      group.add(shaft);
      group.add(head);
      return group;
    }}

    function rebuildLoadArrows(loadSummary) {{
      clearGroup(loadGroup);
      const arrowCount = Math.max(6, Math.min(18, Math.round(total / 8000)));
      const lineLoadScale = Math.min(1.8, Math.max(0.55, loadSummary.lineLoad / 28));
      const arrowHeight = 2.2 * lineLoadScale;
      const halfWidth = data.params.support_width * worldScale / 2;
      const yPositions = [-halfWidth * 0.52, halfWidth * 0.52];
      for (let index = 0; index < arrowCount; index += 1) {{
        const x = total * (index + 0.5) / arrowCount;
        const deckZ = (deckZAt(x) - deflectionAtStation(x, loadSummary) + 900) * worldScale;
        const station = x * worldScale;
        for (const y of yPositions) loadGroup.add(makeLoadArrow(station, y, deckZ, arrowHeight));
      }}
      loadGroup.visible = showLoadsInput.checked;
    }}

    function updateLoadPanel(loadSummary) {{
      document.getElementById('avgLineLoad').textContent = `${{formatNumber(loadSummary.lineLoad)}} kN/m`;
      document.getElementById('totalVerticalLoad').textContent = `${{formatNumber(loadSummary.totalLoad, 0)}} kN`;
      document.getElementById('avgSupportReaction').textContent = `${{formatNumber(loadSummary.avgSupportReaction)}} kN`;
      document.getElementById('maxSpanMoment').textContent = `${{formatNumber(loadSummary.maxMoment, 0)}} kN·m`;
      document.getElementById('maxSpanShear').textContent = `${{formatNumber(loadSummary.maxShear)}} kN`;
      document.getElementById('avgAreaLoad').textContent = `${{formatNumber(loadSummary.avgAreaLoad)}} kN/m²`;
      document.getElementById('maxDeflection').textContent = `${{formatNumber(loadSummary.maxDeflection * 1000, 1)}} mm`;
      const visualDeflection = showDeformationInput.checked ? loadSummary.maxDeflection * 1000 * numericInput(deformScaleInput, 0) : 0;
      document.getElementById('shownDeflection').textContent = `${{formatNumber(visualDeflection, 0)}} mm`;
      document.getElementById('deformScaleValue').textContent = `${{Math.round(numericInput(deformScaleInput, 0))}}×`;
      document.getElementById('supportRows').innerHTML = loadSummary.reactions
        .map(row => `<tr><td>Z${{row.index}}</td><td>${{formatNumber(row.station, 2)}}</td><td>${{formatNumber(row.reaction)}}</td></tr>`)
        .join('');
    }}

    function storedDeckZAt(x) {{
      return startElevation + Math.tan(baselineSlope * Math.PI / 180) * x;
    }}

    function projectedZ(row, prefix, loadSummary) {{
      const x = Number(row[`${{prefix}}_x`]);
      const storedZ = Number(row[`${{prefix}}_z`]);
      if (Math.abs(storedZ) < 1e-6) return 0;
      const deflection = loadSummary ? deflectionAtStation(x, loadSummary) : 0;
      if (row.category === 'column') return Math.max(0, deckZAt(x) * (storedZ / storedDeckZAt(x)) - deflection * (storedZ / storedDeckZAt(x)));
      return deckZAt(x) + (storedZ - storedDeckZAt(x)) - deflection;
    }}

    function projectedPoint(row, prefix, loadSummary) {{
      return {{
        x: Number(row[`${{prefix}}_x`]),
        y: Number(row[`${{prefix}}_y`]),
        z: projectedZ(row, prefix, loadSummary),
      }};
    }}

    function toWorld(row, prefix, loadSummary) {{
      const point = projectedPoint(row, prefix, loadSummary);
      return new THREE.Vector3(point.x * worldScale, point.y * worldScale, point.z * worldScale);
    }}

    function dynamicSummary(loadSummary) {{
      const rowsByCategory = new Map(data.summary.map(row => [row.category, {{ ...row, count: 0, total_length: 0 }}]));
      for (const row of data.members) {{
        const a = projectedPoint(row, 'start', loadSummary);
        const b = projectedPoint(row, 'end', loadSummary);
        const length = Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
        const item = rowsByCategory.get(row.category) || {{ role: row.category, count: 0, total_length: 0 }};
        item.count += 1;
        item.total_length += length;
        rowsByCategory.set(row.category, item);
      }}
      return Array.from(rowsByCategory.values()).sort((a, b) => String(a.role).localeCompare(String(b.role), 'zh-CN'));
    }}

    function materialFor(category) {{
      if (category.includes('truss')) return materials.truss;
      if (category.includes('brace')) return materials.brace;
      if (category === 'column') return materials.column;
      if (category.includes('secondary') || category.includes('cantilever')) return materials.secondary;
      return materials.main;
    }}

    function shouldCurveMember(row) {{
      return ['deck_main_beam', 'deck_secondary_beam', 'cantilever_edge_beam', 'truss_upper_chord', 'truss_lower_chord'].includes(row.category);
    }}

    function interpolatedPoint(row, t, loadSummary) {{
      const start = projectedPoint(row, 'start', loadSummary);
      const end = projectedPoint(row, 'end', loadSummary);
      const x = start.x + (end.x - start.x) * t;
      const y = start.y + (end.y - start.y) * t;
      const storedZ = Number(row.start_z) + (Number(row.end_z) - Number(row.start_z)) * t;
      const storedDeck = storedDeckZAt(x);
      const z = deckZAt(x) + (storedZ - storedDeck) - (loadSummary ? deflectionAtStation(x, loadSummary) : 0);
      return new THREE.Vector3(x * worldScale, y * worldScale, z * worldScale);
    }}

    function makeStraightMember(row, loadSummary, start = toWorld(row, 'start', loadSummary), end = toWorld(row, 'end', loadSummary)) {{
      const direction = new THREE.Vector3().subVectors(end, start);
      const length = direction.length();
      const [w, h] = sectionSize[row.section] || [0.12, 0.12];
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, length), materialFor(row.category));
      const center = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
      mesh.position.copy(center);
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), direction.normalize());
      mesh.userData = {{ id: row.id, category: row.category }};
      return mesh;
    }}

    function makeMember(row, loadSummary) {{
      const start = toWorld(row, 'start', loadSummary);
      const end = toWorld(row, 'end', loadSummary);
      const spanLength = Math.abs(Number(row.end_x) - Number(row.start_x));
      if (!showDeformationInput.checked || !shouldCurveMember(row)) {{
        return makeStraightMember(row, loadSummary, start, end);
      }}
      const startX = Math.min(Number(row.start_x), Number(row.end_x));
      const endX = Math.max(Number(row.start_x), Number(row.end_x));
      const breakpoints = new Set([0, 1]);
      const addBreakpointAtX = x => {{
        if (spanLength <= 1e-6 || x <= startX + 1e-6 || x >= endX - 1e-6) return;
        const t = (x - Number(row.start_x)) / (Number(row.end_x) - Number(row.start_x));
        if (t > 1e-6 && t < 1 - 1e-6) breakpoints.add(Math.min(Math.max(t, 0), 1));
      }};
      for (const station of loadSummary.stations) {{
        const x = station * 1000;
        addBreakpointAtX(x);
      }}
      for (const span of loadSummary.spans) {{
        addBreakpointAtX((span.start + span.span / 2) * 1000);
      }}
      const pieces = Math.max(3, Math.min(28, Math.ceil(Math.max(spanLength, 1000) / 1400)));
      for (let index = 1; index < pieces; index += 1) {{
        breakpoints.add(index / pieces);
      }}
      const points = Array.from(breakpoints).sort((a, b) => a - b);
      const group = new THREE.Group();
      for (let index = 0; index < points.length - 1; index += 1) {{
        const a = interpolatedPoint(row, points[index], loadSummary);
        const b = interpolatedPoint(row, points[index + 1], loadSummary);
        group.add(makeStraightMember(row, loadSummary, a, b));
      }}
      group.userData = {{ id: row.id, category: row.category, curved: true }};
      return group;
    }}

    function clearGroup(group, disposeMaterials = false) {{
      while (group.children.length) {{
        const child = group.children.pop();
        child.traverse?.(node => {{
          node.geometry?.dispose();
          if (disposeMaterials) {{
            node.material?.map?.dispose();
            node.material?.dispose();
            node.userData?.texture?.dispose?.();
          }}
        }});
        child.geometry?.dispose();
        if (disposeMaterials) child.material?.dispose();
      }}
    }}

    function makeSpliceMarker(x, index, loadSummary) {{
      const height = (deckZAt(x) - deflectionAtStation(x, loadSummary) + 3200) * worldScale;
      const width = (data.params.support_width + 1200) * worldScale;
      const station = x * worldScale;
      const group = new THREE.Group();
      const legGeo = new THREE.BoxGeometry(0.13, 0.12, height);
      const capGeo = new THREE.BoxGeometry(0.13, width + 0.12, 0.12);
      for (const y of [-width / 2, width / 2]) {{
        const leg = new THREE.Mesh(legGeo.clone(), materials.splice);
        leg.position.set(station, y, height / 2);
        group.add(leg);
      }}
      const cap = new THREE.Mesh(capGeo, materials.splice);
      cap.position.set(station, 0, height);
      group.add(cap);
      group.name = `拼接标记 P${{index}}/P${{index + 1}}`;
      return group;
    }}

    function makeConceptPlate(x, index, loadSummary) {{
      const station = x * worldScale;
      const deckZ = (deckZAt(x) - deflectionAtStation(x, loadSummary)) * worldScale;
      const halfWidth = data.params.support_width * worldScale / 2;
      const group = new THREE.Group();
      const plateGeo = new THREE.BoxGeometry(0.18, 1.0, 1.2);
      for (const y of [-halfWidth, halfWidth]) {{
        const plate = new THREE.Mesh(plateGeo.clone(), materials.plate);
        plate.position.set(station, y, deckZ - 0.15);
        group.add(plate);
      }}
      group.name = `概念拼接板 P${{index}}/P${{index + 1}}`;
      return group;
    }}

    function rebuild() {{
      clearGroup(modelGroup);
      clearGroup(spliceGroup);
      clearGroup(plateGroup);
      clearGroup(labelGroup, true);
      const loadSummary = structuralLoadSummary();
      for (const row of data.members) modelGroup.add(makeMember(row, loadSummary));
      const ranges = segmentRanges();
      ranges.slice(0, -1).forEach((range, index) => {{
        spliceGroup.add(makeSpliceMarker(range[1], index + 1, loadSummary));
        plateGroup.add(makeConceptPlate(range[1], index + 1, loadSummary));
      }});
      spliceGroup.visible = showSpliceInput.checked;
      plateGroup.visible = showPlatesInput.checked;
      rebuildLoadArrows(loadSummary);
      rebuildDeformationLabels(loadSummary);
      updateLoadPanel(loadSummary);
      document.getElementById('slopeValue').textContent = `${{Number(slopeInput.value).toFixed(1)}}°`;
      document.getElementById('memberCount').textContent = data.members.length;
      document.getElementById('segmentCount').textContent = ranges.length;
      document.getElementById('endElevation').textContent = Math.round(deckZAt(total));
      document.getElementById('totalLength').textContent = Math.round(total);
      document.getElementById('summaryRows').innerHTML = dynamicSummary(loadSummary)
        .map(row => `<tr><td>${{row.role}}</td><td>${{row.count}}</td><td>${{Math.round(row.total_length)}}</td></tr>`)
        .join('');
    }}

    function currentPayload() {{
      return {{
        params: {{
          ...data.params,
          slope_deg: Number(slopeInput.value),
          segment_spans: parseSegments(),
        }},
      }};
    }}

    async function syncOutputs() {{
      if (syncBusy) return;
      const payload = currentPayload();
      const payloadKey = JSON.stringify({{
        slope_deg: payload.params.slope_deg,
        segment_spans: payload.params.segment_spans,
      }});
      if (payloadKey === lastPayload) return;
      syncBusy = true;
      syncState.textContent = 'STEP 生成中...';
      try {{
        const response = await fetch(apiUrl, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload),
        }});
        const result = await response.json();
        if (!response.ok || !result.ok) {{
          throw new Error(result.error || `HTTP ${{response.status}}`);
        }}
        lastPayload = payloadKey;
        latestStepUrl = result.step_url || latestStepUrl;
        latestStepSynced = true;
        const stamp = new Date().toLocaleTimeString('zh-CN', {{ hour12: false }});
        syncState.textContent = `STEP 已更新 ${{stamp}}`;
        data = {{
          params: result.params,
          members: result.members,
          summary: result.summary,
          segments: result.segments,
        }};
        baselineSlope = Number(result.params.slope_deg);
        rebuild();
        updateDownloadLinks();
      }} catch (error) {{
        syncState.textContent = 'STEP 同步失败';
        console.error(error);
      }} finally {{
        syncBusy = false;
      }}
    }}

    function queueSync() {{
      if (syncTimer) window.clearTimeout(syncTimer);
      syncTimer = window.setTimeout(() => {{
        syncTimer = null;
        syncOutputs();
      }}, 650);
    }}

    function updateDownloadLinks() {{
      const stepLinks = document.querySelectorAll('a[href^="trestle.step"], a[data-dynamic-step="true"]');
      stepLinks.forEach(link => {{
        link.href = latestStepSynced ? latestStepUrl : 'trestle.step';
        link.dataset.dynamicStep = 'true';
      }});
    }}

    function resize() {{
      const rect = stage.getBoundingClientRect();
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / Math.max(rect.height, 1);
      camera.updateProjectionMatrix();
    }}

    function resetControls() {{
      slopeInput.value = String(data.params.slope_deg);
      slopeInput.setAttribute('value', String(data.params.slope_deg));
      segmentsInput.value = (data.params.segment_spans || []).join(',');
      segmentsInput.setAttribute('value', (data.params.segment_spans || []).join(','));
      showSpliceInput.checked = true;
      showPlatesInput.checked = false;
    }}

    resetControls();
    slopeInput.addEventListener('input', () => {{
      latestStepSynced = false;
      rebuild();
      queueSync();
    }});
    segmentsInput.addEventListener('input', () => {{
      latestStepSynced = false;
      rebuild();
      queueSync();
    }});
    showSpliceInput.addEventListener('change', rebuild);
    showPlatesInput.addEventListener('change', rebuild);
    showLoadsInput.addEventListener('change', rebuild);
    showDeformationInput.addEventListener('change', rebuild);
    for (const input of [areaLoadInput, equipmentLoadInput, selfWeightLoadInput, loadFactorInput, elasticModulusInput, effectiveInertiaInput, deformScaleInput]) {{
      input.addEventListener('input', rebuild);
    }}
    window.addEventListener('resize', resize);
    window.addEventListener('pageshow', () => {{
      resetControls();
      rebuild();
      updateDownloadLinks();
    }});
    resize();
    rebuild();
    updateDownloadLinks();
    lastPayload = initialPayloadKey;
    queueSync();

    function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      labelGroup.traverse(node => {{
        if (node.isSprite) node.quaternion.copy(camera.quaternion);
      }});
      renderer.render(scene, camera);
    }}
    animate();
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
