from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.config import DATA_DIR, PROJECT_ROOT


@pytest.mark.skipif(
    not (DATA_DIR / "matches.csv").exists(), reason="raw CSV hanya tersedia lokal"
)
def test_training_cli_runs_from_repository_root() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/train.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Selesai: 2 semifinal" in result.stdout
    assert (Path(PROJECT_ROOT) / "artifacts" / "predictions.json").exists()

