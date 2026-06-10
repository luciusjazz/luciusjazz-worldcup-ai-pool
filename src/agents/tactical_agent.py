from src.agents.base_agent import AgentResult, BaseAgent


class TacticalAgent(BaseAgent):
    name = "Scout Tático"
    weight = 0.10

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        return AgentResult(
            findings=[
                f"Análise tática de {home} vs {away} requer dados de últimas 5 partidas.",
                "Sem dados táticos detalhados disponíveis nesta sessão.",
            ],
            confidence=0.3,
            recommendations=[
                "Verificar esquema tático (Sofascore, WhoScored).",
                "Avaliar pressão alta vs. bloco baixo — impacta ritmo de gols.",
            ],
        )
