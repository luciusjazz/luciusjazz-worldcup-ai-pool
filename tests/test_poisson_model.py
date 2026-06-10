# tests/test_poisson_model.py
import pytest
from src.models.poisson_model import PoissonModel


@pytest.fixture
def model():
    return PoissonModel(avg_home_goals=1.35, avg_away_goals=1.10)


def test_attack_strength_strong_team(model):
    strength = model.attack_strength(team_avg_goals_scored=2.0)
    assert strength > 1.0


def test_defense_strength_weak_team(model):
    strength = model.defense_strength(team_avg_goals_conceded=1.8)
    assert strength > 1.0, "Time que sofre mais gols tem defense_strength > 1"


def test_predict_returns_required_keys(model):
    result = model.predict(
        home_team="France", away_team="Nigeria",
        home_attack=1.35, home_defense=1.30,
        away_attack=1.05, away_defense=0.95,
    )
    for key in ("home_team", "away_team", "lambda_home", "lambda_away",
                "prob_home", "prob_draw", "prob_away", "recommended_score", "confidence"):
        assert key in result


def test_home_advantage_applied(model):
    result = model.predict(
        home_team="A", away_team="B",
        home_attack=1.0, home_defense=1.0,
        away_attack=1.0, away_defense=1.0,
    )
    assert result["lambda_home"] > result["lambda_away"], "Home advantage deve elevar lambda_home"


def test_probabilities_sum_to_one(model):
    result = model.predict(
        home_team="X", away_team="Y",
        home_attack=1.2, home_defense=1.1,
        away_attack=0.9, away_defense=1.0,
    )
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001
