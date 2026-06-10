# CLAUDE.md — Instruções para Claude Code

## Objetivo do projeto

Assistente recreativo para bolão da Copa do Mundo FIFA 2026 ("Entre Amigos"). Gera e revisa palpites de placar usando modelos estatísticos e agentes especializados.

> **Não realiza apostas nem recomendações financeiras.**

## Estrutura

```
src/models/         # EloModel, PoissonModel, DixonColesModel, MonteCarloSimulation, EnsembleModel
src/agents/         # 8 agentes com interface AgentResult(findings, confidence, recommendations)
src/history.py      # HistoryStore — salva JSONL em data/history/<match_id>.jsonl
src/evaluation.py   # Evaluator — 7 categorias de pontuação do bolão Entre Amigos
src/revision.py     # RevisionManager — compara revisões, gera reports/revision_history/*.md
data/teams.csv      # 48 seleções com ELO, attack_rating, defense_rating
data/matches.csv    # 72 partidas fase de grupos (datas placeholder)
scripts/predict_match.py  # CLI principal
```

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Previsão inicial de todos os jogos
python scripts/predict_match.py --all --mode INITIAL

# Revisão T-24h de um jogo
python scripts/predict_match.py --match-id GRP_E01 --mode T_24H

# Gerar agenda de revisões
python scripts/generate_automations.py

# Testes
pytest
```

## Modos válidos

`INITIAL` | `T_24H` | `T_2H` | `T_1H` | `FINAL`

## Pontuação do bolão

1. Placar Exato = 25pts
2. Vencedor + gols vencedor = 18pts
3. Vencedor + saldo = 15pts
4. Qualquer empate = 15pts
5. Vencedor + gols perdedor = 12pts
6. Vencedor = 10pts
7. Gols de algum time = 5pts

## Princípios obrigatórios

1. Não inventar lesões, escalações, notícias ou dados.
2. Registrar fontes quando houver coleta externa.
3. Declarar incerteza quando a informação for fraca ou contraditória.
4. Usar horário `America/Sao_Paulo`.
5. Priorizar placares plausíveis: `0-0, 1-0, 1-1, 2-0, 2-1`.
