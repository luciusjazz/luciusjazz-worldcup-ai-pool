# tests/test_ensemble_model.py
import pytest
from src.models.ensemble_model import EnsembleModel, ModelWeights


@pytest.fixture
def ensemble():
    return EnsembleModel()


def test_default_weights_sum_to_one(ensemble):
    w = ensemble.weights
    total = w.elo + w.poisson + w.dixon_coles + w.context
    assert abs(total - 1.0) < 0.001


def test_predict_returns_required_keys(ensemble):
    result = ensemble.predict(
        home_team="Germany", away_team="Italy",
        elo_home=1940, elo_away=1920,
        attack_home=1.22, defense_home=1.18,
        attack_away=1.15, defense_away=1.20,
    )
    for key in ("home_team", "away_team", "prob_home", "prob_draw", "prob_away",
                "recommended_score", "confidence", "lambda_home", "lambda_away",
                "top5_scores", "model_contributions"):
        assert key in result, f"Chave ausente: {key}"


def test_probabilities_sum_to_one(ensemble):
    result = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.1, defense_home=1.0,
        attack_away=0.95, defense_away=1.05,
    )
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001


def test_invalid_weights_raise():
    with pytest.raises(ValueError):
        ModelWeights(elo=0.5, poisson=0.5, dixon_coles=0.5, context=0.5)


def test_context_adjustment_shifts_lambda(ensemble):
    base = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1800,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
    )
    with_ctx = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1800,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.20,
    )
    assert with_ctx["lambda_home"] != base["lambda_home"]
