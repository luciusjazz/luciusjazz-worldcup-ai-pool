# Workflow: Previsão Inicial da Fase de Grupos

## Objetivo
Gerar os primeiros palpites para todos os jogos cadastrados em `data/jogos_fase_grupos.csv`.

## Passos
1. Ler jogos.
2. Ler ratings.
3. Rodar modelo estatístico.
4. Gerar placar recomendado.
5. Salvar em `data/palpites.csv`.
6. Gerar relatório em `reports/`.

## Comando
```bash
python scripts/predict_match.py --all --mode initial
```
