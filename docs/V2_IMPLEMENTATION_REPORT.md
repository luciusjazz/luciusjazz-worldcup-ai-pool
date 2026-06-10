# V2_IMPLEMENTATION_REPORT.md

**Data:** 2026-06-10
**Versão:** 2.0.0

## O que foi alterado

### Dados
- `data/teams.csv`: 48 seleções reais com ELO, FIFA ranking, confederation, attack/defense rating.
- `data/matches.csv`: 72 partidas da fase de grupos com times, grupos e sedes reais.
- `data/history/`: histórico de previsões em JSONL por partida.
- `data/automation_schedule.csv`: agenda T-24H, T-2H, T-1H para 216 tarefas.

### Modelos
- `src/models/elo_model.py`: Elo com distribuição Poisson (peso 40%).
- `src/models/poisson_model.py`: Poisson clássico com home advantage 1.12 (peso 30%).
- `src/models/dixon_coles.py`: correção para placares baixos ρ=0.10 (peso 20%).
- `src/models/monte_carlo.py`: simulação Monte Carlo 10.000 runs com numpy RNG.
- `src/models/ensemble_model.py`: pesos 40/30/20/10, configuráveis via `ModelWeights`.

### Agentes
- 8 agentes em `src/agents/` com interface `AgentResult(findings, confidence, recommendations)`.
- `BaseAgent` como ABC — todos os agentes são testáveis e substituíveis.

### Infraestrutura
- `src/history.py`: `HistoryStore` salva JSONL por partida com múltiplas revisões.
- `src/evaluation.py`: `Evaluator` com 7 categorias hierárquicas do bolão "Entre Amigos".
- `src/revision.py`: `RevisionManager` compara revisões e gera relatórios Markdown.
- `scripts/predict_match.py`: refatorado, usa `EnsembleModel` + `RevisionManager`.
- `scripts/generate_automations.py`: agenda 216 tarefas para 72 partidas.
- `scripts/import_worldcup_schedule.py`: valida e orienta importação do calendário oficial.

### Qualidade
- `pyproject.toml` com ruff, black, pytest-cov.
- 74 testes com cobertura 98.96%.
- `.pre-commit-config.yaml` com ruff + black.

## Arquitetura final

```
scripts/predict_match.py
  └── src/models/ensemble_model.py
        ├── EloModel (40%)
        ├── PoissonModel (30%)
        ├── DixonColesModel (20%)
        └── MonteCarloSimulation
  └── src/revision.py (RevisionManager)
        └── src/history.py (HistoryStore → data/history/<id>.jsonl)
              └── reports/revision_history/<id>_<mode>.md

src/evaluation.py (Evaluator)
  └── 7 categorias hierárquicas do bolão "Entre Amigos"
```

## Pontuação do bolão implementada

| Categoria | Pontos | Lógica |
|-----------|--------|--------|
| Placar Exato | 25 | ph==rh AND pa==ra |
| Vencedor + gols vencedor | 18 | winner_correct AND winner_goals_match |
| Vencedor + saldo | 15 | winner_correct AND (ph-pa)==(rh-ra) |
| Qualquer empate | 15 | pred_draw AND actual_draw |
| Vencedor + gols perdedor | 12 | winner_correct AND loser_goals_match |
| Vencedor | 10 | winner_correct |
| Gols de algum time | 5 | ph==rh OR pa==ra |

## Pendências conhecidas

1. **Calendário oficial**: `data/matches.csv` usa datas/horários placeholder. Atualizar quando FIFA publicar.
2. **ELO em tempo real**: ratings estáticos — precisam ser atualizados durante o torneio.
3. **Agentes com dados reais**: agentes retornam findings genéricos; integração com APIs de notícias/odds está fora do escopo recreativo.
4. **Fase knockout**: `data/matches.csv` contém apenas fase de grupos.
5. **Mali**: está em `teams.csv` mas não tem partida na fase de grupos (grupo a confirmar).

## Sugestões para v3

- Integrar API pública de futebol (football-data.org) para atualizar ELO e notícias.
- Adicionar `streamlit` dashboard para visualização dos palpites e pontuação acumulada.
- Implementar update automático de placares reais para avaliação pós-jogo.
- Adicionar jogos das fases eliminatórias quando os classificados forem conhecidos.
- Implementar `CalibrationPlot` para avaliar qualidade probabilística do modelo.
- Automatizar via GitHub Actions com schedule dos horários T_24H/T_2H/T_1H.
