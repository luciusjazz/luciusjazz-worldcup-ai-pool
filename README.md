# luciusjazz-worldcup-ai-pool

Projeto recreativo para palpites de bolão da Copa do Mundo FIFA 2026 usando agentes de IA e modelos estatísticos.

> **Uso recreativo.** Este projeto não realiza apostas nem recomendações financeiras.

## Bolão "Entre Amigos"

Pontuação do app **Entre Amigos**:

| # | Categoria | Pontos | Exemplo |
|---|-----------|--------|---------|
| 1 | Placar Exato | 25 | Palpitou 2x1, terminou 2x1 |
| 2 | Vencedor + gols do vencedor | 18 | Palpitou 2x1, terminou 2x0 |
| 3 | Vencedor + saldo de gols | 15 | Palpitou 2x1, terminou 1x0 |
| 4 | Acertou Empate | 15 | Palpitou 2x2, terminou 1x1 |
| 5 | Vencedor + gols do perdedor | 12 | Palpitou 2x0, terminou 3x0 |
| 6 | Vencedor | 10 | Palpitou 2x0, terminou 3x2 |
| 7 | Gols de algum time | 5 | Palpitou 3x0, terminou 0x0 |

## Estrutura

```text
src/
  models/         # EloModel, PoissonModel, DixonColes, MonteCarlo, EnsembleModel
  agents/         # 8 agentes especializados com interface padronizada
  history.py      # HistoryStore — JSONL por partida
  evaluation.py   # Métricas: pontuação real do bolão Entre Amigos
  revision.py     # RevisionManager — comparação entre revisões
data/
  teams.csv       # 48 seleções com ELO e ratings
  matches.csv     # 72 partidas fase de grupos (placeholder de datas)
  history/        # Histórico de previsões por partida (.jsonl)
  automation_schedule.csv
scripts/
  predict_match.py            # CLI principal
  generate_automations.py     # Gera agenda de revisões
  import_worldcup_schedule.py # Valida/importa calendário oficial
reports/
  revision_history/           # Relatórios Markdown por revisão
tests/                        # pytest, cobertura 98%
```

## Como começar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Previsão inicial — todos os jogos
python scripts/predict_match.py --all --mode INITIAL

# Previsão de um jogo específico
python scripts/predict_match.py --match-id GRP_E01 --mode T_24H

# Gerar agenda de automações
python scripts/generate_automations.py

# Validar calendário
python scripts/import_worldcup_schedule.py

# Testes
pytest
```

## Modelos estatísticos

| Modelo | Peso | Descrição |
|--------|------|-----------|
| Elo | 40% | Ratings Elo com distribuição Poisson |
| Poisson | 30% | Poisson clássico com vantagem de campo |
| Dixon-Coles | 20% | Ajuste para placares baixos (0-0, 1-0) |
| Contexto | 10% | Ajuste manual contextual |

## Agentes

| Agente | Peso |
|--------|------|
| Estatístico Profissional (EnsembleModel) | 35% |
| Jornalista Esportivo | 12% |
| Analista de Sinais Públicos | 12% |
| Scout Tático | 10% |
| Especialista em Escalações | 10% |
| Historical World Cup Analyst | 6% |
| Meteorologista | 5% |
| Red Team Agent | 5% |
| Auditor de Confiança | 5% |

## Modos de revisão

`INITIAL` → `T_24H` → `T_2H` → `T_1H` → `FINAL`

## Regras

- Não inventar dados, escalações ou notícias.
- Registrar fontes.
- Separar fato, inferência e especulação.
- Usar horário `America/Sao_Paulo`.
