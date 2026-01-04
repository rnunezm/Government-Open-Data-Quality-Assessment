import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import re
from dateutil.parser import parse as parse_date

# =========================
# Configuración
# =========================
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

THRESHOLDS = {
    "null_pct_col_warn": 0.05,
    "duplicated_rows_warn": 0.01,
    "valid_records_warn": 0.95,
    "inconsistency_warn": 0.01
}

SAMPLE_SIZE = 1000   # <-- Used by Streamlit for charts

# =========================
# Utlils
# =========================
def infer_type_series(s: pd.Series):
    if pd.api.types.is_numeric_dtype(s):
        return "numeric"

    sample = s.dropna().astype(str).head(100)
    if len(sample) >= 3:
        parsed = 0
        for v in sample:
            try:
                parse_date(v)
                parsed += 1
            except Exception:
                pass
        if parsed / len(sample) > 0.8:
            return "datetime"

    return "string"


def detect_start_end_pairs(cols):
    pairs = []
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["start", "from", "begin"]):
            for d in cols:
                dl = d.lower()
                if any(k in dl for k in ["end", "to", "finish"]):
                    pairs.append((c, d))
    return pairs


def _try_parse_date(x):
    try:
        parse_date(x)
        return True
    except Exception:
        return False


# =========================
# Main profiling function
# =========================
def profile_dataframe(df: pd.DataFrame, dataset_name: str = "dataset"):
    n = len(df)

    profile = {
        "dataset": dataset_name,
        "execution_date": datetime.utcnow().isoformat(),
        "row_count": n,
        "columns": [],
        "summary": {},
        "warnings": [],
        "df_sample": {}
    }

    # -------------------------
    # Stratified sample for charts
    # -------------------------
    if n > SAMPLE_SIZE:
        sample_df = df.sample(SAMPLE_SIZE, random_state=42)
    else:
        sample_df = df.copy()

    # Convert NaNs to None for JSON serialization
    profile["df_sample"] = sample_df.where(pd.notnull(sample_df), None).to_dict(orient="list")

    # -------------------------
    # Global metrics
    # -------------------------
    duplicated_rows_pct = df.duplicated().mean() if n > 0 else 0.0
    complete_rows_pct = df.dropna().shape[0] / n if n > 0 else 1.0

    # -------------------------
    # Column-wise profiling
    # -------------------------
    for col in df.columns:
        s = df[col]
        null_pct = s.isna().mean() if n > 0 else 0.0
        unique_values = s.nunique(dropna=True) if n > 0 else 0
        dtype_inferred = infer_type_series(s)
        invalid_count = 0

        min_v = max_v = mean_v = std_v = None

        if dtype_inferred == "numeric":
            coerced = pd.to_numeric(s, errors="coerce")
            invalid_count = coerced.isna().sum() - s.isna().sum()
            if coerced.notna().any():
                min_v = float(coerced.min())
                max_v = float(coerced.max())
                mean_v = float(coerced.mean())
                std_v = float(coerced.std())

        elif dtype_inferred == "datetime":
            parsed = s.astype(str).apply(_try_parse_date)
            invalid_count = (~parsed).sum()

        else:  # string
            sample_nonnull = s.dropna().astype(str).head(100)
            email_like = sample_nonnull.str.match(EMAIL_REGEX).mean() if len(sample_nonnull) else 0
            if email_like > 0.6:
                invalid_count = (~s.dropna().astype(str).str.match(EMAIL_REGEX)).sum()

        valid_pct = 1 - (invalid_count / n) if n > 0 else 1.0

        profile["columns"].append({
            "column_name": col,
            "inferred_type": dtype_inferred,
            "null_pct": float(null_pct),
            "unique_count": int(unique_values),
            "invalid_count": int(invalid_count),
            "valid_pct": float(valid_pct),
            "min": min_v,
            "max": max_v,
            "mean": mean_v,
            "std": std_v
        })

    # -------------------------
    # Start/End consistency checks
    # -------------------------
    inconsistency_count = 0
    for start_col, end_col in detect_start_end_pairs(df.columns):
        try:
            start = pd.to_datetime(df[start_col], errors="coerce")
            end = pd.to_datetime(df[end_col], errors="coerce")
            inconsistency_count += ((start.notna()) & (end.notna()) & (start > end)).sum()
        except Exception:
            pass

    inconsistency_pct = inconsistency_count / n if n > 0 else 0.0

    # -------------------------
    # Scores
    # -------------------------
    completeness_score = 1 - np.mean([c["null_pct"] for c in profile["columns"]])
    uniqueness_score = 1 - duplicated_rows_pct
    validity_score = np.mean([c["valid_pct"] for c in profile["columns"]])
    consistency_score = 1 - inconsistency_pct

    dq_score = (
        0.35 * completeness_score +
        0.25 * uniqueness_score +
        0.25 * validity_score +
        0.15 * consistency_score
    )

    profile["summary"] = {
        "duplicated_rows_pct": float(duplicated_rows_pct),
        "complete_rows_pct": float(complete_rows_pct),
        "inconsistency_pct": float(inconsistency_pct),
        "completeness_score": float(completeness_score),
        "uniqueness_score": float(uniqueness_score),
        "validity_score": float(validity_score),
        "consistency_score": float(consistency_score),
        "dq_score": float(dq_score),
        "n_columns": len(profile["columns"])
    }

    # -------------------------
    # Warnings
    # -------------------------
    if completeness_score < 1 - THRESHOLDS["null_pct_col_warn"]:
        profile["warnings"].append({
            "type": "completeness",
            "message": "Some columns have high null percentage"
        })

    if duplicated_rows_pct > THRESHOLDS["duplicated_rows_warn"]:
        profile["warnings"].append({
            "type": "uniqueness",
            "message": "Duplicated rows exceed threshold"
        })

    if validity_score < THRESHOLDS["valid_records_warn"]:
        profile["warnings"].append({
            "type": "validity",
            "message": "Low valid records percentage"
        })

    if inconsistency_pct > THRESHOLDS["inconsistency_warn"]:
        profile["warnings"].append({
            "type": "consistency",
            "message": "High inconsistency in start/end"
        })

    # -------------------------
    # Persist profile
    # -------------------------
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    with open(os.path.join(RESULTS_DIR, "latest_profile.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    with open(os.path.join(RESULTS_DIR, f"{dataset_name}_{ts}_profile.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    return profile


# =========================
# Entry point CSV
# =========================
def run_profile_from_csv(csv_path: str, dataset_name: str = None):
    if dataset_name is None:
        dataset_name = os.path.splitext(os.path.basename(csv_path))[0]
    df = pd.read_csv(csv_path, low_memory=False)
    return profile_dataframe(df, dataset_name)
