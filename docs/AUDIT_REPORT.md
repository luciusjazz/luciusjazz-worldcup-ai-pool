# AUDIT_REPORT.md — WorldCup AI Pool v2.0

**Data:** 2026-06-10  
**Auditor:** Claude Code (análise automatizada + verificações manuais)  
**Commit auditado:** `5f0e782`  
**Escopo:** Código, dados, testes, documentação, performance e riscos metodológicos

---

## Sumário Executivo

O projeto está **funcionalmente operacional**: 74 testes passando, 98.96% de cobertura, código limpo e estrutura modular. Contudo, existe uma **lacuna arquitetural central**: os 8 agentes implementados não são chamados no fluxo de predição — a camada de julgamento contextual prometida na documentação ainda não existe na prática. Além disso, há um bug latente no `DixonColesModel` que não afeta o intervalo de dados atual mas pode ser ativado por inputs extremos, e uma contaminação de dados de teste no histórico de produção.

**Veredicto geral:** Fundação sólida, mas há débitos técnicos concretos que devem ser endereçados antes do uso no bolão real.

---

## 1. Estrutura de Diretórios

### O que existe

```
src/
  models/         ✅ 5 módulos (elo, poisson, dixon_coles, monte_carlo, ensemble)
  agents/         ✅ base + 8 agentes
  history.py      ✅ HistoryStore (JSONL append-only)
  evaluation.py   ✅ Evaluator (7 categorias hierárquicas do bolão)
  revision.py     ✅ RevisionManager + relatórios Markdown
data/
  teams.csv       ✅ 48 seleções reais
  matches.csv     ✅ 72 partidas fase de grupos
  history/        ⚠️  72 arquivos .jsonl — contaminados com execuções de teste
  automation_schedule.csv  ✅ 216 tarefas
scripts/
  predict_match.py         ✅ CLI principal
  generate_automations.py  ✅ Gerador de agenda
  import_worldcup_schedule.py  ✅ Validador de calendário
  schedule_generator.py    ⚠️  Script legado (duplicado)
skills/           ⚠️  10 arquivos Markdown legados (v1, não integrados ao src/)
workflows/        ⚠️  3 arquivos Markdown legados (v1)
codex/            ⚠️  automations.md (referencia scripts v1 incompatíveis)
reports/revision_history/  ✅ 72 relatórios .md gerados
tests/            ✅ 10 suites de teste
docs/             ✅ PROJECT_REVIEW.md, V2_IMPLEMENTATION_REPORT.md, planos
```

### Problemas estruturais

| Item | Problema | Severidade |
|------|----------|------------|
| `skills/*.md` | Documentação de personas v1 nunca integrada ao `src/agents/` | Baixa |
| `workflows/*.md` | Workflows v1 referenciam modos (`pregame`, `initial` minúsculo) incompatíveis com v2 | Baixa |
| `codex/automations.md` | Referencia `python scripts/predict_match.py --mode initial` (minúsculo, inválido) | Baixa |
| `scripts/schedule_generator.py` | Duplicado funcional de `generate_automations.py` (v1 não removido) | Baixa |
| `data/palpites.csv` | Arquivo v1 ainda existe mas não é mais usado | Baixa |

---

## 2. Cobertura dos Agentes

### Status real

| Agente | Classe | Dados Reais | API Externa | Usado em predict? | Confiança |
|--------|--------|-------------|-------------|-------------------|-----------|
| Jornalista Esportivo | `JournalistAgent` | ❌ Placeholder | Nenhuma | ❌ | 0.30 |
| Analista de Sinais | `PublicSignalAgent` | ❌ Placeholder | Nenhuma | ❌ | 0.30 |
| Especialista Escalações | `LineupAgent` | ❌ Placeholder | Nenhuma | ❌ | 0.25 |
| Meteorologista | `WeatherAgent` | ❌ Placeholder | Nenhuma | ❌ | 0.20 |
| Scout Tático | `TacticalAgent` | ❌ Placeholder | Nenhuma | ❌ | 0.30 |
| Historical Analyst | `HistoricalAgent` | ✅ Hardcoded | Nenhuma | ❌ | 0.70 |
| Red Team Agent | `RedTeamAgent` | ⚠️ Lógica local | Nenhuma | ❌ | 0.50 |
| Auditor de Confiança | `ConfidenceAuditor` | ⚠️ Valida entrada | Nenhuma | ❌ | 0.80 |

### Achado crítico: Agentes são decorativos

`scripts/predict_match.py` não importa nenhum agente. O fluxo completo é:

```
predict_match.py → EnsembleModel.predict() → resultado
```

Os agentes existem como classes Python testáveis, mas **não contribuem para nenhum palpite gerado**. O parâmetro `context_adjustment=0.0` em `EnsembleModel.predict()` — que seria o ponto de integração contextual — nunca é preenchido com dados dos agentes.

A "camada de contexto" de 10% do ensemble existe como código, mas está permanentemente em zero.

### HistoricalAgent: único com dados reais hardcoded

```python
_WORLD_CUP_STATS = {
    "avg_goals_per_game": 2.64,
    "draw_rate": 0.22,
    "most_common_score": "1-0",
}
```

Estes valores correspondem aproximadamente à Copa 2022 (Qatar), mas **sem citação de fonte** e sem lógica para evoluir conforme o torneio progride.

---

## 3. Modelos Estatísticos

### 3.1 EloModel

**Funciona corretamente.** Implementação do Poisson duplo com diferença de ELO é matematicamente válida.

**Débitos técnicos:**

```python
# Todos hardcoded, nenhum configurável no __init__
COMMON_SCORES = [(0,0),(1,0),(0,1),...]  # 13 placares fixos
BASE_GOALS = 1.15     # base de gols esperados — sem justificativa
ELO_K = 400           # divisor ELO — padrão FIFA mas não documentado
ELO_WEIGHT = 0.20     # intensidade do efeito ELO — arbitrário
```

`_recommended_score()` prioriza placares da lista `COMMON_SCORES`. Se nenhum dos 8 mais prováveis estiver na lista, cai no fallback `ranked[0]` — correto, mas o fallback nunca é testado.

### 3.2 PoissonModel

**Funciona corretamente.**

`HOME_ADVANTAGE = 1.12` não tem fonte citada. Na literatura, vantagem de jogar em casa em torneios internacionais neutros (como Copa do Mundo em sedes neutras para maioria das equipes) é discutível. Para Copa 2026 com jogos nos EUA/Canadá/México, o conceito de "home team" no CSV representa o time listado primeiro — não o mandante real da partida.

### 3.3 DixonColesModel

**Bug latente confirmado por verificação direta:**

```python
# Verificado: dixon_coles_adjustment(0, 0, lambda_h=10, lambda_a=10, rho=0.15) = -14.0
```

Com lambdas normais da Copa (1.0–2.9, rho=0.10), o ajuste nunca fica negativo:

```python
# Argentina vs Nova Zelândia (pior caso real):
# lambda_ARG ≈ 1.777, lambda_NZL ≈ 0.8
# adj(0,0) = 1 - 1.777 * 0.8 * 0.10 = 0.858  ✅ positivo
```

**O bug não afeta o uso atual** porque os dados reais produzem lambdas entre 0.7–2.9, e com `rho=0.10` o threshold de risco é `lambda_h * lambda_a > 10`. Contudo, se `rho` for aumentado para calibração (ex: rho=0.15 em fases eliminatórias), o risco cresce.

**Ausência de guarda-corpo:** Nenhuma validação de `rho < 1 / (lambda_h * lambda_a)` antes do cálculo.

### 3.4 MonteCarloSimulation

**Funciona corretamente.**

`n_simulations=10_000` é generoso — em benchmarks, 1.000 simulações já converge para ±0.5% nas probabilidades. O overhead é de ~8ms/partida total para o ensemble, então o impacto é mínimo.

Seed fixo em `EnsembleModel(seed=42)` garante determinismo, mas significa que **rodar duas vezes no mesmo segundo produz o mesmo resultado**. Para contexto recreativo isso é aceitável; para uso analítico seria problemático.

### 3.5 EnsembleModel

**Funciona e está completo** (96 linhas). A análise inicial do agente de exploração foi incorreta — o arquivo existe.

**Comportamento verificado:**
```
EnsembleModel.predict("Spain", "Brazil", ...) → {recommended_score: (1,1), confidence: "Baixa"}
72 partidas em 0.59s (8.2ms/partida)
```

**Ponderação das lambdas:**
```python
# Média ponderada das lambdas Elo e Poisson:
lh = (elo_w * lh_elo + poi_w * lh_poi) / (elo_w + poi_w)
# Depois aplica ajuste de contexto (sempre 0.0 na prática)
# Dixon-Coles e Monte Carlo usam lh/la final para calcular distribuição
```

**Problema arquitetural:** `DixonColesModel` recebe as lambdas finais e depois a probabilidade ensemble é calculada como média ponderada entre Dixon-Coles e Monte Carlo. Porém, Monte Carlo também usa as mesmas lambdas — os dois modelos são correlacionados em vez de independentes, o que reduz o benefício do ensemble.

---

## 4. Qualidade dos Dados

### teams.csv

```
48 seleções | ELO: 1530–2090 | Attack: 0.85–1.42 | Defense: 0.85–1.38
```

| Aspecto | Status |
|---------|--------|
| Quantidade | ✅ 48 correto para Copa 2026 |
| Campos mínimos | ✅ team, fifa_code, confederation, elo, fifa_ranking, attack_rating, defense_rating |
| Fonte dos ELOs | ❌ Não documentada |
| Data de referência | ❌ Não documentada |
| Mali sem partida | ⚠️ Mali está em teams.csv mas não aparece em nenhum grupo de matches.csv |
| Grupos A/I com times CONCACAF | ⚠️ Grupo I usa Costa Rica e Panama — mas Honduras está no Grupo A. Consistência com sorteio oficial não verificada |

### matches.csv

```
72 partidas | Fase de grupos | 12 grupos × 6 jogos | Status: todos "scheduled"
```

| Aspecto | Status |
|---------|--------|
| Quantidade | ✅ 72 correto para 12 grupos × 6 jogos |
| Datas | ⚠️ Placeholder — não validadas contra calendário oficial FIFA |
| Estádios | ✅ Sedes reais dos EUA/Canadá |
| Knockout | ❌ Ausente (oitavas, quartas, semis, final = +55 partidas) |
| Grupos A-L | ⚠️ Composição baseada em sorteio de dez/2024 — pode ter mudanças |

### data/history/ — Contaminação de Dados

**Problema confirmado:** O histórico contém execuções de teste misturadas com dados de produção.

```
GRP_E01.jsonl: 8 revisões — todas "INITIAL", todas idênticas
Timestamps: 00:55 → 07:19 (7 horas, múltiplas execuções de teste)
```

Cada vez que `pytest` roda, ele executa `test_predict_match.py` que chama `predict_match.py --all`, que salva em `data/history/`. Os arquivos de histórico deveriam estar em `tmp_path` durante testes ou o script de testes deveria usar um diretório separado.

**Impacto:** `RevisionManager.compare_with_previous()` sempre encontra "versão anterior" mesmo na primeira execução real, tornando a detecção de mudanças ruidosa.

---

## 5. Scripts de Automação

| Script | Status | Funciona? | Observação |
|--------|--------|-----------|------------|
| `predict_match.py` | ✅ Atual | ✅ Sim | CLI principal completo |
| `generate_automations.py` | ✅ Atual | ✅ Sim | 216 tarefas para 72 partidas |
| `import_worldcup_schedule.py` | ✅ Atual | ✅ Sim | Validador de calendário |
| `schedule_generator.py` | ⚠️ Legado | ✅ Sim | Duplicado de `generate_automations.py` — usar o novo |

O `codex/automations.md` referencia `--mode initial` (minúsculo), que não é mais válido. O modo correto é `INITIAL` (maiúsculo). Qualquer agente de automação que use o prompt do `codex/` vai gerar comandos inválidos.

---

## 6. Histórico de Previsões

### Estado atual

- **72 arquivos .jsonl** em `data/history/` — um por partida
- **72 relatórios .md** em `reports/revision_history/` — INITIAL gerado para todos
- Formato JSONL append-only funciona corretamente para múltiplas revisões

### Problemas

**Contaminação por testes** (já descrito na seção 4): histórico de produção e de teste compartilham o mesmo diretório.

**Ausência de deduplicação:** Rodar `--all --mode INITIAL` duas vezes acumula duas linhas idênticas por partida. `HistoryStore.save()` é append-only sem verificação de duplicata.

**Ausência de modo "limpar para nova rodada":** Não existe `--reset` ou separação por data de execução.

---

## 7. Testes Automatizados

**Resultado verificado:** `74 passed, 0 failed, 98.96% coverage`

### Análise de qualidade por suite

| Suite | Testes | Qualidade | Gap Principal |
|-------|--------|-----------|---------------|
| `test_elo_model.py` | 5 | ✅ Bom | Não testa `_recommended_score` fallback |
| `test_poisson_model.py` | 5 | ✅ Bom | Não testa `attack_strength(0)` (divisão por zero) |
| `test_dixon_coles.py` | 5 | ✅ Bom | **Não testa adj negativo** (bug latente confirmado) |
| `test_monte_carlo.py` | 4 | ✅ Bom | Não testa `n_simulations=1` (edge case) |
| `test_ensemble_model.py` | 5 | ✅ Bom | Não valida que lambda_final é média ponderada correta |
| `test_agents.py` | ~28 | ✅ Bom | Não testa que agentes são chamados pelo ensemble |
| `test_history.py` | 5 | ✅ Bom | Não testa comportamento com arquivo JSONL corrompido |
| `test_evaluation.py` | 11 | ✅ Excelente | Cobre todas as 7 categorias com casos de transição |
| `test_revision.py` | 5 | ✅ Bom | Não testa comparação com confidence diferente |
| `test_predict_match.py` | 4 | ⚠️ Superficial | Só verifica returncode — não valida conteúdo das previsões |

### Problema sistêmico

`test_predict_match.py` usa subprocess e verifica apenas `returncode == 0`. Não valida:
- Se os arquivos `.jsonl` foram criados corretamente
- Se as probabilidades geradas são coerentes
- Se o modo `T_24H` difere do `INITIAL`

Os testes de integração são passantes-por-definição — o script roda sem erro, mas não sabemos se produz output correto.

---

## 8. Dependências

### requirements.txt atual

```
pandas>=2.0      ✅ Necessário
numpy>=1.24      ✅ Necessário
scipy>=1.11      ⚠️ Instalado mas não utilizado em nenhum src/
python-dateutil>=2.8  ✅ Necessário (pytz usa)
pytz>=2024.1     ✅ Necessário
pytest>=8.0      ✅ Dev
pytest-cov>=5.0  ✅ Dev
ruff>=0.4        ✅ Dev
black>=24.0      ✅ Dev
pre-commit>=3.7  ✅ Dev
```

**`scipy` não é usado.** Foi adicionado como dependência antecipando implementações futuras (distribuições estatísticas, estimação de parâmetros Dixon-Coles via MLE), mas nenhum arquivo em `src/` o importa atualmente. Adiciona ~30MB de instalação desnecessariamente.

**Versões não fixadas:** `pandas>=2.0` permite instalar `pandas 3.x` quando sair, que pode ter breaking changes. Para reprodutibilidade, deveriam estar fixadas em `pyproject.toml` ou via `pip freeze > requirements.lock`.

---

## 9. Performance

### Medições verificadas

| Operação | Tempo | Aceitável? |
|----------|-------|------------|
| 72 partidas (EnsembleModel) | 0.59s (8.2ms/partida) | ✅ Sim |
| 1 partida (EnsembleModel) | ~8ms | ✅ Sim |
| Suite completa de testes | 1.87s | ✅ Sim |
| Monte Carlo 10.000 sim | ~2ms | ✅ Sim |

**Sem gargalos identificados** para o volume atual (72–104 partidas).

### Observação sobre escalabilidade

Se o projeto expandir para fases eliminatórias (104 partidas totais) e múltiplos modos de revisão, o overhead de salvar `data/history/` (I/O de arquivo) pode crescer. JSONL append-only escala bem — sem preocupação.

---

## 10. Riscos Metodológicos

### R1 — Modelo não adapta parâmetros ao torneio em andamento

Os ratings `elo`, `attack_rating`, `defense_rating` são fixos. Na prática, o desempenho de seleções evolui ao longo do torneio — formas recentes, lesões acumuladas, adaptação ao calor/altitude. O modelo não tem mecanismo para atualizar esses parâmetros.

**Severidade:** Alta para revisões T-2h e T-1h (quando mais informação é disponível).

### R2 — HOME_ADVANTAGE inadequado para Copa do Mundo

`PoissonModel` aplica `HOME_ADVANTAGE = 1.12` sempre. Na Copa 2026, a maioria das equipes joga em campo neutro (EUA/Canadá/México). O "mandante" no CSV é apenas o time listado primeiro — não tem vantagem de campo real na maioria dos jogos.

**Exceção:** México, EUA e Canadá jogam em seus países — esses deveriam ter `HOME_ADVANTAGE > 1`. As demais equipes deveriam ter `1.0`.

**Severidade:** Média. Distorce ligeiramente as previsões de jogos com mandante artificial.

### R3 — Ensemble não é realmente ensemble

`DixonColesModel` e `MonteCarloSimulation` recebem as **mesmas lambdas** como entrada. Os dois modelos são instâncias do mesmo processo estocástico com a mesma parametrização — não são modelos independentes. A diversificação que um ensemble deveria fornecer não existe aqui.

Um ensemble verdadeiro usaria lambdas calculadas independentemente por cada modelo antes de combinar. Atualmente, o "ensemble" é: **Elo + Poisson calculam lambdas → lambda médio → Dixon-Coles aplica correção → Monte Carlo simula**.

### R4 — Dixon-Coles com `rho` fixo e não calibrado

`rho = 0.10` é um valor da literatura original (1997, dados da Premier League). Para Copa do Mundo com times de força muito assimétrica, o valor pode ser diferente. Sem calibração nos dados históricos de Copas, é arbitrário.

### R5 — Agentes contextuais não contribuem para as previsões

O único input contextual disponível ao modelo é `context_adjustment=0.0`. Notícias de lesões, escalações, condições climáticas, odds de mercado — todos os fatores que os agentes deveriam capturar — são ignorados nas previsões finais.

Para um bolão onde informação contextual pode ser a diferença (ex: Mbappé lesionado na véspera), este risco é alto.

### R6 — Dados de histórico contaminados

`data/history/` mistura execuções de teste com dados de produção. Quando o RevisionManager calcular se houve mudança desde a última revisão, pode comparar contra uma execução de teste, não contra a revisão humana mais recente.

### R7 — Calendário não validado contra fonte oficial

`data/matches.csv` foi gerado com base no sorteio de grupos de dez/2024, mas as datas e horários são placeholders. Não há verificação automática contra o calendário oficial da FIFA. O agendamento automático (cron hints) pode estar apontando para horários incorretos.

---

## O que está Realmente Implementado

| Componente | Status |
|------------|--------|
| Modelo Elo com Poisson | ✅ Implementado e testado |
| Modelo Poisson com home advantage | ✅ Implementado e testado |
| Correção Dixon-Coles (placares baixos) | ✅ Implementado — bug latente não crítico para dados atuais |
| Monte Carlo com numpy RNG | ✅ Implementado e testado |
| Ensemble 40/30/20/10 | ✅ Implementado — mas arquiteturalmente incompleto (R3) |
| 8 agentes com AgentResult | ✅ Implementados e testados — **não integrados no fluxo** |
| HistoryStore (JSONL) | ✅ Implementado e testado |
| Evaluator (7 categorias do bolão) | ✅ Implementado e testado |
| RevisionManager | ✅ Implementado e testado |
| CLI predict_match.py | ✅ Funcional |
| Agenda de automações | ✅ 216 tarefas geradas |
| 48 seleções reais | ✅ Dados presentes |
| 72 partidas fase de grupos | ✅ Dados presentes (datas placeholder) |

## O que está Parcialmente Implementado

| Componente | O que existe | O que falta |
|------------|--------------|-------------|
| Integração de agentes | Classes, testes, pesos definidos | Chamada no fluxo de predição |
| Ajuste contextual | Parâmetro `context_adjustment` no EnsembleModel | Quem preenche esse parâmetro |
| Calibração de parâmetros | Valores fixados no código | Estimação via dados históricos de Copas |
| Fase knockout | Estrutura suporta qualquer `stage` | matches.csv sem oitavas/quartas/semis/final |
| Atualização de ratings | `teams.csv` editável manualmente | Script/mecanismo para atualizar durante torneio |
| Validação de calendário | `import_worldcup_schedule.py` detecta placeholders | Integração com fonte oficial (FIFA) |

## O que é Apenas Documentação

| Item | Localização | Status real |
|------|-------------|-------------|
| Agentes especializados com dados reais | `AGENTS.md`, `skills/*.md` | Apenas Markdown — sem código funcional |
| Revisão com notícias e escalações | `workflows/revisao-pre-jogo.md` | Processo manual — sem automação |
| Pesos dos agentes no palpite final | `AGENTS.md` (Estatístico 35%, etc.) | Não implementado em código |
| Gerente de Palpite consolidando todos | `skills/gerente-palpite.md` | Não existe como módulo Python |
| Automações recorrentes com cron | `codex/automations.md` | Cron hints gerados, mas execução manual |

---

## Bugs Encontrados

### BUG-001 — DixonColesModel: probabilidade negativa em inputs extremos

**Arquivo:** `src/models/dixon_coles.py`, linha 14  
**Severidade:** Baixa (não afeta dados reais atuais)  
**Reprodução:**
```python
from src.models.dixon_coles import dixon_coles_adjustment
dixon_coles_adjustment(0, 0, lambda_h=10, lambda_a=10, rho=0.15)
# Retorna: -14.0
```
**Condição de risco:** `rho > 1 / (lambda_h * lambda_a)`. Com dados atuais (max lambda ≈ 2.9, rho=0.10), o threshold é 1/(2.9²) ≈ 0.12 — margem estreita.  
**Correção sugerida:** `return max(1 - lambda_h * lambda_a * rho, 0.0)` na linha 14.

### BUG-002 — Histórico contaminado por execuções de teste

**Arquivo:** `data/history/*.jsonl`  
**Severidade:** Média  
**Reprodução:** Rodar `pytest` escreve em `data/history/` via `test_predict_match.py`  
**Impacto:** `compare_with_previous()` sempre encontra revisão anterior mesmo na primeira execução real  
**Correção sugerida:** `test_predict_match.py` deve usar `HISTORY_DIR` apontando para `tmp_path` via variável de ambiente, ou o script deve aceitar `--history-dir` como argumento.

### BUG-003 — `codex/automations.md` com modo inválido

**Arquivo:** `codex/automations.md`  
**Severidade:** Baixa  
**Problema:** `--mode initial` (minúsculo) é inválido — o modo correto é `INITIAL`  
**Impacto:** Agente de automação usando este prompt vai gerar erro de CLI

### BUG-004 — `workflows/revisao-pre-jogo.md` referencia modo inválido

**Arquivo:** `workflows/revisao-pre-jogo.md`  
**Severidade:** Baixa  
**Problema:** `--mode pregame` não existe nos `VALID_MODES`

---

## Débitos Técnicos

| ID | Débito | Impacto | Esforço |
|----|--------|---------|---------|
| DT-01 | Agentes não integrados no fluxo de predição | Alto | Médio |
| DT-02 | `context_adjustment` fixo em 0.0 para todos os palpites | Alto | Médio |
| DT-03 | `scipy` como dependência sem uso | Baixo | Mínimo |
| DT-04 | Parâmetros dos modelos hardcoded (BASE_GOALS, HOME_ADVANTAGE, rho) | Médio | Médio |
| DT-05 | Sem mecanismo de atualização de ratings durante torneio | Alto | Alto |
| DT-06 | Monte Carlo e Dixon-Coles não são independentes no ensemble | Médio | Alto |
| DT-07 | `test_predict_match.py` sem validação de conteúdo | Médio | Baixo |
| DT-08 | `schedule_generator.py` legado não removido | Baixo | Mínimo |
| DT-09 | `skills/`, `workflows/`, `codex/` com referências obsoletas | Baixo | Baixo |
| DT-10 | Versões de dependências não fixadas (sem lock file) | Médio | Baixo |
| DT-11 | `HOME_ADVANTAGE=1.12` inadequado para Copa (campo neutro) | Médio | Baixo |
| DT-12 | Sem logging estruturado (apenas `print()`) | Baixo | Baixo |

---

## Melhorias Prioritárias

### Prioridade 1 — Corrigir antes do bolão começar

1. **Limpar histórico contaminado** — remover `data/history/*.jsonl` e `reports/revision_history/*.md` gerados pelos testes. Adicionar `--history-dir` ao `predict_match.py` ou variável de ambiente para separar teste de produção.

2. **Corrigir BUG-001 (Dixon-Coles)** — adicionar `max(..., 0.0)` no ajuste de (0,0). Uma linha de código, zero risco.

3. **Corrigir documentação v1** — atualizar `codex/automations.md`, `workflows/revisao-pre-jogo.md` com modos válidos (`INITIAL`, `T_24H`, etc.).

### Prioridade 2 — Melhorar qualidade das previsões

4. **Integrar ao menos 1 agente no fluxo** — `HistoricalAgent` já tem dados reais hardcoded e poderia ajustar `context_adjustment` com base na média histórica de gols por fase/grupo.

5. **Corrigir HOME_ADVANTAGE por partida** — times do Grupo A (USA, México, Honduras) realmente jogam "em casa". Adicionar coluna `is_home_country` em `matches.csv` ou calcular via `confederation + country`.

6. **Remover `scipy` ou usar** — ou implementar estimação de parâmetros Dixon-Coles via scipy (MLE), ou remover do `requirements.txt`.

### Prioridade 3 — Débitos que não bloqueiam mas degradam qualidade

7. **Adicionar `requirements.lock`** com versões fixadas via `pip freeze`.

8. **Melhorar `test_predict_match.py`** — validar que os arquivos `.jsonl` foram criados com conteúdo correto.

9. **Consolidar scripts legados** — remover `schedule_generator.py` ou adicioná-lo ao `.gitignore`.

10. **Documentar parâmetros dos modelos** — adicionar comentário com fonte para `BASE_GOALS=1.15`, `HOME_ADVANTAGE=1.12`, `rho=0.10`.

---

## Roadmap V3 — Priorizado por Impacto

### Fase 1 — Correções essenciais (antes da Copa, ~1 semana)

| # | Item | Impacto Direto no Bolão |
|---|------|------------------------|
| 1.1 | Limpar histórico de teste / separar ambientes | Previsões não vão comparar contra dados de teste |
| 1.2 | Corrigir Dixon-Coles BUG-001 | Modelo matematicamente válido para todos os inputs |
| 1.3 | Corrigir HOME_ADVANTAGE por partida | Previsões de USA/México/Canadá mais realistas |
| 1.4 | Atualizar `codex/automations.md` e workflows v1 | Automações via Codex/Claude funcionam sem erro |

### Fase 2 — Integração contextual mínima (semana 1 da Copa)

| # | Item | Impacto Direto no Bolão |
|---|------|------------------------|
| 2.1 | Orquestrador de agentes em `predict_match.py` | Agentes contribuem para `context_adjustment` |
| 2.2 | Integração `HistoricalAgent` com ajuste de fase (grupos vs knockout) | Previsões calibradas ao contexto da fase |
| 2.3 | Mecanismo de update de ratings pós-jogo | ELO se atualiza conforme resultados reais chegam |
| 2.4 | Campo `match_result` em `matches.csv` para resultados reais | Avaliação automática pós-jogo com `Evaluator` |

### Fase 3 — Modelo mais robusto (durante a Copa)

| # | Item | Impacto Direto no Bolão |
|---|------|------------------------|
| 3.1 | Estimação de rho via MLE com dados históricos de Copas | Dixon-Coles calibrado, não arbitrário |
| 3.2 | Ensemble com lambdas independentes por modelo | Diversificação real entre modelos |
| 3.3 | Integração com API de escalações (ex: football-data.org) | LineupAgent com dados reais T-1h |
| 3.4 | Integração OpenWeather para cidades sede | WeatherAgent com dados reais |

### Fase 4 — Visualização e rastreabilidade (Copa em andamento)

| # | Item | Impacto Direto no Bolão |
|---|------|------------------------|
| 4.1 | Dashboard Streamlit com palpites e pontuação acumulada | Acompanhamento visual do bolão |
| 4.2 | Script `evaluate_results.py` — pontuação automática pós-jogo | Saber quem está ganhando o bolão em tempo real |
| 4.3 | Fase knockout dinâmica — matches.csv atualizado com classificados | Previsões para oitavas/quartas/semis/final |
| 4.4 | Relatório de calibração — probabilidades previstas vs realizadas | Saber se o modelo é bem calibrado |

### Fase 5 — Pós-Copa (aprendizado para próxima edição)

| # | Item | Valor |
|---|------|-------|
| 5.1 | Retreinar parâmetros (BASE_GOALS, ELO_WEIGHT, rho) com dados da Copa 2026 | Modelo melhorado para Copa 2030 |
| 5.2 | Comparar desempenho dos 4 modelos individualmente | Identificar qual modelo foi mais preciso |
| 5.3 | Análise de `context_adjustment` — quando o contexto teria mudado a previsão? | Quantificar valor de cada agente retrospectivamente |
