from src.agents.base_agent import BaseAgent, AgentResult

class ConfidenceAuditor(BaseAgent):
    name = "Auditor de Confiança"
    weight = 0.05

    def analyze(self, context: dict) -> AgentResult:
        prob_home = context.get("prob_home", 0.33)
        prob_draw = context.get("prob_draw", 0.33)
        prob_away = context.get("prob_away", 0.33)
        max_prob = max(prob_home, prob_draw, prob_away)

        findings = []
        recommendations = []

        if max_prob > 0.70:
            findings.append(
                f"ALERTA: probabilidade máxima muito alta ({max_prob:.0%}). "
                "Risco de excesso de confiança."
            )
            recommendations.append(
                "Revisar premissas; reduzir confiança para 'Moderada' se não houver dados sólidos."
            )
        elif max_prob > 0.55:
            findings.append(f"Confiança moderada a alta ({max_prob:.0%}). Aceitável se baseada em dados.")
        else:
            findings.append(f"Jogo equilibrado (max prob: {max_prob:.0%}). Confiança baixa é apropriada.")

        findings.append("Auditoria: verificar se todas as fontes foram consultadas antes do palpite final.")
        recommendations.append("Documentar limitações no relatório final.")

        return AgentResult(
            findings=findings,
            confidence=0.8,
            recommendations=recommendations,
        )
