"""
Gera agenda de automações T-24h, T-2h e T-1h para todas as partidas.
Produz data/automation_schedule.csv com cron hints no horário de Brasília.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import pytz

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = pytz.timezone("America/Sao_Paulo")

WINDOWS = [
    ("T_24H", timedelta(hours=24)),
    ("T_2H", timedelta(hours=2)),
    ("T_1H", timedelta(hours=1)),
]


def main():
    matches = pd.read_csv(DATA / "matches.csv")
    rows = []

    for _, game in matches.iterrows():
        try:
            dt = TZ.localize(datetime.strptime(game["date_brasilia"], "%Y-%m-%d %H:%M"))
        except (ValueError, KeyError) as e:
            print(f"AVISO: data inválida para {game['match_id']}: {e}", file=sys.stderr)
            continue

        for mode, delta in WINDOWS:
            run_at = dt - delta
            rows.append({
                "match_id": game["match_id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "mode": mode,
                "run_at_brasilia": run_at.strftime("%Y-%m-%d %H:%M"),
                "cron_hint": f"{run_at.minute} {run_at.hour} {run_at.day} {run_at.month} *",
                "command": f"python scripts/predict_match.py --match-id {game['match_id']} --mode {mode}",
            })

    out = DATA / "automation_schedule.csv"
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f"Agenda gerada: {len(df)} tarefas para {df['match_id'].nunique()} partidas.")
    print(f"Arquivo: {out}")


if __name__ == "__main__":
    main()
