# V3.1 — Integração Real dos Agentes ao Fluxo de Predição

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer os 8 agentes influenciarem efetivamente o placar final via ContextEngine auditável, corrigir contaminação de histórico nos testes e remover arquivos legados.

**Architecture:** Cada agente devolve `adjustment_home`, `adjustment_away` e `rationale` além dos campos existentes. O `ContextEngine` agrega os 8 agentes em um único escalar `context_adjustment ∈ [-0.20, +0.20]` usando média ponderada por `agent.weight × result.confidence`. Esse escalar aplica-se diretamente às lambdas do `EnsembleModel`. O relatório de revisão inclui seção de contribuições por agente.

**Tech Stack:** Python 3.11, dataclasses, pytest, pandas, numpy — nenhuma API externa nova.

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|------------------|
| `src/agents/base_agent.py` | Modificar | Adicionar `adjustment_home`, `adjustment_away`, `rationale` ao `AgentResult` |
| `src/agents/journalist_agent.py` | Modificar | Retornar novos campos (ajuste neutro) |
| `src/agents/public_signal_agent.py` | Modificar | Retornar novos campos (ajuste neutro) |
| `src/agents/lineup_agent.py` | Modificar | Retornar novos campos (ajuste neutro) |
| `src/agents/weather_agent.py` | Modificar | Retornar novos campos (ajuste neutro) |
| `src/agents/tactical_agent.py` | Modificar | Retornar novos campos (ajuste neutro) |
| `src/agents/historical_agent.py` | Modificar | Ajuste baseado em média histórica de gols |
| `src/agents/red_team_agent.py` | Modificar | Ajuste adversarial baseado em assimetria de probabilidade |
| `src/agents/confidence_auditor.py` | Modificar | Ajuste de regressão à média quando prob > 0.70 |
| `src/context_engine.py` | **Criar** | Agrega agentes → `context_adjustment` escalar |
| `src/history.py` | Modificar | Adicionar `agent_contributions` ao `PredictionRecord` |
| `src/revision.py` | Modificar | Incluir seção de agentes no relatório Markdown |
| `src/models/ensemble_model.py` | Modificar | Aplicar `context_adjustment` diretamente às lambdas |
| `scripts/predict_match.py` | Modificar | Instanciar ContextEngine, `--history-dir` arg |
| `tests/test_agents.py` | Modificar | Testar novos campos de `AgentResult` |
| `tests/test_context_engine.py` | **Criar** | Testes completos do ContextEngine |
| `tests/test_predict_match.py` | Modificar | Usar `tmp_path` + `--history-dir` para isolar histórico |
| `tests/test_revision.py` | Modificar | Testar seção de agentes no relatório |
| `scripts/schedule_generator.py` | **Deletar** | Legado — duplicado de `generate_automations.py` |
| `data/palpites.csv` | **Deletar** | Arquivo v1 não utilizado |
| `codex/automations.md` | Modificar | Corrigir `--mode initial` → `--mode INITIAL` |
| `workflows/previsao-inicial-fase-grupos.md` | Modificar | Corrigir comando legado |
| `docs/V3_1_IMPLEMENTATION_REPORT.md` | **Criar** | Relatório final da implementação |

---

## Task 1: Expandir AgentResult com campos de ajuste

**Files:**
- Modify: `src/agents/base_agent.py`
- Modify: `tests/test_agents.py`

Contexto: `AgentResult` é um dataclass em `src/agents/base_agent.py`. Precisa de 3 campos novos opcionais para que cada agente possa expressar um ajuste direcional auditável. `adjustment_home > 0` significa "casa mais forte do que o modelo estima"; `adjustment_away > 0` significa "visitante mais forte".

- [ ] **Step 1: Escrever teste que falha — novos campos existem e têm defaults**

```python
# Em tests/test_agents.py, adicionar após os imports existentes:

def test_agent_result_has_adjustment_fields():
    result = AgentResult()
    assert hasattr(result, "adjustment_home")
    assert hasattr(result, "adjustment_away")
    assert hasattr(result, "rationale")
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
    assert result.rationale == ""


def test_agent_result_accepts_adjustment_values():
    result = AgentResult(adjustment_home=0.05, adjustment_away=-0.03, rationale="Teste")
    assert result.adjustment_home == 0.05
    assert result.adjustment_away == -0.03
    assert result.rationale == "Teste"
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
cd /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool
source .venv/bin/activate
pytest tests/test_agents.py::test_agent_result_has_adjustment_fields -v
```
Expected: FAIL — `AgentResult` não tem esses campos ainda.

- [ ] **Step 3: Implementar campos no AgentResult**

Substituir o conteúdo de `src/agents/base_agent.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    findings: list[str] = field(default_factory=list)
    confidence: float = 0.5
    recommendations: list[str] = field(default_factory=list)
    adjustment_home: float = 0.0
    adjustment_away: float = 0.0
    rationale: str = ""


class BaseAgent(ABC):
    name: str = "BaseAgent"
    weight: float = 0.0

    @abstractmethod
    def analyze(self, context: dict) -> AgentResult:
        """Analisa o contexto e retorna findings, confidence, recommendations e ajustes direcionais."""
```

- [ ] **Step 4: Rodar todos os testes de agentes**

```bash
pytest tests/test_agents.py -v
```
Expected: todos os testes existentes PASS + os 2 novos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agents/base_agent.py tests/test_agents.py
git commit -m "feat(agents): adicionar adjustment_home, adjustment_away, rationale ao AgentResult"
```

---

## Task 2: Atualizar os 5 agentes placeholder com ajuste neutro

**Files:**
- Modify: `src/agents/journalist_agent.py`
- Modify: `src/agents/public_signal_agent.py`
- Modify: `src/agents/lineup_agent.py`
- Modify: `src/agents/weather_agent.py`
- Modify: `src/agents/tactical_agent.py`

Contexto: Esses 5 agentes não têm dados reais. Devem retornar `adjustment_home=0.0`, `adjustment_away=0.0` com `rationale` explicando a neutralidade. Isso é honesto e auditável.

- [ ] **Step 1: Adicionar teste parametrizado para verificar rationale não-vazio**

Em `tests/test_agents.py`, adicionar:

```python
PLACEHOLDER_AGENTS = [
    JournalistAgent,
    PublicSignalAgent,
    LineupAgent,
    WeatherAgent,
    TacticalAgent,
]

@pytest.mark.parametrize("AgentClass", PLACEHOLDER_AGENTS)
def test_placeholder_agent_has_neutral_adjustment(AgentClass):
    agent = AgentClass()
    result = agent.analyze(MATCH_CONTEXT)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
    assert len(result.rationale) > 0
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_agents.py::test_placeholder_agent_has_neutral_adjustment -v
```
Expected: FAIL — `rationale` está vazio nos agentes atuais.

- [ ] **Step 3: Atualizar JournalistAgent**

Substituir `src/agents/journalist_agent.py`:

```python
from src.agents.base_agent import AgentResult, BaseAgent


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
            adjustment_home=0.0,
            adjustment_away=0.0,
            rationale="Sem notícias coletadas — ajuste neutro aplicado.",
        )
```

- [ ] **Step 4: Atualizar PublicSignalAgent**

Substituir `src/agents/public_signal_agent.py`:

```python
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
            adjustment_home=0.0,
            adjustment_away=0.0,
            rationale="Sem sinais de mercado coletados — ajuste neutro aplicado.",
        )
```

- [ ] **Step 5: Atualizar LineupAgent**

Substituir `src/agents/lineup_agent.py`:

```python
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
```

- [ ] **Step 6: Atualizar WeatherAgent**

Substituir `src/agents/weather_agent.py`:

```python
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
                "Temperatura > 35°C ou chuva forte: considerar redução de lambda.",
            ],
            adjustment_home=0.0,
            adjustment_away=0.0,
            rationale="Clima não verificado — ajuste neutro aplicado.",
        )
```

- [ ] **Step 7: Atualizar TacticalAgent**

Substituir `src/agents/tactical_agent.py`:

```python
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
            adjustment_home=0.0,
            adjustment_away=0.0,
            rationale="Sem dados táticos — ajuste neutro aplicado.",
        )
```

- [ ] **Step 8: Rodar testes**

```bash
pytest tests/test_agents.py -v
```
Expected: todos PASS.

- [ ] **Step 9: Commit**

```bash
git add src/agents/journalist_agent.py src/agents/public_signal_agent.py \
        src/agents/lineup_agent.py src/agents/weather_agent.py \
        src/agents/tactical_agent.py tests/test_agents.py
git commit -m "feat(agents): placeholder agents retornam ajuste neutro com rationale"
```

---

## Task 3: Atualizar os 3 agentes com lógica real de ajuste

**Files:**
- Modify: `src/agents/historical_agent.py`
- Modify: `src/agents/red_team_agent.py`
- Modify: `src/agents/confidence_auditor.py`
- Modify: `tests/test_agents.py`

Contexto: Esses 3 agentes têm lógica própria (dados históricos, análise adversarial, auditoria de confiança). Devem retornar ajustes não-nulos sob condições específicas auditáveis.

- **HistoricalAgent**: média histórica de gols na Copa é 2.64/jogo. Se `lambda_home + lambda_away > 3.0` (modelo prevê jogo aberto demais), aplica `adjustment_home = -0.05` (pressionar de volta à média). Se soma < 2.0, `adjustment_home = +0.04` (histórico sugere mais gols). Lógica simétrica para visitante via diferença de ELO.

- **RedTeamAgent**: se `elo_home - elo_away > 200` (favorito absoluto), adversarialmente sugere pequeno boost ao visitante: `adjustment_away = +0.06` (zebra histórica). Caso contrário, neutro.

- **ConfidenceAuditor**: se `prob_home > 0.70` (excesso de confiança no favorito da casa), aplica regressão à média: `adjustment_home = -0.05`. Se `prob_away > 0.70`, `adjustment_away = -0.05`. Caso contrário, neutro.

- [ ] **Step 1: Escrever testes com dados específicos**

Em `tests/test_agents.py`, adicionar:

```python
def test_historical_agent_reduces_home_when_lambdas_high():
    agent = HistoricalAgent()
    ctx = {**MATCH_CONTEXT, "lambda_home": 2.0, "lambda_away": 1.5}
    result = agent.analyze(ctx)
    assert result.adjustment_home < 0, "Lambda alto deve reduzir ajuste home"
    assert len(result.rationale) > 0


def test_historical_agent_increases_when_lambdas_low():
    agent = HistoricalAgent()
    ctx = {**MATCH_CONTEXT, "lambda_home": 0.8, "lambda_away": 0.9}
    result = agent.analyze(ctx)
    assert result.adjustment_home > 0, "Lambda baixo deve aumentar ajuste home"


def test_historical_agent_neutral_without_lambdas():
    agent = HistoricalAgent()
    result = agent.analyze(MATCH_CONTEXT)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0


def test_red_team_agent_boosts_underdog_when_elo_diff_high():
    agent = RedTeamAgent()
    ctx = {**MATCH_CONTEXT, "elo_home": 2000, "elo_away": 1750}
    result = agent.analyze(ctx)
    assert result.adjustment_away > 0, "Zebra com diff > 200 deve ter ajuste positivo"
    assert len(result.rationale) > 0


def test_red_team_agent_neutral_when_elo_close():
    agent = RedTeamAgent()
    ctx = {**MATCH_CONTEXT, "elo_home": 1800, "elo_away": 1780}
    result = agent.analyze(ctx)
    assert result.adjustment_away == 0.0


def test_confidence_auditor_reduces_home_when_overconfident():
    auditor = ConfidenceAuditor()
    ctx = {**MATCH_CONTEXT, "prob_home": 0.75, "prob_draw": 0.15, "prob_away": 0.10}
    result = auditor.analyze(ctx)
    assert result.adjustment_home < 0, "Excesso de confiança deve reduzir home"
    assert len(result.rationale) > 0


def test_confidence_auditor_neutral_for_balanced_game():
    auditor = ConfidenceAuditor()
    ctx = {**MATCH_CONTEXT, "prob_home": 0.40, "prob_draw": 0.30, "prob_away": 0.30}
    result = auditor.analyze(ctx)
    assert result.adjustment_home == 0.0
    assert result.adjustment_away == 0.0
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_agents.py::test_historical_agent_reduces_home_when_lambdas_high \
       tests/test_agents.py::test_red_team_agent_boosts_underdog_when_elo_diff_high \
       tests/test_agents.py::test_confidence_auditor_reduces_home_when_overconfident -v
```
Expected: FAIL.

- [ ] **Step 3: Implementar HistoricalAgent**

Substituir `src/agents/historical_agent.py`:

```python
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
```

- [ ] **Step 4: Implementar RedTeamAgent**

Substituir `src/agents/red_team_agent.py`:

```python
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
```

- [ ] **Step 5: Implementar ConfidenceAuditor**

Substituir `src/agents/confidence_auditor.py`:

```python
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
```

- [ ] **Step 6: Rodar todos os testes de agentes**

```bash
pytest tests/test_agents.py -v
```
Expected: todos PASS (incluindo os novos 7 testes).

- [ ] **Step 7: Commit**

```bash
git add src/agents/historical_agent.py src/agents/red_team_agent.py \
        src/agents/confidence_auditor.py tests/test_agents.py
git commit -m "feat(agents): historical, red_team, confidence_auditor retornam ajustes não-nulos"
```

---

## Task 4: Criar ContextEngine

**Files:**
- Create: `src/context_engine.py`
- Create: `tests/test_context_engine.py`

Contexto: O ContextEngine agrega os 8 agentes em um único `context_adjustment ∈ [-0.20, +0.20]`. Fórmula de agregação: para cada agente i com `weight_i` e resultado `confidence_i`, `adj_i = (adjustment_home_i - adjustment_away_i)`. O ajuste final é média ponderada por `weight_i * confidence_i`, depois clampado. Resultado positivo favorece a casa; negativo favorece o visitante.

```
context_adjustment = clamp(
    Σ(weight_i × confidence_i × (adj_home_i - adj_away_i)) / Σ(weight_i),
    -0.20, +0.20
)
```

- [ ] **Step 1: Escrever os testes**

Criar `tests/test_context_engine.py`:

```python
# tests/test_context_engine.py
import pytest

from src.context_engine import AgentContribution, ContextEngine, ContextEngineResult
from src.agents.historical_agent import HistoricalAgent
from src.agents.journalist_agent import JournalistAgent


FULL_CONTEXT = {
    "home_team": "Brazil",
    "away_team": "Serbia",
    "match_id": "GRP_E01",
    "stage": "group",
    "lambda_home": 1.8,
    "lambda_away": 0.9,
    "prob_home": 0.55,
    "prob_draw": 0.25,
    "prob_away": 0.20,
    "elo_home": 2060,
    "elo_away": 1800,
    "city": "Los Angeles",
}


def test_context_engine_returns_result_type():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert isinstance(result, ContextEngineResult)


def test_context_engine_result_has_required_fields():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert hasattr(result, "context_adjustment")
    assert hasattr(result, "agent_contributions")
    assert hasattr(result, "total_weight")


def test_context_adjustment_is_clamped():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert -0.20 <= result.context_adjustment <= 0.20


def test_agent_contributions_has_one_per_agent():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    assert len(result.agent_contributions) == 8


def test_agent_contribution_fields():
    engine = ContextEngine()
    result = engine.run(FULL_CONTEXT)
    for contrib in result.agent_contributions:
        assert isinstance(contrib, AgentContribution)
        assert hasattr(contrib, "agent_name")
        assert hasattr(contrib, "weight")
        assert hasattr(contrib, "confidence")
        assert hasattr(contrib, "adjustment_home")
        assert hasattr(contrib, "adjustment_away")
        assert hasattr(contrib, "rationale")
        assert hasattr(contrib, "effective_contribution")


def test_all_neutral_agents_give_zero_adjustment():
    """Com lambdas médias e probs equilibradas, agentes neutros somam a zero."""
    engine = ContextEngine()
    neutral_context = {
        "home_team": "A",
        "away_team": "B",
        "match_id": "GRP_X01",
        "stage": "group",
        "lambda_home": 1.3,
        "lambda_away": 1.2,
        "prob_home": 0.40,
        "prob_draw": 0.30,
        "prob_away": 0.30,
        "elo_home": 1800,
        "elo_away": 1790,
        "city": "Dallas",
    }
    result = engine.run(neutral_context)
    assert result.context_adjustment == pytest.approx(0.0, abs=0.001)


def test_high_elo_diff_produces_nonzero_adjustment():
    """Com diff ELO > 200, RedTeamAgent deve produzir ajuste não-nulo."""
    engine = ContextEngine()
    ctx = {**FULL_CONTEXT, "elo_home": 2100, "elo_away": 1750}
    result = engine.run(ctx)
    assert result.context_adjustment != 0.0


def test_overconfident_home_produces_negative_adjustment():
    """prob_home > 0.70 deve gerar ajuste negativo (regressão à média)."""
    engine = ContextEngine()
    ctx = {**FULL_CONTEXT, "prob_home": 0.75, "prob_draw": 0.15, "prob_away": 0.10}
    result = engine.run(ctx)
    assert result.context_adjustment < 0.0
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_context_engine.py -v
```
Expected: FAIL — `src/context_engine.py` não existe.

- [ ] **Step 3: Implementar ContextEngine**

Criar `src/context_engine.py`:

```python
# src/context_engine.py
from dataclasses import dataclass, field

from src.agents.base_agent import BaseAgent
from src.agents.confidence_auditor import ConfidenceAuditor
from src.agents.historical_agent import HistoricalAgent
from src.agents.journalist_agent import JournalistAgent
from src.agents.lineup_agent import LineupAgent
from src.agents.public_signal_agent import PublicSignalAgent
from src.agents.red_team_agent import RedTeamAgent
from src.agents.tactical_agent import TacticalAgent
from src.agents.weather_agent import WeatherAgent

ADJUSTMENT_MIN = -0.20
ADJUSTMENT_MAX = 0.20


@dataclass
class AgentContribution:
    agent_name: str
    weight: float
    confidence: float
    adjustment_home: float
    adjustment_away: float
    rationale: str
    effective_contribution: float


@dataclass
class ContextEngineResult:
    context_adjustment: float
    agent_contributions: list[AgentContribution] = field(default_factory=list)
    total_weight: float = 0.0


def _default_agents() -> list[BaseAgent]:
    return [
        JournalistAgent(),
        PublicSignalAgent(),
        LineupAgent(),
        WeatherAgent(),
        TacticalAgent(),
        HistoricalAgent(),
        RedTeamAgent(),
        ConfidenceAuditor(),
    ]


class ContextEngine:
    def __init__(self, agents: list[BaseAgent] | None = None):
        self.agents = agents if agents is not None else _default_agents()

    def run(self, context: dict) -> ContextEngineResult:
        contributions = []
        weighted_sum = 0.0
        weight_sum = 0.0

        for agent in self.agents:
            result = agent.analyze(context)
            directional = result.adjustment_home - result.adjustment_away
            effective = agent.weight * result.confidence * directional
            weighted_sum += effective
            weight_sum += agent.weight

            contributions.append(
                AgentContribution(
                    agent_name=agent.name,
                    weight=agent.weight,
                    confidence=result.confidence,
                    adjustment_home=result.adjustment_home,
                    adjustment_away=result.adjustment_away,
                    rationale=result.rationale,
                    effective_contribution=round(effective, 4),
                )
            )

        raw = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        clamped = max(ADJUSTMENT_MIN, min(ADJUSTMENT_MAX, raw))

        return ContextEngineResult(
            context_adjustment=round(clamped, 4),
            agent_contributions=contributions,
            total_weight=round(weight_sum, 4),
        )
```

- [ ] **Step 4: Rodar os testes**

```bash
pytest tests/test_context_engine.py -v
```
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/context_engine.py tests/test_context_engine.py
git commit -m "feat: criar ContextEngine — agrega 8 agentes em context_adjustment auditável"
```

---

## Task 5: Atualizar EnsembleModel — aplicar context_adjustment diretamente

**Files:**
- Modify: `src/models/ensemble_model.py`
- Modify: `tests/test_ensemble_model.py`

Contexto: A fórmula atual usa `self.weights.context * context_adjustment`, o que reduz o impacto máximo para 2% das lambdas. Para que os agentes influenciem o resultado de forma perceptível, o ajuste deve ser aplicado diretamente: `lh *= (1 + context_adjustment)`. Com `context_adjustment` máximo de ±0.20, o impacto máximo nas lambdas será de ±20%, o que é significativo e auditável.

- [ ] **Step 1: Escrever teste que verifica impacto do context_adjustment nas lambdas**

Em `tests/test_ensemble_model.py`, adicionar:

```python
def test_context_adjustment_positive_increases_home_lambda(ensemble):
    result_neutral = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    result_positive = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.10,
    )
    assert result_positive["lambda_home"] > result_neutral["lambda_home"]
    assert result_positive["lambda_away"] < result_neutral["lambda_away"]


def test_context_adjustment_negative_increases_away_lambda(ensemble):
    result_neutral = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    result_negative = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=-0.10,
    )
    assert result_negative["lambda_away"] > result_neutral["lambda_away"]
    assert result_negative["lambda_home"] < result_neutral["lambda_home"]


def test_context_adjustment_zero_has_no_effect(ensemble):
    r1 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
        context_adjustment=0.0,
    )
    r2 = ensemble.predict(
        home_team="A", away_team="B",
        elo_home=1800, elo_away=1750,
        attack_home=1.0, defense_home=1.0,
        attack_away=1.0, defense_away=1.0,
    )
    assert r1["lambda_home"] == r2["lambda_home"]
    assert r1["lambda_away"] == r2["lambda_away"]
```

- [ ] **Step 2: Rodar para verificar que os novos testes são significativos**

```bash
pytest tests/test_ensemble_model.py::test_context_adjustment_positive_increases_home_lambda -v
```
Expected: PASS já (fórmula atual funciona, só é fraca). Os testes passarão, mas verificaremos que a mudança de fórmula produz impacto maior.

- [ ] **Step 3: Atualizar fórmula no EnsembleModel**

Em `src/models/ensemble_model.py`, localizar as linhas:

```python
        lh = lh * (1 + self.weights.context * context_adjustment)
        la = la * (1 - self.weights.context * context_adjustment)
```

Substituir por:

```python
        lh = lh * (1 + context_adjustment)
        la = la * (1 - context_adjustment)
```

Também atualizar `model_contributions` para registrar o ajuste:

```python
            "model_contributions": {
                "elo_lambda": (round(lh_elo, 3), round(la_elo, 3)),
                "poisson_lambda": (round(lh_poi, 3), round(la_poi, 3)),
                "context_adjustment": context_adjustment,
                "lambda_after_context": (round(lh, 3), round(la, 3)),
            },
```

- [ ] **Step 4: Rodar todos os testes do ensemble**

```bash
pytest tests/test_ensemble_model.py -v
```
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/ensemble_model.py tests/test_ensemble_model.py
git commit -m "feat(ensemble): aplicar context_adjustment diretamente às lambdas (impacto ±20%)"
```

---

## Task 6: Adicionar agent_contributions ao PredictionRecord e ao relatório

**Files:**
- Modify: `src/history.py`
- Modify: `src/revision.py`
- Modify: `tests/test_revision.py`

Contexto: O relatório Markdown de cada revisão deve incluir uma seção "Contribuição dos Agentes" listando cada agente, seu ajuste, confiança, e rationale. `PredictionRecord` precisa de campo `agent_contributions` opcional para transportar esses dados até o relatório.

- [ ] **Step 1: Escrever testes para o relatório com seção de agentes**

Em `tests/test_revision.py`, adicionar (leia o arquivo primeiro para entender o padrão):

```python
def test_report_includes_agent_contributions_section(tmp_path):
    from src.history import HistoryStore, PredictionRecord
    from src.revision import RevisionManager

    store = HistoryStore(base_dir=tmp_path / "history")
    manager = RevisionManager(store=store, reports_dir=tmp_path / "reports")

    record = PredictionRecord(
        match_id="TEST01",
        mode="INITIAL",
        home_team="Brazil",
        away_team="Argentina",
        recommended_score=(2, 1),
        prob_home=0.45,
        prob_draw=0.27,
        prob_away=0.28,
        confidence="Moderada",
        lambda_home=1.5,
        lambda_away=1.2,
        top5_scores=[(2, 1, 0.12), (1, 0, 0.10), (2, 0, 0.09), (1, 1, 0.09), (3, 1, 0.07)],
        agent_contributions=[
            {
                "agent_name": "Historical World Cup Analyst",
                "weight": 0.06,
                "confidence": 0.7,
                "adjustment_home": -0.05,
                "adjustment_away": -0.05,
                "rationale": "xG acima da média histórica.",
                "effective_contribution": -0.0042,
            }
        ],
        context_adjustment=-0.02,
    )

    manager.save_revision(record)
    report_path = tmp_path / "reports" / "TEST01_INITIAL.md"
    content = report_path.read_text(encoding="utf-8")

    assert "## Contribuição dos Agentes" in content
    assert "Historical World Cup Analyst" in content
    assert "context_adjustment" in content.lower() or "Ajuste Final" in content
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_revision.py::test_report_includes_agent_contributions_section -v
```
Expected: FAIL — `PredictionRecord` não tem `agent_contributions` nem `context_adjustment`.

- [ ] **Step 3: Atualizar PredictionRecord em src/history.py**

Localizar a classe `PredictionRecord` e adicionar os campos novos **ao final da lista de campos** (antes do `timestamp`):

```python
@dataclass
class PredictionRecord:
    match_id: str
    mode: str
    home_team: str
    away_team: str
    recommended_score: tuple
    prob_home: float
    prob_draw: float
    prob_away: float
    confidence: str
    lambda_home: float
    lambda_away: float
    top5_scores: list
    notes: str = ""
    agent_contributions: list = field(default_factory=list)
    context_adjustment: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(TZ).isoformat(timespec="seconds"))

    def __post_init__(self):
        if self.mode not in MODES:
            raise ValueError(f"mode deve ser um de {MODES}, recebido: {self.mode}")
```

- [ ] **Step 4: Atualizar _write_report em src/revision.py**

Adicionar seção de agentes ao método `_write_report`. Localizar:

```python
## Notas
{record.notes or "—"}
"""
        path.write_text(content, encoding="utf-8")
```

Substituir pelo bloco final completo:

```python
## Notas
{record.notes or "—"}

## Contribuição dos Agentes

| Agente | Peso | Conf. | Adj. Casa | Adj. Visit. | Contribuição | Rationale |
|--------|------|-------|-----------|-------------|--------------|-----------|
{self._render_agent_table(record.agent_contributions)}

**Ajuste Final (context_adjustment):** {record.context_adjustment:+.4f}

**Impacto esperado no placar:**
- λ_casa × (1 + {record.context_adjustment:+.4f}) = {record.lambda_home * (1 + record.context_adjustment):.3f}
- λ_visit × (1 - {record.context_adjustment:+.4f}) = {record.lambda_away * (1 - record.context_adjustment):.3f}
"""
        path.write_text(content, encoding="utf-8")
```

E adicionar o método auxiliar na classe `RevisionManager`:

```python
    def _render_agent_table(self, contributions: list) -> str:
        if not contributions:
            return "| — | — | — | — | — | — | Nenhum agente registrado |"
        rows = []
        for c in contributions:
            rows.append(
                f"| {c['agent_name']} | {c['weight']:.2f} | {c['confidence']:.2f} "
                f"| {c['adjustment_home']:+.3f} | {c['adjustment_away']:+.3f} "
                f"| {c['effective_contribution']:+.4f} | {c['rationale']} |"
            )
        return "\n".join(rows)
```

- [ ] **Step 5: Rodar os testes de revisão**

```bash
pytest tests/test_revision.py -v
```
Expected: todos PASS.

- [ ] **Step 6: Commit**

```bash
git add src/history.py src/revision.py tests/test_revision.py
git commit -m "feat(revision): relatório inclui contribuição de agentes e impacto no placar"
```

---

## Task 7: Integrar ContextEngine no predict_match.py + corrigir contaminação de histórico

**Files:**
- Modify: `scripts/predict_match.py`
- Modify: `tests/test_predict_match.py`

Contexto: `predict_match.py` deve instanciar `ContextEngine`, construir o dict de contexto para cada partida (incluindo lambdas e probs de uma primeira rodada do modelo), executar o engine, passar `context_adjustment` ao `EnsembleModel.predict()` e salvar `agent_contributions` no `PredictionRecord`.

A contaminação ocorre porque os testes chamam `predict_match.py` via subprocess sem passar `--history-dir`, então o script escreve em `data/history/` (produção). Solução: adicionar argumento `--history-dir` ao CLI com default `data/history`.

- [ ] **Step 1: Escrever testes corrigidos**

Substituir o conteúdo de `tests/test_predict_match.py`:

```python
# tests/test_predict_match.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(*args):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "predict_match.py"), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result


def test_predict_all_runs_without_error(tmp_path):
    result = run_script("--all", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_single_match(tmp_path):
    result = run_script("--match-id", "GRP_E01", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert result.returncode == 0, f"STDERR: {result.stderr}"


def test_predict_output_contains_match_id(tmp_path):
    result = run_script("--match-id", "GRP_E01", "--mode", "INITIAL", "--history-dir", str(tmp_path))
    assert "GRP_E01" in result.stdout


def test_predict_unknown_match_exits():
    result = run_script("--match-id", "FAKE999", "--mode", "INITIAL")
    assert result.returncode != 0


def test_predict_no_args_exits():
    result = run_script()
    assert result.returncode != 0


def test_history_not_written_to_production_dir(tmp_path):
    """Testes não devem contaminar data/history/."""
    production_dir = ROOT / "data" / "history"
    files_before = set(production_dir.glob("*.jsonl")) if production_dir.exists() else set()

    run_script("--match-id", "GRP_A01", "--mode", "T_24H", "--history-dir", str(tmp_path))

    files_after = set(production_dir.glob("*.jsonl")) if production_dir.exists() else set()
    new_files = files_after - files_before
    assert len(new_files) == 0, f"Teste contaminou produção: {new_files}"
```

- [ ] **Step 2: Rodar para confirmar que test_history_not_written_to_production_dir falha**

```bash
pytest tests/test_predict_match.py::test_history_not_written_to_production_dir -v
```
Expected: FAIL — scripts escreve em `data/history/` sem `--history-dir`.

- [ ] **Step 3: Atualizar predict_match.py**

Substituir o conteúdo completo de `scripts/predict_match.py`:

```python
"""Entry-point CLI para geração e revisão de palpites."""

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.context_engine import ContextEngine
from src.history import HistoryStore, PredictionRecord
from src.models.ensemble_model import EnsembleModel
from src.revision import RevisionManager

DATA = ROOT / "data"
VALID_MODES = ("INITIAL", "T_24H", "T_2H", "T_1H", "FINAL")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = pd.read_csv(DATA / "matches.csv")
    teams = pd.read_csv(DATA / "teams.csv").set_index("team")
    return matches, teams


def predict_match(
    row: pd.Series,
    teams: pd.DataFrame,
    mode: str,
    model: EnsembleModel,
    context_engine: ContextEngine,
) -> PredictionRecord:
    home, away = row["home_team"], row["away_team"]

    if home not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {home}")
    if away not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {away}")

    th, ta = teams.loc[home], teams.loc[away]

    # Primeira rodada sem ajuste para obter lambdas/probs base (input para agentes)
    base_result = model.predict(
        home_team=home,
        away_team=away,
        elo_home=th["elo"],
        elo_away=ta["elo"],
        attack_home=th["attack_rating"],
        defense_home=th["defense_rating"],
        attack_away=ta["attack_rating"],
        defense_away=ta["defense_rating"],
        context_adjustment=0.0,
    )

    # Contexto rico para os agentes
    agent_context = {
        "home_team": home,
        "away_team": away,
        "match_id": row["match_id"],
        "stage": row.get("stage", "group"),
        "city": row.get("city", ""),
        "lambda_home": base_result["lambda_home"],
        "lambda_away": base_result["lambda_away"],
        "prob_home": base_result["prob_home"],
        "prob_draw": base_result["prob_draw"],
        "prob_away": base_result["prob_away"],
        "elo_home": float(th["elo"]),
        "elo_away": float(ta["elo"]),
    }

    engine_result = context_engine.run(agent_context)

    # Segunda rodada com ajuste real dos agentes
    result = model.predict(
        home_team=home,
        away_team=away,
        elo_home=th["elo"],
        elo_away=ta["elo"],
        attack_home=th["attack_rating"],
        defense_home=th["defense_rating"],
        attack_away=ta["attack_rating"],
        defense_away=ta["defense_rating"],
        context_adjustment=engine_result.context_adjustment,
    )

    contributions_dicts = [
        {
            "agent_name": c.agent_name,
            "weight": c.weight,
            "confidence": c.confidence,
            "adjustment_home": c.adjustment_home,
            "adjustment_away": c.adjustment_away,
            "rationale": c.rationale,
            "effective_contribution": c.effective_contribution,
        }
        for c in engine_result.agent_contributions
    ]

    notes = (
        f"EnsembleModel | xG {home}={result['lambda_home']} {away}={result['lambda_away']} "
        f"| context_adj={engine_result.context_adjustment:+.4f}"
    )

    return PredictionRecord(
        match_id=row["match_id"],
        mode=mode,
        home_team=home,
        away_team=away,
        recommended_score=result["recommended_score"],
        prob_home=result["prob_home"],
        prob_draw=result["prob_draw"],
        prob_away=result["prob_away"],
        confidence=result["confidence"],
        lambda_home=result["lambda_home"],
        lambda_away=result["lambda_away"],
        top5_scores=result["top5_scores"],
        notes=notes,
        agent_contributions=contributions_dicts,
        context_adjustment=engine_result.context_adjustment,
    )


def main():
    parser = argparse.ArgumentParser(description="Gerar palpite para partidas da Copa 2026")
    parser.add_argument("--all", action="store_true", help="Prever todas as partidas")
    parser.add_argument("--match-id", help="ID da partida (ex: GRP_E01)")
    parser.add_argument("--mode", default="INITIAL", choices=VALID_MODES)
    parser.add_argument(
        "--history-dir",
        default=str(DATA / "history"),
        help="Diretório para salvar histórico (default: data/history)",
    )
    args = parser.parse_args()

    if not args.all and not args.match_id:
        parser.error("Use --all ou --match-id MATCH_ID")

    matches, teams = load_data()
    model = EnsembleModel()
    context_engine = ContextEngine()
    history_dir = Path(args.history_dir)
    store = HistoryStore(base_dir=history_dir)
    reports_dir = ROOT / "reports" / "revision_history"
    revision_mgr = RevisionManager(store=store, reports_dir=reports_dir)

    if args.all:
        selected = matches[matches["stage"] == "group"]
    else:
        selected = matches[matches["match_id"] == args.match_id]
        if selected.empty:
            print(f"ERRO: match_id não encontrado: {args.match_id}", file=sys.stderr)
            sys.exit(1)

    records = []
    for _, row in selected.iterrows():
        try:
            record = predict_match(row, teams, args.mode, model, context_engine)
            diff = revision_mgr.compare_with_previous(record.match_id, record)
            if diff.get("score_changed"):
                record.notes += f" | MUDANÇA: {diff['previous_score']} → {record.recommended_score}"
            revision_mgr.save_revision(record)
            records.append(record)
            gh, ga = record.recommended_score
            print(
                f"{record.match_id} | {record.home_team} {gh}-{ga} {record.away_team} "
                f"| {record.confidence} | adj={record.context_adjustment:+.4f}"
            )
        except ValueError as e:
            print(f"AVISO: {e}", file=sys.stderr)

    print(f"\n{len(records)} palpite(s) gerado(s). Modo: {args.mode}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar todos os testes de integração**

```bash
pytest tests/test_predict_match.py -v
```
Expected: todos PASS — incluindo `test_history_not_written_to_production_dir`.

- [ ] **Step 5: Rodar suite completa**

```bash
pytest --tb=short -q
```
Expected: ≥ 70% cobertura, sem falhas.

- [ ] **Step 6: Commit**

```bash
git add scripts/predict_match.py tests/test_predict_match.py
git commit -m "feat: integrar ContextEngine ao predict_match.py; fix contaminação de histórico nos testes"
```

---

## Task 8: Remover arquivos legados e corrigir referências obsoletas

**Files:**
- Delete: `scripts/schedule_generator.py`
- Delete: `data/palpites.csv`
- Modify: `codex/automations.md`
- Modify: `workflows/previsao-inicial-fase-grupos.md`

Contexto: O audit report identificou 4 itens legados de v1. Não há testes para esses arquivos. A remoção é segura e não quebra nenhum teste existente.

- [ ] **Step 1: Verificar que não há imports de schedule_generator**

```bash
grep -r "schedule_generator" /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool/src /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool/tests /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool/scripts/predict_match.py 2>/dev/null
```
Expected: nenhuma saída.

- [ ] **Step 2: Deletar arquivos legados**

```bash
rm /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool/scripts/schedule_generator.py
rm /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool/data/palpites.csv
```

- [ ] **Step 3: Corrigir codex/automations.md**

Substituir o conteúdo de `codex/automations.md`:

```markdown
# Codex Automations

## Automação: previsão inicial

Prompt:
Execute `python scripts/predict_match.py --all --mode INITIAL`. Gere relatórios em `reports/` e atualize `data/history/`.

## Automação: revisão pré-jogo

Prompt:
Execute o workflow `workflows/revisao-pre-jogo.md` para o próximo jogo ainda não finalizado. Use horário de Brasília. Atualize `data/history/` e gere relatório em `reports/`.

## Automação: revisão sob demanda

Prompt:
Revise o jogo informado pelo usuário usando `workflows/revisao-sob-demanda.md`.

## Modos válidos

`INITIAL` | `T_24H` | `T_2H` | `T_1H` | `FINAL`

## Observação

Os horários específicos são gerados por `scripts/generate_automations.py` a partir de `data/matches.csv`.
```

- [ ] **Step 4: Corrigir workflows/previsao-inicial-fase-grupos.md**

Substituir o conteúdo de `workflows/previsao-inicial-fase-grupos.md`:

```markdown
# Workflow: Previsão Inicial da Fase de Grupos

## Objetivo
Gerar os primeiros palpites para todos os jogos cadastrados em `data/matches.csv`.

## Passos
1. Ler partidas de `data/matches.csv`.
2. Ler ratings de `data/teams.csv`.
3. Rodar EnsembleModel + ContextEngine (8 agentes).
4. Gerar placar recomendado com context_adjustment auditável.
5. Salvar histórico em `data/history/`.
6. Gerar relatórios em `reports/revision_history/`.

## Comando
```bash
python scripts/predict_match.py --all --mode INITIAL
```
```

- [ ] **Step 5: Rodar pytest para confirmar nada quebrou**

```bash
pytest --tb=short -q
```
Expected: todos PASS, sem referência a arquivos deletados.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remover schedule_generator.py e palpites.csv legados; corrigir referências obsoletas"
```

---

## Task 9: Criar docs/V3_1_IMPLEMENTATION_REPORT.md e push final

**Files:**
- Create: `docs/V3_1_IMPLEMENTATION_REPORT.md`

Contexto: Relatório final que documenta o que foi implementado, as decisões de arquitetura, e o estado atual do projeto pós-V3.1.

- [ ] **Step 1: Rodar suite completa e coletar métricas**

```bash
cd /Users/lucianooliveira/Documents/luciusjazz-worldcup-ai-pool
source .venv/bin/activate
pytest --tb=short -q 2>&1 | tail -20
```
Anotar: número de testes, cobertura.

- [ ] **Step 2: Criar o relatório**

Criar `docs/V3_1_IMPLEMENTATION_REPORT.md` com o seguinte conteúdo (substituindo `[N]` pelos valores reais):

```markdown
# V3.1 — Implementation Report

**Data:** 2026-06-10
**Status:** Completo

## Objetivo

Integrar efetivamente os 8 agentes ao fluxo de predição, tornando suas contribuições auditáveis no relatório final.

## O que foi implementado

### 1. AgentResult expandido
Cada agente agora retorna 3 campos adicionais:
- `adjustment_home: float` — ajuste direcional para o mandante (−1.0 a +1.0)
- `adjustment_away: float` — ajuste direcional para o visitante (−1.0 a +1.0)
- `rationale: str` — explicação de uma linha do ajuste aplicado

### 2. Agentes com ajuste neutro (5 agentes)
JournalistAgent, PublicSignalAgent, LineupAgent, WeatherAgent e TacticalAgent retornam `adjustment=0.0` com rationale explicando a ausência de dados. Isso é auditável e honesto.

### 3. Agentes com ajuste real (3 agentes)
| Agente | Lógica | Ajuste máximo |
|--------|--------|---------------|
| HistoricalAgent | Se xG total > 3.0: regressão. Se < 2.0: boost. | ±0.05 |
| RedTeamAgent | Se diff ELO > 200: boost adversarial ao underdog. | +0.06 |
| ConfidenceAuditor | Se prob > 70%: regressão à média. | −0.05 |

### 4. ContextEngine (novo)
Agrega os 8 agentes em um único escalar `context_adjustment ∈ [−0.20, +0.20]` via média ponderada por `agent.weight × result.confidence`. Retorna `ContextEngineResult` com contribuições individuais auditáveis.

### 5. EnsembleModel — aplicação direta
`context_adjustment` é aplicado diretamente às lambdas:
```
λ_casa_final = λ_casa_base × (1 + context_adjustment)
λ_visit_final = λ_visit_base × (1 − context_adjustment)
```
Impacto máximo: ±20% nas lambdas (era ±2% antes).

### 6. predict_match.py — fluxo de duas rodadas
1. Rodada base (context_adjustment=0.0) para obter lambdas/probs como input dos agentes
2. ContextEngine processa os 8 agentes
3. Rodada final com context_adjustment real

### 7. Relatório de revisão enriquecido
Cada `.md` em `reports/revision_history/` inclui:
- Tabela de contribuições por agente
- Ajuste final (context_adjustment)
- Impacto esperado nas lambdas pós-ajuste

### 8. Correção de contaminação de histórico
`predict_match.py` aceita `--history-dir` arg. Testes usam `tmp_path` do pytest — histórico de produção (`data/history/`) não é mais contaminado por testes.

### 9. Limpeza de legados
Removidos:
- `scripts/schedule_generator.py` (duplicado de generate_automations.py)
- `data/palpites.csv` (v1, não utilizado)

Corrigidos:
- `codex/automations.md` — modo `initial` → `INITIAL`
- `workflows/previsao-inicial-fase-grupos.md` — referência atualizada

## Métricas

- **Testes:** [N] passando
- **Cobertura:** [N]%
- **Agentes integrados:** 8/8
- **Agentes com ajuste não-nulo:** 3/8 (HistoricalAgent, RedTeamAgent, ConfidenceAuditor)
- **Agentes com ajuste neutro + rationale:** 5/8 (placeholder honesto)

## Limitações conhecidas (para V3.2+)

- Agentes com ajuste neutro precisam de dados externos reais (odds, escalações, clima) para produzir ajustes significativos.
- `HOME_ADVANTAGE=1.12` ainda inadequado para Copa (campo neutro) — DT-11.
- Monte Carlo e Dixon-Coles ainda compartilham as mesmas lambdas — DT-06.
- Sem mecanismo de atualização de ELO durante o torneio — DT-05.
```

- [ ] **Step 3: Commit e push**

```bash
git add docs/V3_1_IMPLEMENTATION_REPORT.md
git commit -m "docs: V3_1_IMPLEMENTATION_REPORT — integração real dos agentes ao fluxo de predição"
git push origin main
```

---

## Self-Review

### 1. Spec coverage

| Requisito | Task que implementa |
|-----------|---------------------|
| Criar ContextEngine | Task 4 |
| Cada agente retorna adjustment_home, adjustment_away, confidence, rationale | Tasks 1-3 |
| ContextEngine combina agentes em context_adjustment [-0.20, +0.20] | Task 4 |
| context_adjustment altera lambdas do EnsembleModel | Task 5 |
| Relatório registra contribuição por agente, ajuste e impacto no placar | Task 6 |
| Corrigir contaminação de data/history nos testes | Task 7 |
| Remover scripts e documentação legados | Task 8 |
| Criar V3_1_IMPLEMENTATION_REPORT.md | Task 9 |

Cobertura: 100%.

### 2. Placeholder scan

Nenhum "TBD", "TODO", "implement later" encontrado. Todos os steps têm código completo.

### 3. Type consistency

- `AgentResult.adjustment_home` — definido em Task 1, usado em Tasks 2, 3, 4 ✅
- `AgentContribution` — definido em Task 4, referenciado em Task 6 ✅
- `ContextEngineResult.context_adjustment` — definido em Task 4, usado em Tasks 5, 7 ✅
- `PredictionRecord.agent_contributions` — definido em Task 6, populado em Task 7 ✅
- `PredictionRecord.context_adjustment` — definido em Task 6, populado em Task 7 ✅
