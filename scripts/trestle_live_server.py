from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
DEFAULT_OUT_DIR = ROOT / "zj8_trestle_20260521_user_params"
DEFAULT_PARAMS_FILE = DEFAULT_OUT_DIR / "trestle_parameters.json"
EXPORT_SCRIPT = SCRIPTS_DIR / "trestle_exports.py"
STEP_SOURCE = SCRIPTS_DIR / "trestle_generator.py"
DRAWING_SOURCE = SCRIPTS_DIR / "trestle_three_view_drawing.py"
CAD_STEP_CLI = Path("C:/Users/Lenovo/.codex/skills/cad/scripts/step")
DRAWING2D_CLI = Path("C:/Users/Lenovo/.codex/skills/drawing2d/scripts/drawing2d_cli.py")

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from trestle_core import TrestleParameters, build_members, compute_segment_ranges, export_parameters_json, summarize_members
from trestle_project import load_parameters


BUILD_LOCK = threading.Lock()


def _cli_path(path: Path) -> str:
    return path.resolve().as_posix()


def _params_from_payload(payload: dict[str, Any]) -> TrestleParameters:
    raw = payload.get("params", payload)
    if not isinstance(raw, dict):
        raise ValueError("Request body must contain a JSON object")
    fields = TrestleParameters.__dataclass_fields__
    kwargs = {key: value for key, value in raw.items() if key in fields}
    return TrestleParameters(**kwargs)


def _load_initial_params() -> TrestleParameters:
    if DEFAULT_PARAMS_FILE.exists():
        data = json.loads(DEFAULT_PARAMS_FILE.read_text(encoding="utf-8"))
        fields = TrestleParameters.__dataclass_fields__
        return TrestleParameters(**{key: value for key, value in data.items() if key in fields})
    return load_parameters()


def _run_command(command: list[str], env: dict[str, str], cwd: Path) -> dict[str, str]:
    result = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "command failed").strip()
        raise RuntimeError(f"{' '.join(command)}\n{details}")
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _build_outputs(params: TrestleParameters, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    params_file = out_dir / "trestle_parameters.json"
    export_parameters_json(params, params_file)

    env = os.environ.copy()
    env["ZJ8_PARAMS"] = str(params_file)
    env["ZJ8_OUT_DIR"] = str(out_dir)
    env["ZJ8_SLOPE_DEG"] = str(params.slope_deg)
    env["ZJ8_SEGMENT_SPANS"] = ",".join(str(value) for value in params.segment_spans)

    export_summary = _run_command(
        [
            sys.executable,
            _cli_path(EXPORT_SCRIPT),
            "--params",
            _cli_path(params_file),
            "--out-dir",
            _cli_path(out_dir),
            "--sample-inputs",
            "--split-segments",
        ],
        env,
        ROOT,
    )

    step_output = out_dir / "trestle.step"
    step_summary = _run_command(
        [
            sys.executable,
            _cli_path(CAD_STEP_CLI),
            _cli_path(STEP_SOURCE),
            "-o",
            _cli_path(step_output),
            "--skip-explorer",
        ],
        env,
        ROOT,
    )

    three_view_base = out_dir / "trestle_three_view"
    drawing_summary = _run_command(
        [
            sys.executable,
            _cli_path(DRAWING2D_CLI),
            f"{_cli_path(DRAWING_SOURCE)}={_cli_path(three_view_base)}",
            "--dwg",
            "auto",
            "--summary",
            _cli_path(out_dir / "trestle_three_view_summary.json"),
        ],
        env,
        ROOT,
    )

    members = build_members(params)
    return {
        "ok": True,
        "out_dir": str(out_dir),
        "params_file": str(params_file),
        "params": params.to_dict(),
        "members": [member.as_row() for member in members],
        "summary": summarize_members(members),
        "segments": compute_segment_ranges(params),
        "outputs": {
            "step": str(step_output),
            "dxf": str(out_dir / "trestle_tutorial_replica.dxf"),
            "dwg": str(out_dir / "trestle_three_view.dwg"),
            "three_view": str(out_dir / "trestle_three_view.html"),
            "summary": str(out_dir / "trestle_three_view_summary.json"),
            "parameters": str(params_file),
        },
        "logs": {
            "exports": export_summary,
            "step": step_summary,
            "drawing": drawing_summary,
        },
    }


class LiveHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/rebuild":
            self.send_error(404, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            params = _params_from_payload(payload)
            with BUILD_LOCK:
                result = _build_outputs(params, self.server.out_dir)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            body = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        message = format % args
        print(f"[http] {self.address_string()} {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the Zhongjian8 live parameter preview and auto-rebuild outputs.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir).resolve()
    handler = partial(LiveHandler, directory=str(out_dir))
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    httpd.out_dir = out_dir  # type: ignore[attr-defined]

    if not (out_dir / "trestle_parameters.json").exists():
        with BUILD_LOCK:
            _build_outputs(_load_initial_params(), out_dir)

    print(f"Serving {out_dir} at http://{args.host}:{args.port}/")
    print(f"Open http://{args.host}:{args.port}/trestle_parametric_3d_preview.html for live STEP/DWG sync.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
