from src.agents.base_agent import AgentResult, BaseAgent


class LineupAgent(BaseAgent):
    name = "Especialista em Escalações"
    weight = 0.10

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        return AgentResult(
            findings=[
                f"Escalações de {home} e {away} não confirmadas nesta sessão.",
                "Escalações oficiais geralmente disponíveis 1h antes do jogo.",
            ],
            confidence=0.25,
            recommendations=[
                "Confirmar titulares via site oficial das federações.",
                "Atenção especial a goleiro titular e artilheiro principal.",
            ],
            adjustment_home=0.0,
            adjustment_away=0.0,
            rationale="Escalações não confirmadas — ajuste neutro aplicado.",
        )
