# tests/test_history.py

import pytest

from src.history import HistoryStore, PredictionRecord


@pytest.fixture
def store(tmp_path):
    return HistoryStore(base_dir=tmp_path / "history")


def test_save_creates_file(store):
    record = PredictionRecord(
        match_id="GRP_E01",
        mode="INITIAL",
        home_team="Brazil",
        away_team="Argentina",
        recommended_score=(1, 0),
        prob_home=0.45,
        prob_draw=0.28,
        prob_away=0.27,
        confidence="Moderada",
        lambda_home=1.5,
        lambda_away=1.1,
        top5_scores=[(1, 0, 0.14), (0, 0, 0.10)],
        notes="Previsão inicial automática",
    )
    path = store.save(record)
    assert path.exists()


def test_load_returns_record(store):
    record = PredictionRecord(
        match_id="GRP_A01",
        mode="T_24H",
        home_team="USA",
        away_team="Panama",
        recommended_score=(2, 0),
        prob_home=0.60,
        prob_draw=0.22,
        prob_away=0.18,
        confidence="Moderada",
        lambda_home=1.8,
        lambda_away=0.9,
        top5_scores=[(2, 0, 0.18)],
        notes="Revisão T-24h",
    )
    store.save(record)
    history = store.load("GRP_A01")
    assert len(history) == 1
    assert history[0]["match_id"] == "GRP_A01"


def test_multiple_revisions_accumulate(store):
    for mode in ["INITIAL", "T_24H", "T_2H"]:
        record = PredictionRecord(
            match_id="GRP_B01",
            mode=mode,
            home_team="Canada",
            away_team="Croatia",
            recommended_score=(1, 1),
            prob_home=0.33,
            prob_draw=0.34,
            prob_away=0.33,
            confidence="Baixa",
            lambda_home=1.1,
            lambda_away=1.1,
            top5_scores=[],
            notes=f"Revisão {mode}",
        )
        store.save(record)
    history = store.load("GRP_B01")
    assert len(history) == 3
    modes = [h["mode"] for h in history]
    assert "INITIAL" in modes and "T_24H" in modes and "T_2H" in modes


def test_load_all_returns_dict(store):
    for mid in ["GRP_A01", "GRP_B01"]:
        record = PredictionRecord(
            match_id=mid,
            mode="INITIAL",
            home_team="A",
            away_team="B",
            recommended_score=(1, 0),
            prob_home=0.5,
            prob_draw=0.3,
            prob_away=0.2,
            confidence="Baixa",
            lambda_home=1.2,
            lambda_away=0.9,
            top5_scores=[],
            notes="",
        )
        store.save(record)
    all_data = store.load_all()
    assert set(all_data.keys()) == {"GRP_A01", "GRP_B01"}


def test_invalid_mode_raises(store):
    with pytest.raises(ValueError):
        PredictionRecord(
            match_id="X",
            mode="INVALID",
            home_team="A",
            away_team="B",
            recommended_score=(1, 0),
            prob_home=0.5,
            prob_draw=0.3,
            prob_away=0.2,
            confidence="Baixa",
            lambda_home=1.2,
            lambda_away=0.9,
            top5_scores=[],
            notes="",
        )
