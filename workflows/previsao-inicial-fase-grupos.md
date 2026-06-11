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
