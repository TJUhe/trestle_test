import type { Config, Context } from "@netlify/functions";
import { getStore } from "@netlify/blobs";

export default async (_req: Request, context: Context) => {
  const key = context.params.key;
  const requestedName = context.params.filename || "trestle.step";
  if (!key) return new Response("Missing STEP key", { status: 400 });

  const store = getStore({ name: "trestle-step-exports", consistency: "strong" });
  const result = await store.getWithMetadata(`${key}.step`, { type: "arrayBuffer" });
  if (!result) return new Response("STEP file not found or expired", { status: 404 });

  const metadata = (result.metadata || {}) as { filename?: string; contentType?: string };
  const filename = sanitizeFilename(metadata.filename || decodeURIComponent(requestedName));
  return new Response(result.data as ArrayBuffer, {
    headers: {
      "Content-Type": metadata.contentType || "model/step",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};

export const config: Config = {
  path: "/api/step/:key/:filename",
  method: "GET",
};

function sanitizeFilename(filename: string) {
  const cleaned = filename.replace(/[^A-Za-z0-9._-]/g, "_");
  return cleaned.toLowerCase().endsWith(".step") ? cleaned : `${cleaned}.step`;
}
