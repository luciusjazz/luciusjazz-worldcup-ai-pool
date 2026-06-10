# tests/test_monte_carlo.py
import pytest

from src.models.monte_carlo import MonteCarloSimulation


@pytest.fixture
def sim():
    return MonteCarloSimulation(n_simulations=1000, seed=42)


def test_simulate_returns_dist(sim):
    dist = sim.simulate(lambda_home=1.5, lambda_away=1.0)
    assert len(dist) > 0
    total = sum(p for _, _, p in dist)
    assert abs(total - 1.0) < 0.01


def test_stronger_team_wins_more(sim):
    dist = sim.simulate(lambda_home=2.0, lambda_away=0.5)
    ph = sum(p for gh, ga, p in dist if gh > ga)
    pa = sum(p for gh, ga, p in dist if gh < ga)
    assert ph > pa


def test_predict_returns_required_keys(sim):
    result = sim.predict(
        home_team="Brazil",
        away_team="Bolivia",
        lambda_home=1.8,
        lambda_away=0.7,
    )
    for key in (
        "home_team",
        "away_team",
        "prob_home",
        "prob_draw",
        "prob_away",
        "recommended_score",
        "confidence",
        "simulations",
    ):
        assert key in result


def test_seeded_results_reproducible():
    s1 = MonteCarloSimulation(n_simulations=500, seed=99)
    s2 = MonteCarloSimulation(n_simulations=500, seed=99)
    r1 = s1.predict(home_team="A", away_team="B", lambda_home=1.2, lambda_away=1.0)
    r2 = s2.predict(home_team="A", away_team="B", lambda_home=1.2, lambda_away=1.0)
    assert r1["prob_home"] == r2["prob_home"]
