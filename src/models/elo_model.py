# src/models/elo_model.py
import math
from dataclasses import dataclass

COMMON_SCORES = [(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2),(2,2),(3,1),(1,3),(3,0),(0,3)]
BASE_GOALS = 1.15
ELO_K = 400
ELO_WEIGHT = 0.20


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam**k) / math.factorial(k)


def _score_distribution(lambda_home: float, lambda_away: float, max_goals: int = 6) -> list[tuple]:
    dist = [
        (gh, ga, _poisson_pmf(gh, lambda_home) * _poisson_pmf(ga, lambda_away))
        for gh in range(max_goals + 1)
        for ga in range(max_goals + 1)
    ]
    total = sum(p for _, _, p in dist)
    return [(gh, ga, p / total) for gh, ga, p in dist]


def _summarize(dist: list[tuple]) -> tuple[float, float, float]:
    p_home = sum(p for gh, ga, p in dist if gh > ga)
    p_draw = sum(p for gh, ga, p in dist if gh == ga)
    p_away = sum(p for gh, ga, p in dist if gh < ga)
    return p_home, p_draw, p_away


def _recommended_score(dist: list[tuple]) -> tuple[int, int]:
    top8 = sorted(dist, key=lambda x: x[2], reverse=True)[:8]
    for s in COMMON_SCORES:
        for gh, ga, _ in top8:
            if (gh, ga) == s:
                return gh, ga
    return sorted(dist, key=lambda x: x[2], reverse=True)[0][:2]


def _confidence(p_home: float, p_draw: float, p_away: float) -> str:
    m = max(p_home, p_draw, p_away)
    if m >= 0.58:
        return "Alta"
    if m >= 0.45:
        return "Moderada"
    return "Baixa"


@dataclass
class EloModel:
    base_goals: float = BASE_GOALS
    elo_weight: float = ELO_WEIGHT

    def expected_goals(
        self,
        elo_a: float, elo_b: float,
        attack_a: float, defense_a: float,
        attack_b: float, defense_b: float,
    ) -> tuple[float, float]:
        diff = (elo_a - elo_b) / ELO_K
        la = self.base_goals * attack_a * defense_b * (1 + self.elo_weight * diff)
        lb = self.base_goals * attack_b * defense_a * (1 - self.elo_weight * diff)
        return max(la, 0.1), max(lb, 0.1)

    def predict(
        self,
        home_team: str, away_team: str,
        elo_home: float, elo_away: float,
        attack_home: float, defense_home: float,
        attack_away: float, defense_away: float,
    ) -> dict:
        lh, la = self.expected_goals(elo_home, elo_away, attack_home, defense_home, attack_away, defense_away)
        dist = _score_distribution(lh, la)
        ph, pd, pa = _summarize(dist)
        gh, ga = _recommended_score(dist)
        top5 = [(gh2, ga2, round(p, 4)) for gh2, ga2, p in sorted(dist, key=lambda x: x[2], reverse=True)[:5]]
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
