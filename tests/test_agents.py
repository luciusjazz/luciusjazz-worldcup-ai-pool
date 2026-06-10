# tests/test_agents.py
import pytest
from src.agents.base_agent import AgentResult
from src.agents.journalist_agent import JournalistAgent
from src.agents.public_signal_agent import PublicSignalAgent
from src.agents.lineup_agent import LineupAgent
from src.agents.weather_agent import WeatherAgent
from src.agents.tactical_agent import TacticalAgent
from src.agents.historical_agent import HistoricalAgent
from src.agents.red_team_agent import RedTeamAgent
from src.agents.confidence_auditor import ConfidenceAuditor


ALL_AGENTS = [
    JournalistAgent, PublicSignalAgent, LineupAgent,
    WeatherAgent, TacticalAgent, HistoricalAgent,
    RedTeamAgent, ConfidenceAuditor,
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
    result = auditor.analyze({**MATCH_CONTEXT, "prob_home": 0.95, "prob_draw": 0.03, "prob_away": 0.02})
    text = " ".join(result.findings).lower()
    assert any(word in text for word in ["confiança", "excesso", "alta", "alerta"])
