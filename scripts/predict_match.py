import argparse
import math
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

COMMON_SCORES = [(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2),(2,2),(3,1),(1,3),(3,0),(0,3)]

def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def expected_goals(row, ratings):
    a = row["selecao_a"]
    b = row["selecao_b"]
    ra = ratings.loc[a]
    rb = ratings.loc[b]

    elo_diff = (ra["elo"] - rb["elo"]) / 400
    base = 1.25

    lambda_a = base * ra["attack"] * rb["defense"] * (1 + 0.18 * elo_diff)
    lambda_b = base * rb["attack"] * ra["defense"] * (1 - 0.18 * elo_diff)

    return max(lambda_a, 0.2), max(lambda_b, 0.2)

def score_distribution(lambda_a, lambda_b, max_goals=6):
    rows = []
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            p = poisson_pmf(ga, lambda_a) * poisson_pmf(gb, lambda_b)
            rows.append((ga, gb, p))
    total = sum(x[2] for x in rows)
    return [(ga, gb, p / total) for ga, gb, p in rows]

def summarize_probs(dist):
    p_a = sum(p for ga, gb, p in dist if ga > gb)
    p_d = sum(p for ga, gb, p in dist if ga == gb)
    p_b = sum(p for ga, gb, p in dist if ga < gb)
    return p_a, p_d, p_b

def recommended_score(dist):
    ranked = sorted(dist, key=lambda x: x[2], reverse=True)
    top = ranked[:8]
    for s in COMMON_SCORES:
        for ga, gb, p in top:
            if (ga, gb) == s:
                return ga, gb
    return ranked[0][0], ranked[0][1]

def confidence_label(p_a, p_d, p_b):
    m = max(p_a, p_d, p_b)
    if m >= 0.58:
        return "Alta"
    if m >= 0.45:
        return "Moderada"
    return "Baixa"

def predict_one(row, ratings, mode):
    la, lb = expected_goals(row, ratings)
    dist = score_distribution(la, lb)
    p_a, p_d, p_b = summarize_probs(dist)
    ga, gb = recommended_score(dist)
    conf = confidence_label(p_a, p_d, p_b)
    top = sorted(dist, key=lambda x: x[2], reverse=True)[:5]

    return {
        "match_id": row["match_id"],
        "mode": mode,
        "selecao_a": row["selecao_a"],
        "selecao_b": row["selecao_b"],
        "placar_a": ga,
        "placar_b": gb,
        "prob_a": round(p_a, 3),
        "prob_empate": round(p_d, 3),
        "prob_b": round(p_b, 3),
        "confianca": conf,
        "ultima_revisao": datetime.now().isoformat(timespec="seconds"),
        "observacoes": f"xG {row['selecao_a']}={la:.2f}; xG {row['selecao_b']}={lb:.2f}; top={top}"
    }

def write_report(pred):
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"{pred['match_id']}_{pred['mode']}.md"
    text = f"""# {pred['selecao_a']} vs {pred['selecao_b']}

## Palpite
{pred['selecao_a']} {pred['placar_a']} x {pred['placar_b']} {pred['selecao_b']}

## Probabilidades
- Vitória {pred['selecao_a']}: {pred['prob_a']}
- Empate: {pred['prob_empate']}
- Vitória {pred['selecao_b']}: {pred['prob_b']}

## Confiança
{pred['confianca']}

## Observações
{pred['observacoes']}
"""
    path.write_text(text, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--match-id")
    parser.add_argument("--mode", default="initial")
    args = parser.parse_args()

    games = pd.read_csv(DATA / "jogos_fase_grupos.csv")
    ratings = pd.read_csv(DATA / "team_ratings.csv").set_index("team")

    if args.all:
        selected = games
    else:
        if not args.match_id:
            raise SystemExit("Use --all ou --match-id MATCH001")
        selected = games[games["match_id"] == args.match_id]
        if selected.empty:
            raise SystemExit(f"match_id não encontrado: {args.match_id}")

    preds = []
    for _, row in selected.iterrows():
        pred = predict_one(row, ratings, args.mode)
        preds.append(pred)
        write_report(pred)

    out = DATA / "palpites.csv"
    old = pd.read_csv(out) if out.exists() and out.stat().st_size > 0 else pd.DataFrame()
    new = pd.DataFrame(preds)
    combined = pd.concat([old, new], ignore_index=True) if not old.empty else new
    combined.to_csv(out, index=False)
    print(combined.tail(len(preds)).to_string(index=False))

if __name__ == "__main__":
    main()
