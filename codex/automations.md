# Codex Automations

## Automação: previsão inicial

Prompt:
Execute `python scripts/predict_match.py --all --mode initial`. Gere relatórios em `reports/` e atualize `data/palpites.csv`.

## Automação: revisão pré-jogo

Prompt:
Execute o workflow `workflows/revisao-pre-jogo.md` para o próximo jogo ainda não finalizado. Use horário de Brasília. Atualize `data/palpites.csv` e gere relatório em `reports/`.

## Automação: revisão sob demanda

Prompt:
Revise o jogo informado pelo usuário usando `workflows/revisao-sob-demanda.md`.

## Observação

Os horários específicos devem ser gerados por `scripts/schedule_generator.py` a partir de `data/jogos_fase_grupos.csv`.
