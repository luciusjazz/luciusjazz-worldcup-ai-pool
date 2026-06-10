from src.agents.base_agent import AgentResult, BaseAgent

ELO_DIFF_THRESHOLD = 200
UNDERDOG_BOOST = 0.06


class RedTeamAgent(BaseAgent):
    name = "Red Team Agent"
    weight = 0.05

    def analyze(self, context: dict) -> AgentResult:
        home, away = context.get("home_team", "?"), context.get("away_team", "?")
        elo_home = context.get("elo_home")
        elo_away = context.get("elo_away")
        stage = context.get("stage", "")

        adjustment_home = 0.0
        adjustment_away = 0.0
        rationale = "Equilíbrio entre times — sem ajuste adversarial."

        findings = [
            "Avaliação adversarial: quais são os cenários que invalidam o palpite?",
            f"Risco: {away} pode surpreender se {home} tiver baixa motivação (ex: já classificado).",
            "Risco: modelo Poisson assume independência de gols — subestima séries e momentum.",
        ]

        if stage == "group":
            findings.append("Em grupos, times favoritos às vezes poupam titulares na 3ª rodada.")

        if elo_home is not None and elo_away is not None:
            elo_diff = elo_home - elo_away
            if elo_diff > ELO_DIFF_THRESHOLD:
                adjustment_away = UNDERDOG_BOOST
                rationale = (
                    f"Diferença ELO={elo_diff:.0f} indica favorito absoluto ({home}). "
                    f"Boost adversarial ao visitante ({UNDERDOG_BOOST}) — zebra histórica."
                )
            elif elo_diff < -ELO_DIFF_THRESHOLD:
                adjustment_home = UNDERDOG_BOOST
                rationale = (
                    f"Diferença ELO={abs(elo_diff):.0f} indica favorito absoluto ({away}). "
                    f"Boost adversarial ao mandante ({UNDERDOG_BOOST}) — zebra histórica."
                )

        return AgentResult(
            findings=findings,
            confidence=0.5,
            recommendations=[
                "Questionar cada premissa do modelo antes de confirmar o palpite.",
                "Se confiança > 70%, revisar se não há viés de confirmação.",
            ],
            adjustment_home=adjustment_home,
            adjustment_away=adjustment_away,
            rationale=rationale,
        )
