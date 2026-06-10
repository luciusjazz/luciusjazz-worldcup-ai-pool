from src.agents.base_agent import AgentResult, BaseAgent


class PublicSignalAgent(BaseAgent):
    name = "Analista de Sinais Públicos"
    weight = 0.12

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        return AgentResult(
            findings=[
                f"Sem odds ou sinais de mercado coletados para {home} vs {away}.",
                "Odds de casas de apostas são sinais públicos; não constituem recomendação.",
            ],
            confidence=0.3,
            recommendations=[
                "Verificar odds médias em Oddsportal ou similar antes do jogo.",
                "Movimentos de linha acima de 5% merecem atenção.",
            ],
        )
