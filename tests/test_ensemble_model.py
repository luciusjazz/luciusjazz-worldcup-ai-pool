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
        home_team="Germany",
        away_team="Italy",
        elo_home=1940,
        elo_away=1920,
        attack_home=1.22,
        defense_home=1.18,
        attack_away=1.15,
        defense_away=1.20,
    )
    for key in (
        "home_team",
        "away_team",
        "prob_home",
        "prob_draw",
        "prob_away",
        "recommended_score",
        "confidence",
        "lambda_home",
        "lambda_away",
        "top5_scores",
        "model_contributions",
    ):
        assert key in result, f"Chave ausente: {key}"


def test_probabilities_sum_to_one(ensemble):
    result = ensemble.predict(
        home_team="A",
        away_team="B",
        elo_home=1800,
        elo_away=1750,
        attack_home=1.1,
        defense_home=1.0,
        attack_away=0.95,
        defense_away=1.05,
    )
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001


def test_invalid_weights_raise():
    with pytest.raises(ValueError):
        ModelWeights(elo=0.5, poisson=0.5, dixon_coles=0.5, context=0.5)


def test_context_adjustment_shifts_lambda(ensemble):
    base = ensemble.predict(
        home_team="A",
        away_team="B",
        elo_home=1800,
        elo_away=1800,
        attack_home=1.0,
        defense_home=1.0,
        attack_away=1.0,
        defense_away=1.0,
    )
    with_ctx = ensemble.predict(
        home_team="A",
        away_team="B",
        elo_home=1800,
        elo_away=1800,
        attack_home=1.0,
        defense_home=1.0,
        attack_away=1.0,
        defense_away=1.0,
        context_adjustment=0.20,
    )
    assert with_ctx["lambda_home"] != base["lambda_home"]


def test_context_adjustment_positive_increases_home_lambda(ensemble):
    result_neutral = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    result_positive = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.10,
    )
    assert result_positive["lambda_home"] > result_neutral["lambda_home"]
    assert result_positive["lambda_away"] < result_neutral["lambda_away"]


def test_context_adjustment_negative_increases_away_lambda(ensemble):
    result_neutral = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    result_negative = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=-0.10,
    )
    assert result_negative["lambda_away"] > result_neutral["lambda_away"]
    assert result_negative["lambda_home"] < result_neutral["lambda_home"]


def test_context_adjustment_zero_has_no_effect(ensemble):
    r1 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    r2 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
    )
    assert r1["lambda_home"] == r2["lambda_home"]
    assert r1["lambda_away"] == r2["lambda_away"]


def test_context_adjustment_impact_is_significant(ensemble):
    """context_adjustment=0.10 deve causar ~10% de diferença nas lambdas."""
    r0 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    r1 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.10,
    )
    ratio_home = r1["lambda_home"] / r0["lambda_home"]
    ratio_away = r1["lambda_away"] / r0["lambda_away"]
    # Com aplicação direta: lh*(1+0.10) = 1.10*lh → ratio deve ser ≈1.10
    assert ratio_home == pytest.approx(1.10, abs=0.01)
    assert ratio_away == pytest.approx(0.90, abs=0.01)
