# CLAUDE.md — Instruções para Claude Code

## Objetivo do projeto

Assistente recreativo para bolão da Copa do Mundo FIFA 2026. Gera e revisa palpites de placar usando agentes especializados, fontes públicas e modelo estatístico simples (Poisson).

## Estrutura

```
AGENTS.md          # Descrição dos agentes e pesos (lido por Codex e Claude)
CLAUDE.md          # Este arquivo — instruções específicas para Claude Code
skills/            # Personas dos agentes especializados
workflows/         # Sequências de revisão (inicial, T-24h, T-2h, sob demanda)
data/              # CSVs de jogos, ratings e palpites
scripts/           # predict_match.py, schedule_generator.py
reports/           # Relatórios gerados (Markdown por jogo)
docs/              # Documentação e prompts de referência
codex/             # Automações para Codex (equivalente a este arquivo)
```

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Previsão inicial para todos os jogos
python scripts/predict_match.py --all --mode initial

# Previsão de um jogo específico
python scripts/predict_match.py --match-id MATCH001 --mode review

# Gerar agenda de revisões
python scripts/schedule_generator.py
```

## Tarefas comuns

- **Previsão inicial**: rodar `predict_match.py --all --mode initial`
- **Revisão pré-jogo**: seguir `workflows/revisao-pre-jogo.md` para o próximo jogo
- **Revisão sob demanda**: seguir `workflows/revisao-sob-demanda.md`
- **Ver agentes disponíveis**: ler arquivos em `skills/`

## Princípios obrigatórios

1. Não inventar lesões, escalações, notícias ou dados.
2. Registrar fontes quando houver coleta de informação externa.
3. Declarar incerteza quando a informação for fraca, antiga ou contraditória.
4. Separar fato, inferência e especulação.
5. Usar horário `America/Sao_Paulo` para agendamento de revisões.
6. Priorizar placares plausíveis para bolão: `0-0, 1-0, 1-1, 2-0, 2-1, 1-2, 0-1, 2-2, 3-1`.

## Agentes (skills/)

Cada arquivo em `skills/` define uma persona. O **Gerente de Palpite** consolida todos e emite o palpite final seguindo o formato em `AGENTS.md`.

## Formato de saída esperado

Ver seção "Formato final" em `AGENTS.md`.
