# src/revision.py
from pathlib import Path
from src.history import HistoryStore, PredictionRecord


class RevisionManager:
    def __init__(self, store: HistoryStore, reports_dir: Path = Path("reports/revision_history")):
        self.store = store
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_revision(self, record: PredictionRecord) -> Path:
        path = self.store.save(record)
        self._write_report(record)
        return path

    def compare_with_previous(self, match_id: str, current: PredictionRecord) -> dict:
        history = self.store.load(match_id)
        if not history:
            return {"has_previous": False, "score_changed": False, "confidence_changed": False}

        prev = history[-1]
        prev_score = tuple(prev["recommended_score"])
        curr_score = tuple(current.recommended_score)

        return {
            "has_previous": True,
            "previous_mode": prev["mode"],
            "previous_score": prev_score,
            "current_score": curr_score,
            "score_changed": prev_score != curr_score,
            "confidence_changed": prev["confidence"] != current.confidence,
            "prev_prob_home": prev["prob_home"],
            "curr_prob_home": current.prob_home,
        }

    def _write_report(self, record: PredictionRecord) -> None:
        filename = f"{record.match_id}_{record.mode}.md"
        path = self.reports_dir / filename
        content = f"""# {record.home_team} vs {record.away_team} — {record.mode}

**Match ID:** {record.match_id}
**Revisão:** {record.mode}
**Timestamp:** {record.timestamp}

## Palpite
{record.home_team} **{record.recommended_score[0]}** x **{record.recommended_score[1]}** {record.away_team}

## Probabilidades
- Vitória {record.home_team}: {record.prob_home:.1%}
- Empate: {record.prob_draw:.1%}
- Vitória {record.away_team}: {record.prob_away:.1%}

## Gols Esperados
- {record.home_team}: {record.lambda_home}
- {record.away_team}: {record.lambda_away}

## Confiança
{record.confidence}

## Notas
{record.notes or "—"}
"""
        path.write_text(content, encoding="utf-8")
