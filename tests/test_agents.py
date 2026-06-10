# tests/test_agents.py
import pytest

from src.agents.base_agent import AgentResult
from src.agents.confidence_auditor import ConfidenceAuditor
from src.agents.historical_agent import HistoricalAgent
from src.agents.journalist_agent import JournalistAgent
from src.agents.lineup_agent import LineupAgent
from src.agents.public_signal_agent import PublicSignalAgent
from src.agents.red_team_agent import RedTeamAgent
from src.agents.tactical_agent import TacticalAgent
from src.agents.weather_agent import WeatherAgent

ALL_AGENTS = [
    JournalistAgent,
    PublicSignalAgent,
    LineupAgent,
    WeatherAgent,
    TacticalAgent,
    HistoricalAgent,
    RedTeamAgent,
    ConfidenceAuditor,
]

MATCH_CONTEXT = {
    "home_team": "Brazil",
    "away_team": "Argentina",
    "match_id": "GRP_E01",
    "stage": "group",
}


@pytest.mark.parametrize("AgentClass", ALL_AGENTS)
def test_agent_returns_agent_result(AgentClass):
    agent = AgentClass()
    result = agent.analyze(MATCH_CONTEXT)
    assert isinstance(result, AgentResult)


@pytest.mark.parametrize("AgentClass", ALL_AGENTS)
def test_agent_result_has_required_fields(AgentClass):
    agent = AgentClass()
    result = agent.analyze(MATCH_CONTEXT)
    assert isinstance(result.findings, list)
    assert isinstance(result.confidence, float)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.recommendations, list)


@pytest.mark.parametrize("AgentClass", ALL_AGENTS)
def test_agent_findings_are_strings(AgentClass):
    agent = AgentClass()
    result = agent.analyze(MATCH_CONTEXT)
    for f in result.findings:
        assert isinstance(f, str)


def test_confidence_auditor_flags_high_confidence():
    auditor = ConfidenceAuditor()
    result = auditor.analyze(
        {**MATCH_CONTEXT, "prob_home": 0.95, "prob_draw": 0.03, "prob_away": 0.02}
    )
    text = " ".join(result.findings).lower()
    assert any(word in text for word in ["confiança", "excesso", "alta", "alerta"])


def test_agent_result_has_adjustment_fields():
    result = AgentResult()
    assert hasattr(result, "adjustment_home")
    assert hasattr(result, "adjustment_away")
    assert hasattr(result, "rationale")
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
    assert result.rationale == ""


def test_agent_result_accepts_adjustment_values():
    result = AgentResult(adjustment_home=0.05, adjustment_away=-0.03, rationale="Teste")
    assert result.adjustment_home == 0.05
    assert result.adjustment_away == -0.03
    assert result.rationale == "Teste"


PLACEHOLDER_AGENTS = [
    JournalistAgent,
    PublicSignalAgent,
    LineupAgent,
    WeatherAgent,
    TacticalAgent,
]


@pytest.mark.parametrize("AgentClass", PLACEHOLDER_AGENTS)
def test_placeholder_agent_has_neutral_adjustment(AgentClass):
    agent = AgentClass()
    result = agent.analyze(MATCH_CONTEXT)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
    assert len(result.rationale) > 0


def test_historical_agent_reduces_when_lambdas_high():
    agent = HistoricalAgent()
    ctx = {**MATCH_CONTEXT, "lambda_home": 2.0, "lambda_away": 1.5}
    result = agent.analyze(ctx)
    assert result.adjustment_home < 0, "Lambda alto deve reduzir ajuste home"
    assert len(result.rationale) > 0


def test_historical_agent_increases_when_lambdas_low():
    agent = HistoricalAgent()
    ctx = {**MATCH_CONTEXT, "lambda_home": 0.8, "lambda_away": 0.9}
    result = agent.analyze(ctx)
    assert result.adjustment_home > 0, "Lambda baixo deve aumentar ajuste home"


def test_historical_agent_neutral_without_lambdas():
    agent = HistoricalAgent()
    result = agent.analyze(MATCH_CONTEXT)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0


def test_red_team_agent_boosts_underdog_when_elo_diff_high():
    agent = RedTeamAgent()
    ctx = {**MATCH_CONTEXT, "elo_home": 2000, "elo_away": 1750}
    result = agent.analyze(ctx)
    assert result.adjustment_away > 0, "Zebra com diff > 200 deve ter ajuste positivo"
    assert len(result.rationale) > 0


def test_red_team_agent_neutral_when_elo_close():
    agent = RedTeamAgent()
    ctx = {**MATCH_CONTEXT, "elo_home": 1800, "elo_away": 1780}
    result = agent.analyze(ctx)
    assert result.adjustment_away == 0.0


def test_confidence_auditor_reduces_home_when_overconfident():
    auditor = ConfidenceAuditor()
    ctx = {**MATCH_CONTEXT, "prob_home": 0.75, "prob_draw": 0.15, "prob_away": 0.10}
    result = auditor.analyze(ctx)
    assert result.adjustment_home < 0, "Excesso de confiança deve reduzir home"
    assert len(result.rationale) > 0


def test_confidence_auditor_neutral_for_balanced_game():
    auditor = ConfidenceAuditor()
    ctx = {**MATCH_CONTEXT, "prob_home": 0.40, "prob_draw": 0.30, "prob_away": 0.30}
    result = auditor.analyze(ctx)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
