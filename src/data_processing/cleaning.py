"""Conservative cleaning helpers that preserve Telugu and code-mixed text."""

from __future__ import annotations

import pandas as pd

from .normalization import clean_text, normalize_url


def clean_frame(frame: pd.DataFrame, url_columns: tuple[str, ...] = ()) -> tuple[pd.DataFrame, dict[str, int]]:
    result = frame.copy()
    result.columns = [str(column).strip().lower().replace(" ", "_") for column in result.columns]
    before = len(result)
    result = result.drop_duplicates().copy()
    removed = before - len(result)
    for column in result.columns:
        if column in url_columns:
            result[column] = result[column].map(normalize_url)
        elif result[column].dtype == "object":
            result[column] = result[column].map(clean_text)
    return result, {"duplicates_before": removed, "duplicates_removed": removed, "rows_after_cleaning": len(result)}