from src.agents.base_agent import AgentResult, BaseAgent

AVG_GOALS_PER_GAME = 2.64
DRAW_RATE = 0.22


class HistoricalAgent(BaseAgent):
    name = "Historical World Cup Analyst"
    weight = 0.06

    def analyze(self, context: dict) -> AgentResult:
        lambda_home = context.get("lambda_home")
        lambda_away = context.get("lambda_away")

        adjustment_home = 0.0
        adjustment_away = 0.0
        rationale = "Sem lambdas no contexto — ajuste neutro aplicado."

        if lambda_home is not None and lambda_away is not None:
            total_lambdas = lambda_home + lambda_away
            if total_lambdas > 3.0:
                adjustment_home = -0.05
                adjustment_away = -0.05
                rationale = (
                    f"xG total={total_lambdas:.2f} acima da média histórica "
                    f"({AVG_GOALS_PER_GAME}). Regressão à média aplicada."
                )
            elif total_lambdas < 2.0:
                adjustment_home = 0.04
                adjustment_away = 0.04
                rationale = (
                    f"xG total={total_lambdas:.2f} abaixo da média histórica "
                    f"({AVG_GOALS_PER_GAME}). Leve boost aplicado."
                )
            else:
                rationale = (
                    f"xG total={total_lambdas:.2f} dentro da faixa histórica. "
                    "Ajuste neutro."
                )

        return AgentResult(
            findings=[
                f"Média histórica de gols por jogo na Copa: {AVG_GOALS_PER_GAME}.",
                f"Taxa de empate histórica na fase de grupos: {DRAW_RATE:.0%}.",
                "Placar mais frequente historicamente: 1-0.",
            ],
            confidence=0.7,
            recommendations=[
                "Respeitar base histórica; evitar palpitar > 3 gols sem justificativa forte.",
            ],
            adjustment_home=adjustment_home,
            adjustment_away=adjustment_away,
            rationale=rationale,
        )
