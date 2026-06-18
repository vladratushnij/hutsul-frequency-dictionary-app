from __future__ import annotations

import pandas as pd

from .utils import is_service_token, normalize_lexeme, safe_frequency


def clean_frequency_dictionary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = df.copy()
    if "lexeme" not in result.columns:
        result["lexeme"] = ""
    if "frequency" not in result.columns:
        result["frequency"] = "0"

    result["original_lexeme"] = result["lexeme"].astype(str)
    result["normalized_lexeme"] = result["lexeme"].map(normalize_lexeme)
    result["frequency"] = result["frequency"].map(safe_frequency)
    result["is_service_token"] = result["normalized_lexeme"].map(is_service_token)

    removed = result[result["is_service_token"]].copy()
    cleaned = result[~result["is_service_token"]].copy()
    cleaned = cleaned[cleaned["frequency"] > 0].copy()
    cleaned = cleaned.sort_values("frequency", ascending=False).reset_index(drop=True)
    return cleaned, removed


def prepare_hutsul_dictionary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = df.copy()
    if "dialectism" not in result.columns:
        result["dialectism"] = ""
    result["normalized_dialectism"] = result["dialectism"].map(normalize_lexeme)
    result = result[result["normalized_dialectism"] != ""].copy()
    duplicates = result[result.duplicated("normalized_dialectism", keep=False)].copy()
    result = result.drop_duplicates("normalized_dialectism", keep="first").reset_index(drop=True)
    return result, duplicates

