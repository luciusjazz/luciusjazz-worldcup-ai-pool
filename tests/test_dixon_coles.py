# tests/test_dixon_coles.py
import pytest

from src.models.dixon_coles import DixonColesModel, dixon_coles_adjustment


def test_adjustment_low_scores_above_one():
    # (1,0): 1 + lambda_a * rho = 1 + 1.0*0.1 = 1.1 > 1.0
    adj = dixon_coles_adjustment(1, 0, lambda_h=1.2, lambda_a=1.0, rho=0.1)
    assert adj > 1.0


def test_adjustment_high_scores_near_one():
    adj = dixon_coles_adjustment(3, 2, lambda_h=1.2, lambda_a=1.0, rho=0.1)
    assert abs(adj - 1.0) < 0.001


def test_adjustment_rho_zero_is_one():
    for gh in range(3):
        for ga in range(3):
            adj = dixon_coles_adjustment(gh, ga, lambda_h=1.2, lambda_a=1.0, rho=0.0)
            assert abs(adj - 1.0) < 1e-9, f"rho=0 deve retornar 1.0 para ({gh},{ga})"


@pytest.fixture
def model():
    return DixonColesModel()


def test_predict_returns_required_keys(model):
    result = model.predict(
        home_team="Japan",
        away_team="Iraq",
        lambda_home=1.1,
        lambda_away=0.9,
    )
    for key in (
        "home_team",
        "away_team",
        "prob_home",
        "prob_draw",
        "prob_away",
        "recommended_score",
        "confidence",
    ):
        assert key in result


def test_probabilities_sum_to_one(model):
    result = model.predict(
        home_team="A",
        away_team="B",
        lambda_home=1.3,
        lambda_away=1.0,
    )
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001
