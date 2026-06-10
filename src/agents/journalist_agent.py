from src.agents.base_agent import BaseAgent, AgentResult

class JournalistAgent(BaseAgent):
    name = "Jornalista Esportivo"
    weight = 0.12

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        return AgentResult(
            findings=[
                f"Sem notícias recentes disponíveis para {home} vs {away} nesta sessão.",
                "Consulte: BBC Sport, UOL Esporte, ESPN Brasil para atualizações.",
            ],
            confidence=0.3,
            recommendations=[
                "Verificar notícias de lesões e suspensões 24h antes do jogo.",
                "Confirmar status de jogadores-chave na véspera.",
            ],
        )
