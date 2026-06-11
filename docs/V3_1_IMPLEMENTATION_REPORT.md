# V3.1 — Implementation Report

**Data:** 2026-06-10
**Status:** Completo
**Cobertura:** 97.94% | **Testes:** 103 passando

---

## Objetivo

Integrar efetivamente os 8 agentes ao fluxo de predição, tornando suas contribuições auditáveis no relatório final. Corrigir contaminação de histórico nos testes. Remover arquivos legados.

---

## O que foi implementado

### 1. AgentResult expandido (Task 1)

Cada agente retorna 3 campos adicionais com defaults seguros (retrocompatível):

```python
adjustment_home: float = 0.0   # ajuste direcional para o mandante
adjustment_away: float = 0.0   # ajuste direcional para o visitante
rationale: str = ""            # explicação de uma linha
```

### 2. Agentes com ajuste neutro — 5 agentes (Task 2)

`JournalistAgent`, `PublicSignalAgent`, `LineupAgent`, `WeatherAgent` e `TacticalAgent` retornam `adjustment=0.0` com `rationale` explicando a ausência de dados. Honesto e auditável.

### 3. Agentes com ajuste real — 3 agentes (Task 3)

| Agente | Lógica | Ajuste máximo |
|--------|--------|---------------|
| `HistoricalAgent` | xG total > 3.0 → regressão (−0.05); xG total < 2.0 → boost (+0.04) | ±0.05 |
| `RedTeamAgent` | diff ELO > 200 → boost adversarial ao underdog (+0.06) | +0.06 |
| `ConfidenceAuditor` | prob > 70% → regressão à média (−0.05) | −0.05 |

Todas as constantes são nomeadas (`AVG_GOALS_PER_GAME`, `ELO_DIFF_THRESHOLD`, `OVERCONFIDENCE_THRESHOLD`). Zero magic numbers.

### 4. ContextEngine — novo módulo (Task 4)

`src/context_engine.py` agrega os 8 agentes em um único escalar auditável:

```
context_adjustment = clamp(
    Σ(weight_i × confidence_i × (adj_home_i − adj_away_i)) / Σ(weight_i),
    −0.20, +0.20
)
```

Retorna `ContextEngineResult` com lista completa de `AgentContribution` por agente.

### 5. EnsembleModel — aplicação direta (Task 5)

`context_adjustment` é agora aplicado diretamente às lambdas:

```python
# Antes (impacto ≈ ±2%)
lh = lh * (1 + self.weights.context * context_adjustment)

# Depois (impacto ≈ ±20%)
lh = lh * (1 + context_adjustment)
la = la * (1 - context_adjustment)
```

`model_contributions` inclui `lambda_after_context` para rastreabilidade completa.

### 6. PredictionRecord e relatório enriquecidos (Task 6)

Dois novos campos no `PredictionRecord`:
- `agent_contributions: list` — lista de dicts com contribuição de cada agente
- `context_adjustment: float` — valor final aplicado

Cada relatório Markdown em `reports/revision_history/` inclui:

```markdown
## Contribuição dos Agentes

| Agente | Peso | Conf. | Adj. Casa | Adj. Visit. | Contribuição | Rationale |
|--------|------|-------|-----------|-------------|--------------|-----------|
| Red Team Agent | 0.05 | 0.50 | +0.000 | +0.060 | -0.0030 | Diff ELO=250 → boost ao visitante |
...

**Ajuste Final (context_adjustment):** -0.0030

**Impacto esperado no placar:**
- λ_casa × (1 + -0.0030) = 1.474
- λ_visit × (1 - -0.0030) = 1.063
```

### 7. Fluxo de duas rodadas no predict_match.py (Task 7)

```
1. Rodada base (context_adjustment=0.0)
   → obtém lambda_home, lambda_away, prob_home, prob_draw, prob_away

2. ContextEngine processa os 8 agentes com contexto completo
   → retorna context_adjustment e agent_contributions

3. Rodada final (context_adjustment real)
   → placar e probabilidades com influência dos agentes
```

Output do CLI agora inclui o ajuste aplicado:
```
GRP_A01 | USA 1-0 Panama | Moderada | adj=+0.0000
GRP_B01 | Argentina 2-0 Morocco | Alta | adj=-0.0023
```

### 8. Correção de contaminação de histórico (Task 7)

`predict_match.py` aceita `--history-dir` (default: `data/history`). Todos os testes passam `--history-dir tmp_path` via `pytest`'s `tmp_path` fixture. O diretório `data/history/` de produção não é mais modificado por `pytest`.

### 9. Limpeza de legados (Task 8)

**Removidos:**
- `scripts/schedule_generator.py` — duplicado de `generate_automations.py`
- `data/palpites.csv` — arquivo v1 não utilizado

**Corrigidos:**
- `codex/automations.md` — modo `initial` → `INITIAL`
- `workflows/previsao-inicial-fase-grupos.md` — referências e comando atualizados

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Testes passando | 103 |
| Cobertura de testes | 97.94% |
| Agentes integrados ao fluxo | 8/8 |
| Agentes com ajuste não-nulo | 3/8 |
| Agentes com ajuste neutro auditável | 5/8 |
| Arquivos legados removidos | 2 |
| APIs externas adicionadas | 0 |

---

## Limitações conhecidas (para V3.2+)

| ID | Limitação | Impacto |
|----|-----------|---------|
| DT-01b | 5 agentes placeholder retornam `adj=0.0` — precisam de dados externos (odds, escalações, clima) para produzir ajustes significativos | Médio |
| DT-05 | Sem atualização de ratings ELO durante o torneio | Alto |
| DT-06 | Monte Carlo e Dixon-Coles compartilham as mesmas lambdas (não são fontes independentes) | Médio |
| DT-11 | `HOME_ADVANTAGE=1.12` inadequado para Copa (todos os jogos em campo neutro) | Médio |
| BUG-001 | Dixon-Coles pode gerar fator negativo com lambdas extremas (> 3.0, rho=0.10) — não ativado com dados reais | Baixo |

---

## Arquitetura V3.1

```
predict_match.py
  ↓ load_data()
  ↓ EnsembleModel.predict(context_adjustment=0.0)  ← rodada base
  ↓ ContextEngine.run(agent_context)
      ├── JournalistAgent     (w=0.12, adj=0.0)
      ├── PublicSignalAgent   (w=0.12, adj=0.0)
      ├── LineupAgent         (w=0.10, adj=0.0)
      ├── WeatherAgent        (w=0.05, adj=0.0)
      ├── TacticalAgent       (w=0.10, adj=0.0)
      ├── HistoricalAgent     (w=0.06, adj=f(xG))
      ├── RedTeamAgent        (w=0.05, adj=f(ELO))
      └── ConfidenceAuditor   (w=0.05, adj=f(prob))
  ↓ context_adjustment ∈ [-0.20, +0.20]
  ↓ EnsembleModel.predict(context_adjustment=real)  ← rodada final
  ↓ PredictionRecord(agent_contributions, context_adjustment)
  ↓ RevisionManager.save_revision()
      ├── data/history/<match_id>.jsonl
      └── reports/revision_history/<match_id>_<mode>.md
```
