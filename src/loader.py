from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd


FREQUENCY_COLUMNS = ["lexeme", "class", "frequency", "semantics"]
HUTSUL_COLUMNS = ["dialectism", "meaning", "source", "type", "comment"]


def _read_csv_like(file: str | Path | BinaryIO) -> pd.DataFrame:
    try:
        return pd.read_csv(file, sep=";", encoding="utf-8", dtype=str, keep_default_na=False)
    except UnicodeDecodeError:
        if hasattr(file, "seek"):
            file.seek(0)
        return pd.read_csv(file, sep=";", encoding="cp1251", dtype=str, keep_default_na=False)


def _read_excel(file: str | Path | BinaryIO) -> pd.DataFrame:
    return pd.read_excel(file, dtype=str).fillna("")


def read_table(file: str | Path | BinaryIO, name: str | None = None) -> pd.DataFrame:
    filename = name or getattr(file, "name", "") or str(file)
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return _read_excel(file)
    return _read_csv_like(file)


def _add_missing_columns(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, list[str]]:
    missing = [col for col in columns if col not in df.columns]
    result = df.copy()
    for col in missing:
        result[col] = ""
    return result[columns + [col for col in result.columns if col not in columns]], missing


def load_frequency_dictionary(file: str | Path | BinaryIO, name: str | None = None) -> tuple[pd.DataFrame, list[str]]:
    df = read_table(file, name)
    df, missing = _add_missing_columns(df, FREQUENCY_COLUMNS)
    return df, missing


def load_hutsul_dictionary(file: str | Path | BinaryIO, name: str | None = None) -> tuple[pd.DataFrame, list[str]]:
    df = read_table(file, name)
    df, missing = _add_missing_columns(df, HUTSUL_COLUMNS)
    return df, missing


def table_info(df: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "empty_values": int(df.eq("").sum().sum()),
        "preview": df.head(10),
    }

