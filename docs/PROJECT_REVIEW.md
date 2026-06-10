# PROJECT_REVIEW.md — Auditoria WorldCup AI Pool v1

**Data:** 2026-06-10  
**Revisor:** Claude Code (automatizado)

---

## Pontos Fortes

- Separação clara entre skills (agentes), workflows e scripts.
- Modelo Poisson duplo com distribuição de placares implementado corretamente.
- `recommend_score` prioriza placares plausíveis de bolão (lista `COMMON_SCORES`).
- `confidence_label` com três níveis razoáveis.
- Agenda de revisões com cron hints gerada automaticamente.
- Documentação de agentes em Markdown legível por humanos e LLMs.
- `.gitignore` adequado.

---

## Pontos Fracos

### Dados
- `data/team_ratings.csv`: 4 times fictícios ("Time A/B/C/D") sem dados reais.
- `data/jogos_fase_grupos.csv`: 2 partidas fictícias sem datas, locais ou grupos reais.
- Sem separação entre `elo`, `attack_rating` e `defense_rating` com fonte documentada.
- Ausência de `fifa_ranking`, `confederation`, `fifa_code`.

### Modelo estatístico
- Poisson simples sem ajuste Dixon-Coles para placares baixos (0-0, 1-0).
- Sem Monte Carlo para propagação de incerteza.
- Parâmetros `base=1.25` e `elo_diff * 0.18` hardcoded sem justificativa.
- `score_distribution` normaliza manualmente — pode acumular erro de arredondamento.
- `observacoes` inclui objeto `np.float64` como string (feio em CSV).

### Agentes
- Agentes existem apenas como arquivos Markdown descritivos.
- Nenhum agente retorna estrutura de dados programática.
- Sem integração entre agentes e modelo estatístico.

### Histórico e avaliação
- Previsões acumuladas em `palpites.csv` sem versionamento por revisão.
- Sem métricas de avaliação retroativa (acerto de vencedor, erro de gols).
- Sem comparação automática entre revisões do mesmo jogo.

### Qualidade de código
- Sem testes automatizados.
- Sem linter (ruff) nem formatter (black).
- Sem pre-commit hooks.
- `predict_match.py` mistura I/O, lógica de modelo e formatação de relatório.
- `write_report` hardcoded em `predict_match.py` — difícil de reusar.

### Escalabilidade
- Sistema inteiro em dois scripts monolíticos.
- Sem pacote `src/` — imports relativos impossíveis entre scripts.
- `palpites.csv` usa `pd.concat` sem deduplicação (cria duplicatas se rodar duas vezes).
- `schedule_generator.py` recria o CSV completo a cada execução.

---

## Melhorias Recomendadas

1. Criar pacote `src/` com modelos e agentes como módulos Python.
2. Substituir dados fictícios por 48 seleções reais da Copa 2026.
3. Implementar Dixon-Coles e Monte Carlo.
4. Formalizar agentes como classes Python com interface padronizada.
5. Criar sistema de histórico com versionamento por revisão.
6. Adicionar métricas de avaliação.
7. Configurar pytest + ruff + black + pre-commit.
8. Refatorar `predict_match.py` para usar `EnsembleModel`.

---

## Backlog Priorizado

| # | Item | Impacto | Esforço |
|---|------|---------|---------|
| 1 | Dados reais (48 times, calendário placeholder) | Alto | Médio |
| 2 | Pacote src/ com modelos v2 | Alto | Alto |
| 3 | Sistema de histórico e versionamento | Alto | Médio |
| 4 | Agentes formais (interface Python) | Médio | Alto |
| 5 | Métricas de avaliação | Médio | Baixo |
| 6 | Testes automatizados ≥ 70% | Médio | Médio |
| 7 | Linter + formatter + pre-commit | Baixo | Baixo |
| 8 | Monte Carlo + Dixon-Coles | Médio | Médio |
| 9 | Relatório automático de revisão | Baixo | Baixo |
