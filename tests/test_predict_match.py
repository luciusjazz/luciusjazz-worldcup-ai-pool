# tests/test_predict_match.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(*args):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "predict_match.py"), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result


def test_predict_all_runs_without_error():
    result = run_script("--all", "--mode", "INITIAL")
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_single_match():
    result = run_script("--match-id", "GRP_E01", "--mode", "INITIAL")
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_unknown_match_exits():
    result = run_script("--match-id", "FAKE999", "--mode", "INITIAL")
    assert result.returncode != 0


def test_predict_no_args_exits():
    result = run_script()
    assert result.returncode != 0
