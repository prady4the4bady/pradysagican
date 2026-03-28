"""One-command smoke validation for PRADYSAGICAN unified app."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8020"


def get_json(path: str, headers: dict[str, str] | None = None) -> dict:
    req = Request(f"{BASE_URL}{path}", headers=headers or {}, method="GET")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(path: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "pradysagican.api.app:create_unified_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            "8020",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(3)
        live = get_json("/live")
        ready = get_json("/ready")
        version = get_json("/version")
        key = get_json("/keys/test")["api_key"]
        _ = post_json("/process", {"query": "smoke test request"}, headers={"X-API-Key": key})
        traces = get_json("/traces", headers={"X-API-Key": key})
        dashboard = get_json("/dashboard", headers={"X-API-Key": key})
        report = get_json("/reports/export", headers={"X-API-Key": key})

        assert live["status"] == "alive"
        assert ready["status"] in ("ready", "not_ready")
        assert "version" in version
        assert traces["total"] >= 1
        assert "metrics" in dashboard
        assert report["trace_count"] >= 1
        print("SMOKE_VALIDATE_OK")
        return 0
    except (AssertionError, HTTPError, URLError, KeyError, TimeoutError) as exc:
        print(f"SMOKE_VALIDATE_FAIL: {exc}")
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
