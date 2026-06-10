# src/evaluation.py
from dataclasses import dataclass


@dataclass
class MatchResult:
    home_goals: int
    away_goals: int

    def outcome(self) -> str:
        if self.home_goals > self.away_goals:
            return "home"
        if self.home_goals < self.away_goals:
            return "away"
        return "draw"


class Evaluator:
    """
    Calcula pontuação do bolão 'Entre Amigos' para uma previsão vs resultado real.

    Hierarquia de pontuação (pega a primeira que se encaixa):
    1. Placar Exato           = 25pts
    2. Vencedor + gols_vencedor = 18pts
    3. Vencedor + saldo_gols  = 15pts
    4. Acertou Empate         = 15pts
    5. Vencedor + gols_perdedor = 12pts
    6. Vencedor               = 10pts
    7. Gols de algum time     = 5pts
    8. Errou tudo             = 0pts
    """

    def evaluate(self, prediction: dict, actual: MatchResult) -> dict:
        ph, pa = tuple(prediction["recommended_score"])
        rh, ra = actual.home_goals, actual.away_goals

        pred_outcome = "home" if ph > pa else ("away" if ph < pa else "draw")
        actual_outcome = actual.outcome()
        winner_correct = pred_outcome == actual_outcome and pred_outcome != "draw"
        is_draw_pred = pred_outcome == "draw"
        is_draw_actual = actual_outcome == "draw"

        # 1. Placar exato
        if ph == rh and pa == ra:
            return self._result(25, "exact_score", ph, pa, rh, ra)

        # 2. Vencedor + gols do vencedor
        if winner_correct:
            if pred_outcome == "home" and ph == rh:
                return self._result(18, "winner_winner_goals", ph, pa, rh, ra)
            if pred_outcome == "away" and pa == ra:
                return self._result(18, "winner_winner_goals", ph, pa, rh, ra)

        # 3. Vencedor + saldo de gols
        if winner_correct and (ph - pa) == (rh - ra):
            return self._result(15, "winner_goal_diff", ph, pa, rh, ra)

        # 4. Acertou empate (qualquer empate)
        if is_draw_pred and is_draw_actual:
            return self._result(15, "any_draw", ph, pa, rh, ra)

        # 5. Vencedor + gols do perdedor
        if winner_correct:
            if pred_outcome == "home" and pa == ra:
                return self._result(12, "winner_loser_goals", ph, pa, rh, ra)
            if pred_outcome == "away" and ph == rh:
                return self._result(12, "winner_loser_goals", ph, pa, rh, ra)

        # 6. Vencedor
        if winner_correct:
            return self._result(10, "winner_only", ph, pa, rh, ra)

        # 7. Gols de algum time
        if ph == rh or pa == ra:
            return self._result(5, "one_team_goals", ph, pa, rh, ra)

        # 8. Errou tudo
        return self._result(0, "miss", ph, pa, rh, ra)

    def _result(self, points: int, category: str, ph: int, pa: int, rh: int, ra: int) -> dict:
        return {
            "pool_points": points,
            "category": category,
            "predicted": (ph, pa),
            "actual": (rh, ra),
            "goal_error": abs(ph - rh) + abs(pa - ra),
        }

    def summary(self, results: list[dict]) -> dict:
        if not results:
            return {}
        n = len(results)
        categories = [r["category"] for r in results]
        return {
            "total_matches": n,
            "total_pool_points": sum(r["pool_points"] for r in results),
            "avg_pool_points": round(sum(r["pool_points"] for r in results) / n, 1),
            "exact_hits": categories.count("exact_score"),
            "draw_hits": categories.count("any_draw"),
            "winner_hits": sum(1 for c in categories if c.startswith("winner")),
            "avg_goal_error": round(sum(r["goal_error"] for r in results) / n, 2),
            "category_counts": {c: categories.count(c) for c in set(categories)},
        }
