"""Repository hygiene checks for confidentiality rules."""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("git not available")
    return out.splitlines()


def test_no_local_files_tracked():
    """D-24: *.local.* files (e.g. the real denylist) must never be committed."""
    offenders = [f for f in tracked_files() if ".local." in Path(f).name]
    assert offenders == []


def test_no_env_file_tracked():
    assert ".env" not in [Path(f).name for f in tracked_files()]
