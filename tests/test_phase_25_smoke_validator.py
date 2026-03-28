"""PHASE 25 tests: smoke validator utility."""

import subprocess
import sys
from pathlib import Path


def test_smoke_script_exists() -> None:
    path = Path("scripts") / "smoke_validate.py"
    assert path.exists()


def test_smoke_script_runs_successfully() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/smoke_validate.py"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SMOKE_VALIDATE_OK" in proc.stdout
