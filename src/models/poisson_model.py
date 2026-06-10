# src/models/poisson_model.py
from dataclasses import dataclass

from src.models.elo_model import _confidence, _recommended_score, _score_distribution, _summarize

HOME_ADVANTAGE = 1.12


@dataclass
class PoissonModel:
    """Modelo Poisson clássico com força de ataque/defesa relativa à média do torneio."""

    avg_home_goals: float = 1.35
    avg_away_goals: float = 1.10
    home_advantage: float = HOME_ADVANTAGE

    def attack_strength(self, team_avg_goals_scored: float) -> float:
        return team_avg_goals_scored / self.avg_home_goals

    def defense_strength(self, team_avg_goals_conceded: float) -> float:
        return team_avg_goals_conceded / self.avg_away_goals

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
    ) -> dict:
        lh = self.avg_home_goals * home_attack * away_defense * self.home_advantage
        la = self.avg_away_goals * away_attack * home_defense
        lh, la = max(lh, 0.1), max(la, 0.1)

        dist = _score_distribution(lh, la)
        ph, pd, pa = _summarize(dist)
        gh, ga = _recommended_score(dist)
        top5 = [
            (gh2, ga2, round(p, 4))
            for gh2, ga2, p in sorted(dist, key=lambda x: x[2], reverse=True)[:5]
        ]

        return {
            "home_team": home_team,
            "away_team": away_team,
            "lambda_home": round(lh, 3),
            "lambda_away": round(la, 3),
            "prob_home": round(ph, 3),
            "prob_draw": round(pd, 3),
            "prob_away": round(pa, 3),
            "top5_scores": top5,
            "recommended_score": (gh, ga),
            "confidence": _confidence(ph, pd, pa),
        }
