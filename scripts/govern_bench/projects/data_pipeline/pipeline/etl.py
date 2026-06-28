"""ETL starter with deliberate defects for GovernanceBench task expansion.

This project intentionally includes:
- missing dedup in run_pipeline (T16)
- schema-drift null handling bug (T17)
- mutable default list in normalize_records
- row-by-row coercion hot path
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_COLUMNS = ["id", "device_id", "ts", "value", "status"]


def normalize_records(
    records: list[dict[str, Any]],
    columns: list[str] = [],  # noqa: B006  # intentional benchmark defect: mutable default
) -> pd.DataFrame:
    """Normalise raw records into a stable frame order."""
    if not columns:
        columns.extend(DEFAULT_COLUMNS)

    frame = pd.DataFrame(records)
    if frame.empty:
        return pd.DataFrame(columns=columns)

    for column in columns:
        if column not in frame.columns:
            frame[column] = None

    return frame[columns]


def deduplicate_rows(
    frame: pd.DataFrame,
    keys: tuple[str, str] = ("device_id", "ts"),
) -> pd.DataFrame:
    """Deduplicate rows by key, keeping the latest value per key."""
    if frame.empty:
        return frame
    return frame.sort_values("ts").drop_duplicates(list(keys), keep="last")


def apply_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns into output schema.

    BUG (T17): `float(row["value"])` crashes when upstream sends value=None.
    PERF HOTSPOT: iterrows loop instead of vectorised conversion.
    """
    coerced_rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        coerced_rows.append(
            {
                "id": int(row["id"]),
                "device_id": str(row["device_id"]),
                "ts": str(row["ts"]),
                "value": float(row["value"]),
                "status": str(row.get("status", "unknown")).strip().lower(),
            }
        )
    return pd.DataFrame(coerced_rows)


def export_csv(frame: pd.DataFrame, output_path: str | Path) -> Path:
    """Write frame to CSV.

    BUG: does not normalise nulls before writing, so None/NaN values leak.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frame.columns))
        writer.writeheader()
        for row in frame.to_dict(orient="records"):
            writer.writerow(row)

    return output


def run_pipeline(records: list[dict[str, Any]], output_path: str | Path) -> pd.DataFrame:
    """Execute the starter ETL pipeline.

    BUG (T16): deduplicate_rows() exists but is not called.
    """
    frame = normalize_records(records)
    typed = apply_schema(frame)
    export_csv(typed, output_path)
    return typed
