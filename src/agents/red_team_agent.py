from src.agents.base_agent import BaseAgent, AgentResult

class RedTeamAgent(BaseAgent):
    name = "Red Team Agent"
    weight = 0.05

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        findings = [
            "Avaliação adversarial: quais são os cenários que invalidam o palpite?",
            f"Risco: {away} pode surpreender se {home} tiver baixa motivação (ex: já classificado).",
            "Risco: modelo Poisson assume independência de gols — subestima séries e momentum.",
        ]
        if context.get("stage") == "group":
            findings.append("Em grupos, times favoritos às vezes poupam titulares na 3ª rodada.")
        return AgentResult(
            findings=findings,
            confidence=0.5,
            recommendations=[
                "Questionar cada premissa do modelo antes de confirmar o palpite.",
                "Se confiança > 70%, revisar se não há viés de confirmação.",
            ],
        )
