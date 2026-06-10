# Prompt de Inicialização — Codex e Claude Code

Você está trabalhando no repositório `luciusjazz/luciusjazz-worldcup-ai-pool`.

> **Claude Code**: leia também `CLAUDE.md` na raiz do projeto.  
> **Codex**: leia também `AGENTS.md` e os arquivos em `codex/`.

## Tarefa inicial

1. Verifique a estrutura do projeto lendo `CLAUDE.md` (Claude Code) ou `AGENTS.md` + `codex/automations.md` (Codex).
2. Rode os testes básicos:
   ```bash
   python scripts/predict_match.py --all
   python scripts/schedule_generator.py
   ```
3. Se houver erro, corrija.
4. Faça commit das alterações.
5. Prepare o projeto para automações recorrentes da Copa do Mundo 2026.

## Objetivo do projeto

Criar um assistente recreativo para bolão da Copa, com agentes especializados (ver `skills/`) e modelo estatístico simples (Poisson duplo).

## Regras

- Não inventar notícias ou dados.
- Registrar fontes quando houver coleta online.
- Manter separação entre modelo estatístico, sinais públicos e julgamento contextual.
- Priorizar placares plausíveis.
- Usar horário America/Sao_Paulo para revisões.

## Arquivos de configuração por ferramenta

| Ferramenta   | Arquivo principal |
|-------------|-------------------|
| Claude Code | `CLAUDE.md`       |
| Codex       | `AGENTS.md`       |
| Ambos       | `skills/`, `workflows/`, `data/`, `scripts/` |
