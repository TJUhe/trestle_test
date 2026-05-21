# Zhongjian8 Netlify STEP Sync

This Netlify package keeps the browser preview responsive while generating STEP files from the same current parameters.

- The 3D page updates immediately in WebGL when `平台倾角` or `拼接分段长度` changes.
- After the user pauses editing, the page posts the current parameters to `/api/rebuild-step`.
- The Netlify Function rebuilds the trestle members in Node, exports a real STEP file with `brepjs`/OpenCascade WASM, stores it in Netlify Blobs, and returns a download URL.
- The `下载当前 STEP` link then points to that newly generated file.
- DWG/DXF outputs remain the static/local generated files unless a separate DWG workflow is added later.

Local checks:

```powershell
npm install
node --input-type=module -e "import('./netlify/functions/_shared/trestle-step.mjs').then(async m => { const r = await m.buildStepExport({ slope_deg: 2, segment_spans: [30000,30000,59520] }); console.log(r.filename, r.members.length, r.stepText.length); })"
```
