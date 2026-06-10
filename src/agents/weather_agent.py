from src.agents.base_agent import AgentResult, BaseAgent


class WeatherAgent(BaseAgent):
    name = "Meteorologista"
    weight = 0.05

    def analyze(self, context: dict) -> AgentResult:
        city = context.get("city", "não informada")
        return AgentResult(
            findings=[
                f"Condições climáticas em {city} não verificadas nesta sessão.",
                "Chuva intensa ou calor extremo podem reduzir ritmo e gols.",
            ],
            confidence=0.2,
            recommendations=[
                "Verificar previsão do tempo para o estádio no dia do jogo.",
                "Temperatura > 35°C ou chuva forte: reduzir ligeiramente lambda.",
            ],
        )
