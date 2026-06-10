# tests/test_elo_model.py
import pytest

from src.models.elo_model import EloModel


@pytest.fixture
def model():
    return EloModel()


def test_expected_goals_higher_rated_team(model):
    la, lb = model.expected_goals(
        elo_a=2000, elo_b=1600, attack_a=1.3, defense_a=1.2, attack_b=1.0, defense_b=1.0
    )
    assert la > lb, "Time com ELO maior deve ter xG maior"


def test_expected_goals_equal_teams(model):
    la, lb = model.expected_goals(
        elo_a=1800, elo_b=1800, attack_a=1.0, defense_a=1.0, attack_b=1.0, defense_b=1.0
    )
    assert abs(la - lb) < 0.01, "Times iguais devem ter xG iguais"


def test_expected_goals_minimum_floor(model):
    la, lb = model.expected_goals(
        elo_a=1000, elo_b=2500, attack_a=0.5, defense_a=2.0, attack_b=2.0, defense_b=0.5
    )
    assert la >= 0.1
    assert lb >= 0.1


def test_predict_returns_required_keys(model):
    result = model.predict(
        home_team="Brazil",
        away_team="Bolivia",
        elo_home=2000,
        elo_away=1550,
        attack_home=1.32,
        defense_home=1.20,
        attack_away=0.88,
        defense_away=0.85,
    )
    for key in (
        "home_team",
        "away_team",
        "lambda_home",
        "lambda_away",
        "prob_home",
        "prob_draw",
        "prob_away",
        "recommended_score",
        "confidence",
    ):
        assert key in result, f"Chave ausente: {key}"


def test_probabilities_sum_to_one(model):
    result = model.predict(
        home_team="Spain",
        away_team="Germany",
        elo_home=1990,
        elo_away=1940,
        attack_home=1.30,
        defense_home=1.28,
        attack_away=1.22,
        defense_away=1.18,
    )
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001
