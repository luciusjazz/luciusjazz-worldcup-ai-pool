# src/models/ensemble_model.py
from dataclasses import dataclass, field

from src.models.elo_model import EloModel, _recommended_score, _confidence
from src.models.poisson_model import PoissonModel
from src.models.dixon_coles import DixonColesModel
from src.models.monte_carlo import MonteCarloSimulation


@dataclass
class ModelWeights:
    elo: float = 0.40
    poisson: float = 0.30
    dixon_coles: float = 0.20
    context: float = 0.10

    def __post_init__(self):
        total = self.elo + self.poisson + self.dixon_coles + self.context
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Pesos devem somar 1.0, soma atual: {total}")


@dataclass
class EnsembleModel:
    weights: ModelWeights = field(default_factory=ModelWeights)
    monte_carlo_sims: int = 10_000
    seed: int = 42

    def __post_init__(self):
        self._elo = EloModel()
        self._poisson = PoissonModel()
        self._dc = DixonColesModel()
        self._mc = MonteCarloSimulation(n_simulations=self.monte_carlo_sims, seed=self.seed)

    def predict(
        self,
        home_team: str, away_team: str,
        elo_home: float, elo_away: float,
        attack_home: float, defense_home: float,
        attack_away: float, defense_away: float,
        context_adjustment: float = 0.0,
    ) -> dict:
        lh_elo, la_elo = self._elo.expected_goals(
            elo_home, elo_away, attack_home, defense_home, attack_away, defense_away
        )
        p_result = self._poisson.predict(
            home_team, away_team, attack_home, defense_home, attack_away, defense_away
        )
        lh_poi, la_poi = p_result["lambda_home"], p_result["lambda_away"]

        elo_w = self.weights.elo
        poi_w = self.weights.poisson
        stat_total = elo_w + poi_w
        lh = (elo_w * lh_elo + poi_w * lh_poi) / stat_total
        la = (elo_w * la_elo + poi_w * la_poi) / stat_total

        lh = lh * (1 + self.weights.context * context_adjustment)
        la = la * (1 - self.weights.context * context_adjustment)
        lh, la = max(lh, 0.1), max(la, 0.1)

        dc_result = self._dc.predict(home_team, away_team, lh, la)
        mc_result = self._mc.predict(home_team, away_team, lh, la)

        dc_w = self.weights.dixon_coles
        mc_w = 1 - dc_w
        ph = dc_w * dc_result["prob_home"] + mc_w * mc_result["prob_home"]
        pd = dc_w * dc_result["prob_draw"] + mc_w * mc_result["prob_draw"]
        pa = dc_w * dc_result["prob_away"] + mc_w * mc_result["prob_away"]
        total = ph + pd + pa
        ph, pd, pa = ph / total, pd / total, pa / total

        gh, ga = _recommended_score(sorted(dc_result["top5_scores"], key=lambda x: x[2], reverse=True))

        return {
            "home_team": home_team,
            "away_team": away_team,
            "lambda_home": round(lh, 3),
            "lambda_away": round(la, 3),
            "prob_home": round(ph, 3),
            "prob_draw": round(pd, 3),
            "prob_away": round(pa, 3),
            "top5_scores": dc_result["top5_scores"],
            "recommended_score": (gh, ga),
            "confidence": _confidence(ph, pd, pa),
            "model_contributions": {
                "elo_lambda": (round(lh_elo, 3), round(la_elo, 3)),
                "poisson_lambda": (round(lh_poi, 3), round(la_poi, 3)),
                "context_adjustment": context_adjustment,
            },
        }
