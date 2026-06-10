# luciusjazz-worldcup-ai-pool

Projeto recreativo para organizar palpites de bolão da Copa do Mundo FIFA 2026 usando agentes de IA, notícias públicas, contexto esportivo e modelos estatísticos simples.

## Objetivo

Gerar, revisar e documentar palpites de placar para cada jogo, com:
- previsão inicial;
- revisão T-24h;
- revisão T-2h;
- revisão T-1h;
- revisão sob demanda.

## Estrutura

```text
AGENTS.md
skills/
workflows/
data/
scripts/
reports/
codex/
docs/
```

## Como começar

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python scripts/predict_match.py --all
```

No Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\predict_match.py --all
```

## Uso recreativo

Este projeto não promete acerto. Ele serve para organizar raciocínio, fontes e revisão de palpites de bolão.
