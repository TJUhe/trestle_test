export const LAYER_TABLE = {
  deck_main_beam: { cad_layer: "ZJ8_DECK_MAIN", aci: 4, section: "HM-220x220", role: "平台主梁" },
  deck_cross_beam: { cad_layer: "ZJ8_DECK_CROSS", aci: 4, section: "HN-180x180", role: "横向梁" },
  deck_secondary_beam: { cad_layer: "ZJ8_DECK_SECONDARY", aci: 3, section: "HN-120x120", role: "平台次梁" },
  cantilever_edge_beam: { cad_layer: "ZJ8_CANTILEVER_EDGE", aci: 3, section: "HN-120x120", role: "外挑边梁" },
  platform_brace: { cad_layer: "ZJ8_PLATFORM_BRACE", aci: 1, section: "L90x90", role: "平台平面支撑" },
  column: { cad_layer: "ZJ8_COLUMN", aci: 8, section: "HM-240x240", role: "柱子" },
  transverse_column_brace: { cad_layer: "ZJ8_TRANSVERSE_BRACE", aci: 1, section: "L90x90", role: "横向柱间支撑" },
  longitudinal_support_brace: { cad_layer: "ZJ8_LONGITUDINAL_BRACE", aci: 1, section: "L90x90", role: "固定支架纵向支撑" },
  truss_upper_chord: { cad_layer: "ZJ8_TRUSS_UPPER", aci: 5, section: "HN-180x180", role: "桁架上弦" },
  truss_lower_chord: { cad_layer: "ZJ8_TRUSS_LOWER", aci: 5, section: "HN-180x180", role: "桁架下弦" },
  truss_vertical: { cad_layer: "ZJ8_TRUSS_VERTICAL", aci: 5, section: "L90x90", role: "桁架竖腹杆" },
  truss_diagonal: { cad_layer: "ZJ8_TRUSS_DIAGONAL", aci: 5, section: "L90x90", role: "桁架斜腹杆" },
};

export const SECTION_SIZES = {
  "HM-220x220": [220, 220],
  "HN-180x180": [180, 180],
  "HN-120x120": [120, 120],
  "HM-240x240": [240, 240],
  "L90x90": [90, 90],
};

const DEFAULT_PARAMS = {
  support_spans: [0, 12000, 12000, 12000, 3000, 20520, 3000, 12000, 3000, 39000, 3000],
  support_width: 5750,
  start_elevation: 17000,
  slope_deg: 0,
  equipment_width: 2150,
  y_origin: 0,
  left_cantilever: 1125,
  right_cantilever: 1625,
  start_cantilever_length: 1400,
  end_cantilever_length: 0,
  platform_segment_limit: 3000,
  column_segment_limit: 5000,
  fixed_support_span_range: [2000, 6000],
  truss_span_range: [13000, 40000],
  truss_segment_limit: 2000,
  truss_depth: 1800,
  platform_scheme: "double-side-cantilever",
  brace_scheme: "alternating-x",
  truss_scheme: "warren-with-verticals",
  segment_spans: [39000, 38520, 42000],
};

export function normalizeParams(raw = {}) {
  const source = raw && typeof raw === "object" && raw.params ? raw.params : raw;
  const params = { ...DEFAULT_PARAMS, ...(source || {}) };
  params.support_spans = toNumberList(params.support_spans, DEFAULT_PARAMS.support_spans);
  params.segment_spans = toNumberList(params.segment_spans, DEFAULT_PARAMS.segment_spans);
  params.fixed_support_span_range = toRange(params.fixed_support_span_range, DEFAULT_PARAMS.fixed_support_span_range);
  params.truss_span_range = toRange(params.truss_span_range, DEFAULT_PARAMS.truss_span_range);
  for (const key of [
    "support_width",
    "start_elevation",
    "slope_deg",
    "equipment_width",
    "y_origin",
    "left_cantilever",
    "right_cantilever",
    "start_cantilever_length",
    "end_cantilever_length",
    "platform_segment_limit",
    "column_segment_limit",
    "truss_segment_limit",
    "truss_depth",
  ]) {
    params[key] = finiteNumber(params[key], DEFAULT_PARAMS[key]);
  }
  params.support_stations = supportStations(params.support_spans);
  return params;
}

export function buildPayload(params) {
  const members = buildMembers(params);
  return {
    params: { ...params, support_stations: supportStations(params.support_spans) },
    members: members.map(memberRow),
    summary: summarizeMembers(members),
    segments: computeSegmentRanges(params),
  };
}

export function buildMembers(params) {
  const p = normalizeParams(params);
  const stations = supportStations(p.support_spans);
  const segmentRanges = computeSegmentRanges(p);
  const members = [];
  const counter = new Map();

  const pt = (station, y, zOffset = 0) => [
    station,
    p.y_origin + y,
    p.start_elevation + Math.tan((p.slope_deg * Math.PI) / 180) * station + zOffset,
  ];

  const segmentForStation = (station) => {
    for (let index = 0; index < segmentRanges.length; index += 1) {
      const [start, end] = segmentRanges[index];
      if (start - 1e-6 <= station && station <= end + 1e-6) return `P${index + 1}_${Math.trunc(start)}_${Math.trunc(end)}`;
    }
    return "P1";
  };

  const add = (category, start, end, segment, scheme = "") => {
    if (distance(start, end) <= 1e-6) return;
    const info = LAYER_TABLE[category];
    const next = (counter.get(category) || 0) + 1;
    counter.set(category, next);
    members.push({
      id: `${category}_${String(next).padStart(4, "0")}`,
      category,
      start,
      end,
      section: info.section,
      cad_layer: info.cad_layer,
      aci: info.aci,
      segment,
      scheme,
    });
  };

  const half = p.support_width / 2;
  const leftEdge = -p.equipment_width / 2 - p.left_cantilever;
  const rightEdge = p.equipment_width / 2 + p.right_cantilever;
  const leftMain = -half;
  const rightMain = half;
  const leftInner = -p.equipment_width / 2;
  const rightInner = p.equipment_width / 2;

  stations.forEach((station, index) => {
    const topZ = pt(station, 0)[2];
    for (const y of [leftMain, rightMain]) {
      const levels = equalSubdivisionValues(0, topZ, p.column_segment_limit);
      for (let levelIndex = 0; levelIndex < levels.length - 1; levelIndex += 1) {
        add("column", [station, p.y_origin + y, levels[levelIndex]], [station, p.y_origin + y, levels[levelIndex + 1]], `Z${index + 1}`, p.brace_scheme);
      }
    }
    const supportSegment = `${segmentForStation(station)}:Z${index + 1}`;
    add("deck_cross_beam", pt(station, leftEdge), pt(station, rightEdge), supportSegment, p.platform_scheme);
    add("transverse_column_brace", [station, p.y_origin + leftMain, 0], pt(station, rightMain), supportSegment, p.brace_scheme);
    add("transverse_column_brace", [station, p.y_origin + rightMain, 0], pt(station, leftMain), supportSegment, p.brace_scheme);
  });

  const routeStart = stations[0] - p.start_cantilever_length;
  const routeEnd = stations[stations.length - 1] + p.end_cantilever_length;
  if (p.start_cantilever_length > 0) {
    for (const y of [leftEdge, rightEdge]) add("cantilever_edge_beam", pt(routeStart, y), pt(stations[0], y), "START_CANTILEVER", p.platform_scheme);
  }
  if (p.end_cantilever_length > 0) {
    for (const y of [leftEdge, rightEdge]) add("cantilever_edge_beam", pt(stations[stations.length - 1], y), pt(routeEnd, y), "END_CANTILEVER", p.platform_scheme);
  }

  for (let bayIndex = 0; bayIndex < stations.length - 1; bayIndex += 1) {
    const a = stations[bayIndex];
    const b = stations[bayIndex + 1];
    const span = b - a;
    const segment = `${segmentForStation((a + b) / 2)}:S${bayIndex + 1}_${Math.trunc(a)}_${Math.trunc(b)}`;
    const bayStations = equalSubdivisionValues(a, b, p.platform_segment_limit);

    for (const y of [leftMain, rightMain]) {
      forEachPair(bayStations, (x0, x1) => add("deck_main_beam", pt(x0, y), pt(x1, y), segment, p.platform_scheme));
    }
    for (const x of bayStations.slice(1, -1)) add("deck_cross_beam", pt(x, leftEdge), pt(x, rightEdge), segment, p.platform_scheme);
    for (const y of [leftInner, rightInner]) {
      forEachPair(bayStations, (x0, x1) => add("deck_secondary_beam", pt(x0, y), pt(x1, y), segment, p.platform_scheme));
    }
    for (const y of [leftEdge, rightEdge]) {
      forEachPair(bayStations, (x0, x1) => add("cantilever_edge_beam", pt(x0, y), pt(x1, y), segment, p.platform_scheme));
    }
    forEachPair(bayStations, (x0, x1, index) => {
      if (p.brace_scheme === "single-diagonal" || index % 2 === 0) {
        add("platform_brace", pt(x0, leftMain), pt(x1, rightMain), segment, p.brace_scheme);
      } else {
        add("platform_brace", pt(x0, rightMain), pt(x1, leftMain), segment, p.brace_scheme);
      }
    });

    if (inRange(span, p.fixed_support_span_range)) {
      add("longitudinal_support_brace", [a, p.y_origin + leftMain, 0], pt(b, leftMain), segment, p.brace_scheme);
      add("longitudinal_support_brace", [a, p.y_origin + rightMain, 0], pt(b, rightMain), segment, p.brace_scheme);
    }

    if (inRange(span, p.truss_span_range)) {
      const trussStations = equalSubdivisionValues(a, b, p.truss_segment_limit);
      for (const y of [leftMain, rightMain]) {
        const upper = trussStations.map((x) => pt(x, y));
        const lower = trussStations.map((x) => pt(x, y, -p.truss_depth));
        forEachPair(upper, (u0, u1) => add("truss_upper_chord", u0, u1, segment, p.truss_scheme));
        forEachPair(lower, (l0, l1) => add("truss_lower_chord", l0, l1, segment, p.truss_scheme));
        for (let i = 0; i < upper.length; i += 1) add("truss_vertical", upper[i], lower[i], segment, p.truss_scheme);
        for (let i = 0; i < trussStations.length - 1; i += 1) {
          if (p.truss_scheme === "pratt") {
            add("truss_diagonal", lower[i], upper[i + 1], segment, p.truss_scheme);
          } else if (p.truss_scheme === "x-braced") {
            add("truss_diagonal", lower[i], upper[i + 1], segment, p.truss_scheme);
            add("truss_diagonal", upper[i], lower[i + 1], segment, p.truss_scheme);
          } else if (i % 2 === 0) {
            add("truss_diagonal", lower[i], upper[i + 1], segment, p.truss_scheme);
          } else {
            add("truss_diagonal", upper[i], lower[i + 1], segment, p.truss_scheme);
          }
        }
      }
    }
  }

  return members;
}

export function supportStations(supportSpans) {
  const spans = toNumberList(supportSpans, DEFAULT_PARAMS.support_spans);
  if (!spans.length) return [0];
  const stations = [0];
  const source = Math.abs(spans[0]) < 1e-9 ? spans.slice(1) : spans;
  for (const span of source) stations.push(stations[stations.length - 1] + span);
  return stations;
}

export function computeSegmentRanges(params) {
  const p = normalizeParams(params);
  const stations = supportStations(p.support_spans);
  const total = stations[stations.length - 1] || 0;
  if (!p.segment_spans.length) return [[0, total]];
  const ranges = [];
  let cursor = 0;
  for (const span of p.segment_spans) {
    const end = Math.min(total, cursor + span);
    ranges.push([cursor, end]);
    cursor = end;
    if (cursor >= total - 1e-6) break;
  }
  if (!ranges.length || ranges[ranges.length - 1][1] < total - 1e-6) ranges.push([cursor, total]);
  return ranges;
}

export function summarizeMembers(members) {
  const groups = new Map();
  for (const member of members) {
    const key = `${member.category}|${member.cad_layer}|${member.section}`;
    const info = LAYER_TABLE[member.category];
    const row = groups.get(key) || {
      category: member.category,
      role: info.role,
      cad_layer: member.cad_layer,
      section: member.section,
      count: 0,
      total_length: 0,
    };
    row.count += 1;
    row.total_length += distance(member.start, member.end);
    groups.set(key, row);
  }
  return Array.from(groups.values())
    .sort((a, b) => String(a.category).localeCompare(String(b.category)))
    .map((row) => ({ ...row, total_length: round(row.total_length, 3) }));
}

export function memberRow(member) {
  const info = LAYER_TABLE[member.category];
  return {
    id: member.id,
    category: member.category,
    role: info.role,
    cad_layer: member.cad_layer,
    aci: member.aci,
    section: member.section,
    segment: member.segment,
    scheme: member.scheme,
    start_x: round(member.start[0], 6),
    start_y: round(member.start[1], 6),
    start_z: round(member.start[2], 6),
    end_x: round(member.end[0], 6),
    end_y: round(member.end[1], 6),
    end_z: round(member.end[2], 6),
    length: round(distance(member.start, member.end), 6),
  };
}

function toNumberList(value, fallback = []) {
  if (Array.isArray(value)) return value.map((item) => Number(item)).filter((item) => Number.isFinite(item));
  if (typeof value === "string") {
    return value
      .replace(/[，；;|\n\t、]/g, ",")
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));
  }
  return [...fallback];
}

function toRange(value, fallback) {
  const values = toNumberList(value, fallback);
  return values.length >= 2 ? [values[0], values[1]] : [...fallback];
}

function finiteNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function equalSubdivisionValues(start, end, limit) {
  const length = Math.abs(end - start);
  if (length <= 1e-9) return [start];
  const count = Math.max(1, Math.ceil(length / Math.max(limit, 1)));
  return Array.from({ length: count + 1 }, (_, index) => start + ((end - start) * index) / count);
}

function forEachPair(values, fn) {
  for (let index = 0; index < values.length - 1; index += 1) fn(values[index], values[index + 1], index);
}

function inRange(value, bounds) {
  return bounds[0] <= Math.abs(value) && Math.abs(value) <= bounds[1];
}

function distance(a, b) {
  return Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
}

function round(value, digits) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}
