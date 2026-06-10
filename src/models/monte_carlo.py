# src/models/monte_carlo.py
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.models.elo_model import _recommended_score, _confidence


@dataclass
class MonteCarloSimulation:
    n_simulations: int = 10_000
    seed: int | None = None

    def simulate(self, lambda_home: float, lambda_away: float) -> list[tuple]:
        rng = np.random.default_rng(self.seed)
        goals_home = rng.poisson(lambda_home, self.n_simulations)
        goals_away = rng.poisson(lambda_away, self.n_simulations)
        counts = Counter(zip(goals_home.tolist(), goals_away.tolist()))
        total = sum(counts.values())
        return [(gh, ga, c / total) for (gh, ga), c in counts.items()]

    def predict(
        self,
        home_team: str, away_team: str,
        lambda_home: float, lambda_away: float,
    ) -> dict:
        dist = self.simulate(lambda_home, lambda_away)
        ph = sum(p for gh, ga, p in dist if gh > ga)
        pd = sum(p for gh, ga, p in dist if gh == ga)
        pa = sum(p for gh, ga, p in dist if gh < ga)
        gh, ga = _recommended_score(sorted(dist, key=lambda x: x[2], reverse=True))
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
            "simulations": self.n_simulations,
        }
