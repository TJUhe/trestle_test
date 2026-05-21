import type { Config, Context } from "@netlify/functions";
import { getStore } from "@netlify/blobs";
import { buildStepExport } from "./_shared/trestle-step.mjs";

const jsonHeaders = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
};

export default async (req: Request, _context: Context) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders() });
  if (req.method !== "POST") {
    return json({ ok: false, error: "Method not allowed" }, 405);
  }

  try {
    const payload = await req.json();
    const step = await buildStepExport(payload.params ?? payload);
    const store = getStore({ name: "trestle-step-exports", consistency: "strong" });
    const blobKey = `${step.key}.step`;
    await store.set(blobKey, step.stepText, {
      metadata: {
        contentType: step.contentType,
        filename: step.filename,
        generatedAt: new Date().toISOString(),
      },
    });

    return json({
      ok: true,
      key: step.key,
      filename: step.filename,
      step_url: `/api/step/${step.key}/${encodeURIComponent(step.filename)}`,
      params: step.params,
      members: step.members,
      summary: step.summary,
      segments: step.segments,
    });
  } catch (error) {
    console.error(error);
    return json({ ok: false, error: error instanceof Error ? error.message : String(error) }, 500);
  }
};

export const config: Config = {
  path: "/api/rebuild-step",
  method: ["POST", "OPTIONS"],
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...jsonHeaders, ...corsHeaders() },
  });
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
}
