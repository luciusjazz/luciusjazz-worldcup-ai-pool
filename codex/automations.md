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
