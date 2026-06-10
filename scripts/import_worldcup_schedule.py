"""
import_worldcup_schedule.py — Documentação de como atualizar o calendário quando
a FIFA publicar o cronograma oficial.

Enquanto o calendário oficial não estiver disponível, este script:
1. Valida o matches.csv existente.
2. Reporta entradas com data/sede placeholder.
3. Orienta como substituir os dados.

Fontes recomendadas:
- https://www.fifa.com/worldcup/2026/
- https://en.wikipedia.org/wiki/2026_FIFA_World_Cup
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

REQUIRED_COLUMNS = {
    "match_id", "date_utc", "date_brasilia", "stage",
    "group", "home_team", "away_team", "stadium", "city", "country", "status"
}

PLACEHOLDER_INDICATORS = ["a definir", "tbd", "placeholder", "?"]


def validate_matches(path: Path) -> dict:
    if not path.exists():
        return {"error": f"Arquivo não encontrado: {path}"}

    df = pd.read_csv(path)
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        return {"error": f"Colunas ausentes: {missing_cols}"}

    placeholders = df[
        df["stadium"].str.lower().isin(PLACEHOLDER_INDICATORS)
        | df["city"].str.lower().isin(PLACEHOLDER_INDICATORS)
    ]

    return {
        "total_matches": len(df),
        "stages": df["stage"].value_counts().to_dict(),
        "placeholder_count": len(placeholders),
        "placeholder_matches": placeholders["match_id"].tolist(),
        "status_counts": df["status"].value_counts().to_dict(),
    }


def main():
    path = DATA / "matches.csv"
    result = validate_matches(path)

    if "error" in result:
        print(f"ERRO: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print("=== Validação do Calendário FIFA 2026 ===")
    print(f"Total de partidas: {result['total_matches']}")
    print(f"Por fase: {result['stages']}")
    print(f"Por status: {result['status_counts']}")
    print(f"Placeholders: {result['placeholder_count']}")

    if result["placeholder_count"]:
        print("\nAVISO: As seguintes partidas têm dados placeholder:")
        for mid in result["placeholder_matches"]:
            print(f"  - {mid}")
        print("\nPara atualizar, edite data/matches.csv com os dados oficiais da FIFA.")
        print("Fonte: https://www.fifa.com/worldcup/2026/")
    else:
        print("\nCalendário validado sem placeholders.")


if __name__ == "__main__":
    main()
