# src/models/dixon_coles.py
from dataclasses import dataclass

from src.models.elo_model import (
    _poisson_pmf, _summarize, _recommended_score, _confidence
)


def dixon_coles_adjustment(gh: int, ga: int, lambda_h: float, lambda_a: float, rho: float) -> float:
    """Fator de correção Dixon-Coles para placares baixos (gh+ga <= 1)."""
    if gh == 0 and ga == 0:
        return 1 - lambda_h * lambda_a * rho
    if gh == 1 and ga == 0:
        return 1 + lambda_a * rho
    if gh == 0 and ga == 1:
        return 1 + lambda_h * rho
    if gh == 1 and ga == 1:
        return 1 - rho
    return 1.0


def _dc_distribution(lambda_h: float, lambda_a: float, rho: float, max_goals: int = 6) -> list:
    dist = []
    for gh in range(max_goals + 1):
        for ga in range(max_goals + 1):
            p_raw = _poisson_pmf(gh, lambda_h) * _poisson_pmf(ga, lambda_a)
            adj = dixon_coles_adjustment(gh, ga, lambda_h, lambda_a, rho)
            dist.append((gh, ga, p_raw * adj))
    total = sum(p for _, _, p in dist)
    return [(gh, ga, p / total) for gh, ga, p in dist]


@dataclass
class DixonColesModel:
    rho: float = 0.10

    def predict(
        self,
        home_team: str, away_team: str,
        lambda_home: float, lambda_away: float,
    ) -> dict:
        dist = _dc_distribution(lambda_home, lambda_away, self.rho)
        ph, pd, pa = _summarize(dist)
        gh, ga = _recommended_score(dist)
        top5 = [(gh2, ga2, round(p, 4)) for gh2, ga2, p in sorted(dist, key=lambda x: x[2], reverse=True)[:5]]

        return {
            "home_team": home_team,
            "away_team": away_team,
            "lambda_home": round(lambda_home, 3),
            "lambda_away": round(lambda_away, 3),
            "prob_home": round(ph, 3),
            "prob_draw": round(pd, 3),
            "prob_away": round(pa, 3),
            "top5_scores": top5,
            "recommended_score": (gh, ga),
            "confidence": _confidence(ph, pd, pa),
        }
