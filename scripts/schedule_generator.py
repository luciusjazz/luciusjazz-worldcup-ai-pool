from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import pytz

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TZ = pytz.timezone("America/Sao_Paulo")

def main():
    games = pd.read_csv(DATA / "jogos_fase_grupos.csv")
    rows = []
    for _, game in games.iterrows():
        dt = TZ.localize(datetime.strptime(game["data_hora_brasilia"], "%Y-%m-%d %H:%M"))
        for label, delta in [("T-24h", timedelta(hours=24)), ("T-2h", timedelta(hours=2)), ("T-1h", timedelta(hours=1))]:
            run_at = dt - delta
            rows.append({
                "match_id": game["match_id"],
                "label": label,
                "run_at_brasilia": run_at.strftime("%Y-%m-%d %H:%M"),
                "cron_hint": f"{run_at.minute} {run_at.hour} {run_at.day} {run_at.month} *",
                "command": f"python scripts/predict_match.py --match-id {game['match_id']} --mode {label.lower().replace('-', '_')}"
            })
    out = DATA / "automation_schedule.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(pd.DataFrame(rows).to_string(index=False))

if __name__ == "__main__":
    main()
