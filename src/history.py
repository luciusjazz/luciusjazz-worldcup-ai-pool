# src/history.py
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import pytz

TZ = pytz.timezone("America/Sao_Paulo")
MODES = ("INITIAL", "T_24H", "T_2H", "T_1H", "FINAL")


@dataclass
class PredictionRecord:
    match_id: str
    mode: str
    home_team: str
    away_team: str
    recommended_score: tuple
    prob_home: float
    prob_draw: float
    prob_away: float
    confidence: str
    lambda_home: float
    lambda_away: float
    top5_scores: list
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(TZ).isoformat(timespec="seconds"))

    def __post_init__(self):
        if self.mode not in MODES:
            raise ValueError(f"mode deve ser um de {MODES}, recebido: {self.mode}")


class HistoryStore:
    def __init__(self, base_dir="data/history"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, match_id: str) -> Path:
        return self.base_dir / f"{match_id}.jsonl"

    def save(self, record: PredictionRecord) -> Path:
        path = self._path(record.match_id)
        data = asdict(record)
        data["recommended_score"] = list(data["recommended_score"])
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return path

    def load(self, match_id: str) -> list:
        path = self._path(match_id)
        if not path.exists():
            return []
        records = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def load_all(self) -> dict:
        result = {}
        for path in sorted(self.base_dir.glob("*.jsonl")):
            match_id = path.stem
            result[match_id] = self.load(match_id)
        return result
