# Workflow: Revisão Pré-Jogo

## Objetivo
Revisar o palpite antes da partida.

## Janelas
- T-24h
- T-2h
- T-1h
- sob demanda

## Passos
1. Atualizar notícias.
2. Atualizar sinais públicos.
3. Verificar escalações.
4. Rodar modelo.
5. Comparar com palpite anterior.
6. Salvar nova versão.

## Comando
```bash
python scripts/predict_match.py --match-id MATCH001 --mode pregame
```
