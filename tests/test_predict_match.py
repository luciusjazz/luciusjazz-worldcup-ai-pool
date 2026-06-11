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


def test_predict_all_runs_without_error(tmp_path):
    result = run_script("--all", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_single_match(tmp_path):
    result = run_script("--match-id", "GRP_E01", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_output_contains_match_id(tmp_path):
    result = run_script("--match-id", "GRP_E01", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert "GRP_E01" in result.stdout


def test_predict_unknown_match_exits():
    result = run_script("--match-id", "FAKE999", "--mode", "INITIAL")
    assert result.returncode != 0


def test_predict_no_args_exits():
    result = run_script()
    assert result.returncode != 0


def test_history_not_written_to_production_dir(tmp_path):
    """Testes não devem contaminar data/history/."""
    production_dir = ROOT / "data" / "history"
    files_before = set(production_dir.glob("*.jsonl")) if production_dir.exists() else set()

    run_script("--match-id", "GRP_A01", "--mode", "T_24H", "--history-dir", str(tmp_path))

    files_after = set(production_dir.glob("*.jsonl")) if production_dir.exists() else set()
    new_files = files_after - files_before
    assert len(new_files) == 0, f"Teste contaminou produção: {new_files}"
