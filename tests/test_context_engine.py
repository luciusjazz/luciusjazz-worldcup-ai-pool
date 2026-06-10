# tests/test_context_engine.py
import pytest

from src.context_engine import AgentContribution, ContextEngine, ContextEngineResult


FULL_CONTEXT = {
    "home_team": "Brazil",
    "away_team": "Serbia",
    "match_id": "GRP_E01",
    "stage": "group",
    "lambda_home": 1.8,
    "lambda_away": 0.9,
    "prob_home": 0.55,
    "prob_draw": 0.25,
    "prob_away": 0.20,
    "elo_home": 2060,
    "elo_away": 1800,
    "city": "Los Angeles",
}


def test_context_engine_returns_result_type():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert isinstance(result, ContextEngineResult)


def test_context_engine_result_has_required_fields():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert hasattr(result, "context_adjustment")
    assert hasattr(result, "agent_contributions")
    assert hasattr(result, "total_weight")


def test_context_adjustment_is_clamped():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert -0.20 <= result.context_adjustment <= 0.20


def test_agent_contributions_has_one_per_agent():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert len(result.agent_contributions) == 8


def test_agent_contribution_fields():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    for contrib in result.agent_contributions:
        assert isinstance(contrib, AgentContribution)
        assert hasattr(contrib, "agent_name")
        assert hasattr(contrib, "weight")
        assert hasattr(contrib, "confidence")
        assert hasattr(contrib, "adjustment_home")
        assert hasattr(contrib, "adjustment_away")
        assert hasattr(contrib, "rationale")
        assert hasattr(contrib, "effective_contribution")


def test_all_neutral_agents_give_zero_adjustment():
    """Com lambdas médias e probs equilibradas e ELO close, ajuste deve ser ~0."""
    engine = ContextEngine()
    neutral_context = {
        "home_team": "A",
        "away_team": "B",
        "match_id": "GRP_X01",
        "stage": "group",
        "lambda_home": 1.3,
        "lambda_away": 1.2,
        "prob_home": 0.40,
        "prob_draw": 0.30,
        "prob_away": 0.30,
        "elo_home": 1800,
        "elo_away": 1790,
        "city": "Dallas",
    }
    result = engine.run(neutral_context)
    assert result.context_adjustment == pytest.approx(0.0, abs=0.001)


def test_high_elo_diff_produces_nonzero_adjustment():
    """Com diff ELO > 200, RedTeamAgent deve produzir ajuste não-nulo."""
    engine = ContextEngine()
    ctx = {**FULL_CONTEXT, "elo_home": 2100, "elo_away": 1750}
    result = engine.run(ctx)
    assert result.context_adjustment != 0.0


def test_overconfident_home_produces_negative_adjustment():
    """prob_home > 0.70 deve gerar ajuste negativo (regressão à média)."""
    engine = ContextEngine()
    ctx = {**FULL_CONTEXT, "prob_home": 0.75, "prob_draw": 0.15, "prob_away": 0.10}
    result = engine.run(ctx)
    assert result.context_adjustment < 0.0
