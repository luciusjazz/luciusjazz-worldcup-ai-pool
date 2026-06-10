# tests/test_revision.py
import pytest
from pathlib import Path
from src.revision import RevisionManager
from src.history import HistoryStore, PredictionRecord


@pytest.fixture
def manager(tmp_path):
    store = HistoryStore(base_dir=tmp_path / "history")
    reports_dir = tmp_path / "reports" / "revision_history"
    return RevisionManager(store=store, reports_dir=reports_dir)


def make_record(match_id, mode, score, conf):
    return PredictionRecord(
        match_id=match_id, mode=mode,
        home_team="Brazil", away_team="France",
        recommended_score=score,
        prob_home=0.40, prob_draw=0.30, prob_away=0.30,
        confidence=conf,
        lambda_home=1.4, lambda_away=1.2,
        top5_scores=[], notes="",
    )


def test_save_and_generate_report(manager):
    rec = make_record("GRP_E06", "INITIAL", (1, 1), "Baixa")
    path = manager.save_revision(rec)
    assert path.exists()


def test_compare_detects_score_change(manager):
    r1 = make_record("GRP_E06", "INITIAL", (1, 0), "Baixa")
    r2 = make_record("GRP_E06", "T_24H", (2, 1), "Moderada")
    manager.save_revision(r1)
    diff = manager.compare_with_previous("GRP_E06", r2)
    assert diff["score_changed"] is True


def test_compare_detects_no_change(manager):
    r1 = make_record("GRP_E06", "INITIAL", (1, 0), "Baixa")
    r2 = make_record("GRP_E06", "T_24H", (1, 0), "Baixa")
    manager.save_revision(r1)
    diff = manager.compare_with_previous("GRP_E06", r2)
    assert diff["score_changed"] is False


def test_report_file_created(manager):
    rec = make_record("GRP_A01", "T_24H", (2, 0), "Moderada")
    manager.save_revision(rec)
    reports = list(manager.reports_dir.glob("*.md"))
    assert len(reports) >= 1


def test_compare_no_previous(manager):
    r = make_record("GRP_NEW", "INITIAL", (1, 0), "Baixa")
    diff = manager.compare_with_previous("GRP_NEW", r)
    assert diff["has_previous"] is False
