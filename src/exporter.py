from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from .utils import ensure_output_dir


def write_excel(path: str | Path, sheets: dict[str, pd.DataFrame]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = sheet_name[:31] or "Sheet1"
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return output_path


def export_results_to_excel(
    matios_result: pd.DataFrame,
    prokhasko_result: pd.DataFrame,
    combined_result: pd.DataFrame,
    manual_review: pd.DataFrame,
    statistics: dict[str, pd.DataFrame],
    output_dir: str | Path = "output",
) -> dict[str, Path]:
    out = ensure_output_dir(output_dir)
    paths = {
        "matios": write_excel(out / "matios_hutsulisms.xlsx", {"matios_hutsulisms": matios_result}),
        "prokhasko": write_excel(out / "prokhasko_hutsulisms.xlsx", {"prokhasko_hutsulisms": prokhasko_result}),
        "combined": write_excel(out / "combined_hutsulisms.xlsx", {"combined_hutsulisms": combined_result}),
        "manual": write_excel(out / "manual_review.xlsx", {"manual_review": manual_review}),
        "statistics": write_excel(out / "statistics_summary.xlsx", statistics),
    }
    zip_path = out / "all_results.zip"
    with ZipFile(zip_path, "w") as archive:
        for path in paths.values():
            archive.write(path, arcname=path.name)
    paths["zip"] = zip_path
    return paths

