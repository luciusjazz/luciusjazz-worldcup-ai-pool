"""Entry-point CLI para geração e revisão de palpites."""

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.context_engine import ContextEngine
from src.history import HistoryStore, PredictionRecord
from src.models.ensemble_model import EnsembleModel
from src.revision import RevisionManager

DATA = ROOT / "data"
VALID_MODES = ("INITIAL", "T_24H", "T_2H", "T_1H", "FINAL")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = pd.read_csv(DATA / "matches.csv")
    teams = pd.read_csv(DATA / "teams.csv").set_index("team")
    return matches, teams


def predict_match(
    row: pd.Series,
    teams: pd.DataFrame,
    mode: str,
    model: EnsembleModel,
    context_engine: ContextEngine,
) -> PredictionRecord:
    home, away = row["home_team"], row["away_team"]

    if home not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {home}")
    if away not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {away}")

    th, ta = teams.loc[home], teams.loc[away]

    # Primeira rodada sem ajuste para obter lambdas/probs base (input para agentes)
    base_result = model.predict(
        home_team=home,
        away_team=away,
        elo_home=th["elo"],
        elo_away=ta["elo"],
        attack_home=th["attack_rating"],
        defense_home=th["defense_rating"],
        attack_away=ta["attack_rating"],
        defense_away=ta["defense_rating"],
        context_adjustment=0.0,
    )

    # Contexto rico para os agentes (inclui lambdas e probs da rodada base)
    agent_context = {
        "home_team": home,
        "away_team": away,
        "match_id": row["match_id"],
        "stage": row.get("stage", "group"),
        "city": row.get("city", ""),
        "lambda_home": base_result["lambda_home"],
        "lambda_away": base_result["lambda_away"],
        "prob_home": base_result["prob_home"],
        "prob_draw": base_result["prob_draw"],
        "prob_away": base_result["prob_away"],
        "elo_home": float(th["elo"]),
        "elo_away": float(ta["elo"]),
    }

    engine_result = context_engine.run(agent_context)

    # Segunda rodada com context_adjustment real dos agentes
    result = model.predict(
        home_team=home,
        away_team=away,
        elo_home=th["elo"],
        elo_away=ta["elo"],
        attack_home=th["attack_rating"],
        defense_home=th["defense_rating"],
        attack_away=ta["attack_rating"],
        defense_away=ta["defense_rating"],
        context_adjustment=engine_result.context_adjustment,
    )

    contributions_dicts = [
        {
            "agent_name": c.agent_name,
            "weight": c.weight,
            "confidence": c.confidence,
            "adjustment_home": c.adjustment_home,
            "adjustment_away": c.adjustment_away,
            "rationale": c.rationale,
            "effective_contribution": c.effective_contribution,
        }
        for c in engine_result.agent_contributions
    ]

    notes = (
        f"EnsembleModel | xG {home}={result['lambda_home']} {away}={result['lambda_away']} "
        f"| context_adj={engine_result.context_adjustment:+.4f}"
    )

    return PredictionRecord(
        match_id=row["match_id"],
        mode=mode,
        home_team=home,
        away_team=away,
        recommended_score=result["recommended_score"],
        prob_home=result["prob_home"],
        prob_draw=result["prob_draw"],
        prob_away=result["prob_away"],
        confidence=result["confidence"],
        lambda_home=result["lambda_home"],
        lambda_away=result["lambda_away"],
        top5_scores=result["top5_scores"],
        notes=notes,
        agent_contributions=contributions_dicts,
        context_adjustment=engine_result.context_adjustment,
    )


def main():
    parser = argparse.ArgumentParser(description="Gerar palpite para partidas da Copa 2026")
    parser.add_argument("--all", action="store_true", help="Prever todas as partidas")
    parser.add_argument("--match-id", help="ID da partida (ex: GRP_E01)")
    parser.add_argument("--mode", default="INITIAL", choices=VALID_MODES)
    parser.add_argument(
        "--history-dir",
        default=str(DATA / "history"),
        help="Diretório para salvar histórico (default: data/history)",
    )
    args = parser.parse_args()

    if not args.all and not args.match_id:
        parser.error("Use --all ou --match-id MATCH_ID")

    matches, teams = load_data()
    model = EnsembleModel()
    context_engine = ContextEngine()
    history_dir = Path(args.history_dir)
    store = HistoryStore(base_dir=history_dir)
    reports_dir = ROOT / "reports" / "revision_history"
    revision_mgr = RevisionManager(store=store, reports_dir=reports_dir)

    if args.all:
        selected = matches[matches["stage"] == "group"]
    else:
        selected = matches[matches["match_id"] == args.match_id]
        if selected.empty:
            print(f"ERRO: match_id não encontrado: {args.match_id}", file=sys.stderr)
            sys.exit(1)

    records = []
    for _, row in selected.iterrows():
        try:
            record = predict_match(row, teams, args.mode, model, context_engine)
            diff = revision_mgr.compare_with_previous(record.match_id, record)
            if diff.get("score_changed"):
                record.notes += f" | MUDANÇA: {diff['previous_score']} → {record.recommended_score}"
            revision_mgr.save_revision(record)
            records.append(record)
            gh, ga = record.recommended_score
            print(
                f"{record.match_id} | {record.home_team} {gh}-{ga} {record.away_team} "
                f"| {record.confidence} | adj={record.context_adjustment:+.4f}"
            )
        except ValueError as e:
            print(f"AVISO: {e}", file=sys.stderr)

    print(f"\n{len(records)} palpite(s) gerado(s). Modo: {args.mode}")


if __name__ == "__main__":
    main()
