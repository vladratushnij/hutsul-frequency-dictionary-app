from __future__ import annotations

import pandas as pd


def _unique_lexemes(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    if "normalized_lexeme" in df.columns:
        return int(df["normalized_lexeme"].nunique())
    return len(df)


def _group_stats(df: pd.DataFrame, group_col: str, author: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return pd.DataFrame(columns=["author", group_col, "count", "total_frequency"])
    result = (
        df.groupby(group_col, dropna=False)
        .agg(count=("dialectism", "count"), total_frequency=("frequency", "sum"))
        .reset_index()
    )
    result.insert(0, "author", author)
    return result.sort_values("total_frequency", ascending=False).reset_index(drop=True)


def calculate_statistics(
    matios_result: pd.DataFrame,
    prokhasko_result: pd.DataFrame,
    matios_cleaned: pd.DataFrame,
    prokhasko_cleaned: pd.DataFrame,
    combined_result: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    general_stats = pd.DataFrame(
        [
            {
                "author": "Matios",
                "total_tokens_after_cleaning": int(matios_cleaned["frequency"].sum()) if not matios_cleaned.empty else 0,
                "total_unique_lexemes_after_cleaning": _unique_lexemes(matios_cleaned),
                "detected_hutsulisms_count": len(matios_result),
                "detected_hutsulisms_total_frequency": int(matios_result["frequency"].sum()) if not matios_result.empty else 0,
            },
            {
                "author": "Prokhasko",
                "total_tokens_after_cleaning": int(prokhasko_cleaned["frequency"].sum()) if not prokhasko_cleaned.empty else 0,
                "total_unique_lexemes_after_cleaning": _unique_lexemes(prokhasko_cleaned),
                "detected_hutsulisms_count": len(prokhasko_result),
                "detected_hutsulisms_total_frequency": int(prokhasko_result["frequency"].sum()) if not prokhasko_result.empty else 0,
            },
        ]
    )
    all_results = pd.concat([matios_result, prokhasko_result], ignore_index=True)
    top_hutsulisms = all_results.sort_values("frequency", ascending=False).head(40).reset_index(drop=True)
    by_part_of_speech = pd.concat(
        [_group_stats(matios_result, "class", "Matios"), _group_stats(prokhasko_result, "class", "Prokhasko")],
        ignore_index=True,
    )
    by_dialectism_type = pd.concat(
        [_group_stats(matios_result, "dialectism_type", "Matios"), _group_stats(prokhasko_result, "dialectism_type", "Prokhasko")],
        ignore_index=True,
    )
    by_semantics = pd.concat(
        [_group_stats(matios_result, "semantics", "Matios"), _group_stats(prokhasko_result, "semantics", "Prokhasko")],
        ignore_index=True,
    )
    shared_rows = []
    for _, row in combined_result.iterrows():
        if row.get("present_in_matios") and row.get("present_in_prokhasko"):
            status = "shared"
        elif row.get("present_in_matios"):
            status = "only_matios"
        else:
            status = "only_prokhasko"
        shared_rows.append(
            {
                "dialectism": row.get("dialectism", ""),
                "frequency_matios": row.get("frequency_matios", 0),
                "frequency_prokhasko": row.get("frequency_prokhasko", 0),
                "status": status,
            }
        )
    shared_and_unique = pd.DataFrame(shared_rows)
    return {
        "general_stats": general_stats,
        "top_hutsulisms": top_hutsulisms,
        "by_part_of_speech": by_part_of_speech,
        "by_dialectism_type": by_dialectism_type,
        "by_semantics": by_semantics,
        "shared_and_unique": shared_and_unique,
    }
