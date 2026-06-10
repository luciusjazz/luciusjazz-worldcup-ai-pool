"""Entry-point CLI para geração e revisão de palpites."""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.ensemble_model import EnsembleModel
from src.history import HistoryStore, PredictionRecord
from src.revision import RevisionManager

DATA = ROOT / "data"
VALID_MODES = ("INITIAL", "T_24H", "T_2H", "T_1H", "FINAL")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = pd.read_csv(DATA / "matches.csv")
    teams = pd.read_csv(DATA / "teams.csv").set_index("team")
    return matches, teams


def predict_match(row: pd.Series, teams: pd.DataFrame, mode: str, model: EnsembleModel) -> PredictionRecord:
    home, away = row["home_team"], row["away_team"]

    if home not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {home}")
    if away not in teams.index:
        raise ValueError(f"Time não encontrado em teams.csv: {away}")

    th, ta = teams.loc[home], teams.loc[away]
    result = model.predict(
        home_team=home, away_team=away,
        elo_home=th["elo"], elo_away=ta["elo"],
        attack_home=th["attack_rating"], defense_home=th["defense_rating"],
        attack_away=ta["attack_rating"], defense_away=ta["defense_rating"],
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
        notes=f"EnsembleModel | xG {home}={result['lambda_home']} {away}={result['lambda_away']}",
    )


def main():
    parser = argparse.ArgumentParser(description="Gerar palpite para partidas da Copa 2026")
    parser.add_argument("--all", action="store_true", help="Prever todas as partidas")
    parser.add_argument("--match-id", help="ID da partida (ex: GRP_E01)")
    parser.add_argument("--mode", default="INITIAL", choices=VALID_MODES)
    args = parser.parse_args()

    if not args.all and not args.match_id:
        parser.error("Use --all ou --match-id MATCH_ID")

    matches, teams = load_data()
    model = EnsembleModel()
    store = HistoryStore(base_dir=DATA / "history")
    revision_mgr = RevisionManager(store=store, reports_dir=ROOT / "reports" / "revision_history")

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
            record = predict_match(row, teams, args.mode, model)
            diff = revision_mgr.compare_with_previous(record.match_id, record)
            if diff.get("score_changed"):
                record.notes += f" | MUDANÇA: {diff['previous_score']} → {record.recommended_score}"
            revision_mgr.save_revision(record)
            records.append(record)
            gh, ga = record.recommended_score
            print(f"{record.match_id} | {record.home_team} {gh}-{ga} {record.away_team} | {record.confidence}")
        except ValueError as e:
            print(f"AVISO: {e}", file=sys.stderr)

    print(f"\n{len(records)} palpite(s) gerado(s). Modo: {args.mode}")


if __name__ == "__main__":
    main()
