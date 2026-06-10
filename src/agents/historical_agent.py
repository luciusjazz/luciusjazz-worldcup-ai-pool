from src.agents.base_agent import AgentResult, BaseAgent


class HistoricalAgent(BaseAgent):
    name = "Historical World Cup Analyst"
    weight = 0.06

    _WORLD_CUP_STATS = {
        "avg_goals_per_game": 2.64,
        "draw_rate": 0.22,
        "most_common_score": "1-0",
    }

    def analyze(self, context: dict) -> AgentResult:
        return AgentResult(
            findings=[
                f"Média histórica de gols por jogo na Copa: {self._WORLD_CUP_STATS['avg_goals_per_game']}.",
                f"Taxa de empate histórica na fase de grupos: {self._WORLD_CUP_STATS['draw_rate']:.0%}.",
                f"Placar mais frequente historicamente: {self._WORLD_CUP_STATS['most_common_score']}.",
            ],
            confidence=0.7,
            recommendations=[
                "Respeitar base histórica; evitar palpitar > 3 gols sem justificativa forte.",
            ],
        )
