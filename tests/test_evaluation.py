# tests/test_evaluation.py
import pytest

from src.evaluation import Evaluator, MatchResult


@pytest.fixture
def ev():
    return Evaluator()


def make_pred(score):
    return {"recommended_score": score}


# Categoria 1: Placar Exato = 25pts
def test_exact_score(ev):
    assert ev.evaluate(make_pred((2, 1)), MatchResult(2, 1))["pool_points"] == 25
    assert ev.evaluate(make_pred((0, 0)), MatchResult(0, 0))["pool_points"] == 25


# Categoria 2: Vencedor + gols do vencedor = 18pts
# palpitou 2x1, terminou 2x0 (vencedor=home, gols_home=2 bate)
def test_winner_and_winner_goals(ev):
    assert ev.evaluate(make_pred((2, 1)), MatchResult(2, 0))["pool_points"] == 18


# Categoria 3: Vencedor + saldo de gols = 15pts
# palpitou 2x1 (saldo=1), terminou 1x0 (saldo=1), vencedor=home em ambos
def test_winner_and_goal_diff(ev):
    assert ev.evaluate(make_pred((2, 1)), MatchResult(1, 0))["pool_points"] == 15


# Categoria 4: Acertou Empate = 15pts
# palpitou 2x2, terminou 1x1 (ambos empate)
def test_any_draw(ev):
    assert ev.evaluate(make_pred((2, 2)), MatchResult(1, 1))["pool_points"] == 15
    assert ev.evaluate(make_pred((0, 0)), MatchResult(3, 3))["pool_points"] == 15


# Categoria 5: Vencedor + gols do perdedor = 12pts
# palpitou 2x0, terminou 3x0 (vencedor=home, gols_away=0 bate)
def test_winner_and_loser_goals(ev):
    assert ev.evaluate(make_pred((2, 0)), MatchResult(3, 0))["pool_points"] == 12


# Categoria 6: Vencedor = 10pts
# palpitou 2x0, terminou 3x2 (vencedor=home mas nada mais bate)
def test_winner_only(ev):
    assert ev.evaluate(make_pred((2, 0)), MatchResult(3, 2))["pool_points"] == 10


# Categoria 7: Gols de algum time = 5pts
# palpitou 3x0, terminou 0x0 (away_goals bate: 0=0, mas vencedor errado)
def test_one_team_goals(ev):
    result = ev.evaluate(make_pred((3, 0)), MatchResult(0, 0))
    assert result["pool_points"] == 5


# Categoria 8: Errou tudo = 0pts
def test_miss_all(ev):
    result = ev.evaluate(make_pred((3, 1)), MatchResult(0, 2))
    assert result["pool_points"] == 0


# Não confundir categorias — acerto exato não deve cair em categoria menor
def test_exact_beats_other_categories(ev):
    result = ev.evaluate(make_pred((1, 0)), MatchResult(1, 0))
    assert result["pool_points"] == 25
    assert result["category"] == "exact_score"


def test_summary_empty(ev):
    assert ev.summary([]) == {}


def test_summary_with_results(ev):
    results = [
        ev.evaluate(make_pred((2, 1)), MatchResult(2, 1)),  # 25pts
        ev.evaluate(make_pred((1, 0)), MatchResult(3, 0)),  # 12pts
        ev.evaluate(make_pred((0, 1)), MatchResult(1, 0)),  # 0pts
    ]
    s = ev.summary(results)
    assert s["total_matches"] == 3
    assert s["total_pool_points"] == 37
    assert s["exact_hits"] == 1
