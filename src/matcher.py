from __future__ import annotations

import pandas as pd


RESULT_COLUMNS = [
    "dialectism",
    "author",
    "original_lexeme",
    "normalized_lexeme",
    "class",
    "frequency",
    "semantics",
    "dialectism_type",
    "meaning",
    "dictionary_source",
    "match_type",
    "comment",
]


def match_exact(author_df: pd.DataFrame, hutsul_df: pd.DataFrame) -> pd.DataFrame:
    merged = author_df.merge(
        hutsul_df,
        left_on="normalized_lexeme",
        right_on="normalized_dialectism",
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    result = pd.DataFrame(
        {
            "dialectism": merged.get("dialectism", ""),
            "author": merged.get("author", ""),
            "original_lexeme": merged.get("original_lexeme", merged.get("lexeme", "")),
            "normalized_lexeme": merged.get("normalized_lexeme", ""),
            "class": merged.get("class", ""),
            "frequency": merged.get("frequency", 0),
            "semantics": merged.get("semantics", ""),
            "dialectism_type": merged.get("type", ""),
            "meaning": merged.get("meaning", ""),
            "dictionary_source": merged.get("source", ""),
            "match_type": "exact",
            "comment": merged.get("comment", ""),
        }
    )
    return result.sort_values("frequency", ascending=False).reset_index(drop=True)


def find_manual_candidates(author_df: pd.DataFrame, hutsul_df: pd.DataFrame) -> pd.DataFrame:
    exact_keys = set(hutsul_df["normalized_dialectism"].dropna())
    exact_author = set(author_df.loc[author_df["normalized_lexeme"].isin(exact_keys), "normalized_lexeme"])
    rows: list[dict[str, object]] = []
    dictionary_items = hutsul_df[["dialectism", "normalized_dialectism"]].dropna().values.tolist()

    for _, row in author_df.iterrows():
        lexeme = row.get("normalized_lexeme", "")
        if not lexeme or lexeme in exact_author:
            continue
        for dialectism, normalized in dictionary_items:
            if len(normalized) < 4:
                continue
            if lexeme.startswith(normalized) or normalized in lexeme:
                rows.append(
                    {
                        "author": row.get("author", ""),
                        "original_lexeme": row.get("original_lexeme", row.get("lexeme", "")),
                        "normalized_lexeme": lexeme,
                        "possible_dictionary_match": dialectism,
                        "frequency": row.get("frequency", 0),
                        "class": row.get("class", ""),
                        "semantics": row.get("semantics", ""),
                        "reason": "partial_or_derived_form",
                        "decision": "",
                        "corrected_dialectism": "",
                        "comment": "",
                    }
                )
                break

    return pd.DataFrame(rows).sort_values("frequency", ascending=False).reset_index(drop=True)


def build_author_result(author_name: str, author_df: pd.DataFrame, hutsul_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = author_df.copy()
    prepared["author"] = author_name
    exact = match_exact(prepared, hutsul_df)
    manual = find_manual_candidates(prepared, hutsul_df)
    return exact, manual


def build_combined_result(matios_result: pd.DataFrame, prokhasko_result: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([matios_result, prokhasko_result], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(
            columns=[
                "dialectism",
                "meaning",
                "dialectism_type",
                "dictionary_source",
                "frequency_matios",
                "frequency_prokhasko",
                "total_frequency",
                "present_in_matios",
                "present_in_prokhasko",
            ]
        )
    pivot = combined.pivot_table(index="dialectism", columns="author", values="frequency", aggfunc="sum", fill_value=0)
    pivot = pivot.reset_index()
    if "Matios" not in pivot.columns:
        pivot["Matios"] = 0
    if "Prokhasko" not in pivot.columns:
        pivot["Prokhasko"] = 0
    meta = combined.drop_duplicates("dialectism")[["dialectism", "meaning", "dialectism_type", "dictionary_source"]]
    result = meta.merge(pivot, on="dialectism", how="left")
    result = result.rename(columns={"Matios": "frequency_matios", "Prokhasko": "frequency_prokhasko"})
    result["total_frequency"] = result["frequency_matios"] + result["frequency_prokhasko"]
    result["present_in_matios"] = result["frequency_matios"] > 0
    result["present_in_prokhasko"] = result["frequency_prokhasko"] > 0
    return result.sort_values("total_frequency", ascending=False).reset_index(drop=True)

