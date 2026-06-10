# src/context_engine.py
from dataclasses import dataclass, field

from src.agents.base_agent import BaseAgent
from src.agents.confidence_auditor import ConfidenceAuditor
from src.agents.historical_agent import HistoricalAgent
from src.agents.journalist_agent import JournalistAgent
from src.agents.lineup_agent import LineupAgent
from src.agents.public_signal_agent import PublicSignalAgent
from src.agents.red_team_agent import RedTeamAgent
from src.agents.tactical_agent import TacticalAgent
from src.agents.weather_agent import WeatherAgent

ADJUSTMENT_MIN = -0.20
ADJUSTMENT_MAX = 0.20


@dataclass
class AgentContribution:
    agent_name: str
    weight: float
    confidence: float
    adjustment_home: float
    adjustment_away: float
    rationale: str
    effective_contribution: float


@dataclass
class ContextEngineResult:
    context_adjustment: float
    agent_contributions: list = field(default_factory=list)
    total_weight: float = 0.0


def _default_agents() -> list:
    return [
        JournalistAgent(),
        PublicSignalAgent(),
        LineupAgent(),
        WeatherAgent(),
        TacticalAgent(),
        HistoricalAgent(),
        RedTeamAgent(),
        ConfidenceAuditor(),
    ]


class ContextEngine:
    def __init__(self, agents=None):
        self.agents = agents if agents is not None else _default_agents()

    def run(self, context: dict) -> ContextEngineResult:
        contributions = []
        weighted_sum = 0.0
        weight_sum = 0.0

        for agent in self.agents:
            result = agent.analyze(context)
            directional = result.adjustment_home - result.adjustment_away
            effective = agent.weight * result.confidence * directional
            weighted_sum += effective
            weight_sum += agent.weight

            contributions.append(
                AgentContribution(
                    agent_name=agent.name,
                    weight=agent.weight,
                    confidence=result.confidence,
                    adjustment_home=result.adjustment_home,
                    adjustment_away=result.adjustment_away,
                    rationale=result.rationale,
                    effective_contribution=round(effective, 4),
                )
            )

        raw = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        clamped = max(ADJUSTMENT_MIN, min(ADJUSTMENT_MAX, raw))

        return ContextEngineResult(
            context_adjustment=round(clamped, 4),
            agent_contributions=contributions,
            total_weight=round(weight_sum, 4),
        )
