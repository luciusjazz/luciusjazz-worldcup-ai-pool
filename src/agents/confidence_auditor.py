from src.agents.base_agent import AgentResult, BaseAgent

OVERCONFIDENCE_THRESHOLD = 0.70
REGRESSION_ADJUSTMENT = -0.05


class ConfidenceAuditor(BaseAgent):
    name = "Auditor de Confiança"
    weight = 0.05

    def analyze(self, context: dict) -> AgentResult:
        prob_home = context.get("prob_home", 0.33)
        prob_draw = context.get("prob_draw", 0.33)
        prob_away = context.get("prob_away", 0.33)
        max_prob = max(prob_home, prob_draw, prob_away)

        adjustment_home = 0.0
        adjustment_away = 0.0
        rationale = f"Probabilidades equilibradas (max={max_prob:.0%}). Sem ajuste."

        findings = []
        recommendations = []

        if prob_home > OVERCONFIDENCE_THRESHOLD:
            adjustment_home = REGRESSION_ADJUSTMENT
            rationale = (
                f"Excesso de confiança no mandante (prob_home={prob_home:.0%}). "
                f"Regressão à média aplicada (adj={REGRESSION_ADJUSTMENT})."
            )
            findings.append(
                f"ALERTA: prob_home={prob_home:.0%} muito alta. Risco de excesso de confiança."
            )
            recommendations.append(
                "Revisar premissas; considerar cenários alternativos para o visitante."
            )
        elif prob_away > OVERCONFIDENCE_THRESHOLD:
            adjustment_away = REGRESSION_ADJUSTMENT
            rationale = (
                f"Excesso de confiança no visitante (prob_away={prob_away:.0%}). "
                f"Regressão à média aplicada (adj={REGRESSION_ADJUSTMENT})."
            )
            findings.append(
                f"ALERTA: prob_away={prob_away:.0%} muito alta. Risco de excesso de confiança."
            )
            recommendations.append(
                "Revisar premissas; considerar cenários alternativos para o mandante."
            )
        elif max_prob > 0.55:
            findings.append(
                f"Confiança moderada a alta ({max_prob:.0%}). Aceitável se baseada em dados."
            )
        else:
            findings.append(
                f"Jogo equilibrado (max prob: {max_prob:.0%}). Confiança baixa é apropriada."
            )

        findings.append(
            "Auditoria: verificar se todas as fontes foram consultadas antes do palpite final."
        )
        recommendations.append("Documentar limitações no relatório final.")

        return AgentResult(
            findings=findings,
            confidence=0.8,
            recommendations=recommendations,
            adjustment_home=adjustment_home,
            adjustment_away=adjustment_away,
            rationale=rationale,
        )
