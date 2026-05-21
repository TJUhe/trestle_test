import { createHash } from "node:crypto";
import { box, exportAssemblySTEP, init, rotate, translate } from "brepjs";
import { buildMembers, buildPayload, computeSegmentRanges, normalizeParams, SECTION_SIZES } from "./trestle-core.mjs";

const COLOR_BY_CATEGORY = {
  deck_main_beam: "#265cae",
  deck_cross_beam: "#265cae",
  deck_secondary_beam: "#1f8c6b",
  cantilever_edge_beam: "#1f8c6b",
  platform_brace: "#e04733",
  column: "#8c8f94",
  transverse_column_brace: "#e04733",
  longitudinal_support_brace: "#e04733",
  truss_upper_chord: "#9e52c7",
  truss_lower_chord: "#9e52c7",
  truss_vertical: "#9e52c7",
  truss_diagonal: "#9e52c7",
  splice_marker: "#ff1f1f",
};

let kernelReady;

export async function buildStepExport(rawParams) {
  await ensureKernel();
  const params = normalizeParams(rawParams);
  const members = buildMembers(params);
  const parts = [
    ...members.map((member) => memberToPart(member)),
    ...spliceMarkerParts(params),
  ];
  const result = withQuietConsole(() => exportAssemblySTEP(parts, { unit: "MM", modelUnit: "MM" }));
  if (!result.ok) throw new Error(formatBrepError(result.error));
  const stepText = await result.value.text();
  const payload = buildPayload(params);
  return {
    key: stepKey(params),
    filename: stepFilename(params),
    contentType: "model/step",
    stepText,
    params: payload.params,
    members: payload.members,
    summary: payload.summary,
    segments: payload.segments,
  };
}

export function stepKey(params) {
  return createHash("sha256").update(stableStringify(normalizeParams(params))).digest("hex").slice(0, 24);
}

export function stepFilename(params) {
  const p = normalizeParams(params);
  const slope = String(p.slope_deg).replace("-", "m").replace(".", "p");
  return `trestle_slope_${slope}_${stepKey(p).slice(0, 8)}.step`;
}

async function ensureKernel() {
  kernelReady ||= init();
  await kernelReady;
}

function memberToPart(member) {
  const start = member.start;
  const end = member.end;
  const direction = [end[0] - start[0], end[1] - start[1], end[2] - start[2]];
  const length = vectorLength(direction);
  const [width, depth] = SECTION_SIZES[member.section] || [120, 120];
  const center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2];
  const shape = orientBox(width, depth, length, center, direction);
  return {
    shape,
    name: `${member.category}:${member.id}`,
    color: COLOR_BY_CATEGORY[member.category] || "#666666",
    alpha: 1,
  };
}

function spliceMarkerParts(params) {
  const p = normalizeParams(params);
  const ranges = computeSegmentRanges(p).slice(0, -1);
  const parts = [];
  const width = p.support_width + 1200;
  const y0 = p.y_origin - width / 2;
  const y1 = p.y_origin + width / 2;
  ranges.forEach(([, end], index) => {
    const topZ = p.start_elevation + Math.tan((p.slope_deg * Math.PI) / 180) * end;
    const height = topZ + 3200;
    const specs = [
      { size: [130, 120, height], center: [end, y0, height / 2] },
      { size: [130, 120, height], center: [end, y1, height / 2] },
      { size: [130, width + 120, 120], center: [end, p.y_origin, height] },
    ];
    specs.forEach((spec, pieceIndex) => {
      parts.push({
        shape: translate(box(spec.size[0], spec.size[1], spec.size[2], { centered: true }), spec.center),
        name: `splice_marker:P${index + 1}/P${index + 2}:${pieceIndex + 1}`,
        color: COLOR_BY_CATEGORY.splice_marker,
        alpha: 1,
      });
    });
  });
  return parts;
}

function orientBox(width, depth, length, center, direction) {
  const sourceAxis = [0, 0, 1];
  const targetAxis = normalize(direction);
  let shape = box(width, depth, length, { centered: true });
  const dot = clamp(vectorDot(sourceAxis, targetAxis), -1, 1);
  if (dot < 1 - 1e-10) {
    if (dot <= -1 + 1e-10) {
      shape = rotate(shape, 180, { axis: [1, 0, 0] });
    } else {
      const axis = normalize(vectorCross(sourceAxis, targetAxis));
      const angle = (Math.acos(dot) * 180) / Math.PI;
      shape = rotate(shape, angle, { axis });
    }
  }
  return translate(shape, center);
}

function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function vectorLength(vector) {
  return Math.hypot(vector[0], vector[1], vector[2]);
}

function normalize(vector) {
  const length = vectorLength(vector) || 1;
  return [vector[0] / length, vector[1] / length, vector[2] / length];
}

function vectorDot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function vectorCross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function formatBrepError(error) {
  if (!error) return "STEP export failed";
  if (typeof error === "string") return error;
  return error.message || error.kind || JSON.stringify(error);
}

function withQuietConsole(fn) {
  const originalLog = console.log;
  const originalInfo = console.info;
  const originalStdoutWrite = process.stdout.write;
  const originalStderrWrite = process.stderr.write;
  console.log = () => {};
  console.info = () => {};
  process.stdout.write = () => true;
  process.stderr.write = () => true;
  try {
    return fn();
  } finally {
    console.log = originalLog;
    console.info = originalInfo;
    process.stdout.write = originalStdoutWrite;
    process.stderr.write = originalStderrWrite;
  }
}
