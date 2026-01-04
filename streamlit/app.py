import streamlit as st
import os, sys, json
import pandas as pd
import altair as alt
import numpy as np

# =========================
# Configuración de rutas
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(
    page_title="Data Profiling Dashboard",
    layout="wide"
)

st.title("📊 Government Open Data Quality Assessment")

# =========================
# Carga de perfil
# =========================
@st.cache_data(ttl=30)
def load_profile(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

latest_json = os.path.join(RESULTS_DIR, "latest_profile.json")

if not os.path.exists(latest_json):
    st.error("No existe results/latest_profile.json")
    st.stop()

profile = load_profile(latest_json)

summary = profile.get("summary", {})
columns = pd.DataFrame(profile.get("columns", []))
df_sample = pd.DataFrame(profile.get("df_sample", {}))

# =========================
# KPIs principales
# =========================
st.header(f"Dataset: {profile.get('dataset', 'unknown')}")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("DQ Score", f"{summary.get('dq_score', 0):.2%}")
c2.metric("Completeness", f"{summary.get('completeness_score', 0):.2%}")
c3.metric("Uniqueness", f"{summary.get('uniqueness_score', 0):.2%}")
c4.metric("Validity", f"{summary.get('validity_score', 0):.2%}")
c5.metric("Consistency", f"{summary.get('consistency_score', 0):.2%}")

st.markdown("---")

# =========================
# Warnings
# =========================
st.subheader("🚨 Warnings / Alerts")
if profile.get("warnings"):
    for w in profile["warnings"]:
        st.warning(f"{w.get('type','').capitalize()}: {w.get('message','')}")
else:
    st.success("There are no warnings.")

st.markdown("---")

# =========================
# Tabla de columnas
# =========================
st.subheader("📋 Column Details")

display_cols = [
    "column_name","inferred_type","null_pct","unique_count",
    "invalid_count","valid_pct","min","max","mean","std"
]

for c in display_cols:
    if c not in columns.columns:
        columns[c] = None

df_display = columns[display_cols].copy()
df_display["null_pct"] = df_display["null_pct"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")
df_display["valid_pct"] = df_display["valid_pct"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")

st.dataframe(df_display, use_container_width=True)

st.markdown("---")

# =========================
# Heatmap de calidad
# =========================
st.subheader("🔥 Quality Heatmap")

if not columns.empty:
    heat = columns.melt(
        id_vars=["column_name"],
        value_vars=["null_pct", "valid_pct"]
    )

    heat_chart = alt.Chart(heat).mark_rect().encode(
        x=alt.X("variable:N", title="Métrica"),
        y=alt.Y("column_name:N", title="Columna"),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(domain=[0, 1], scheme="redyellowgreen")
        ),
        tooltip=["column_name", "variable", "value"]
    ).properties(height=400)

    st.altair_chart(heat_chart, use_container_width=True)

st.markdown("---")

# =========================
# Numeric Stats
# =========================
def numeric_stats(series: pd.Series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return None
    return {
        "min": float(s.min()),
        "max": float(s.max()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "p25": float(np.percentile(s, 25)),
        "p50": float(np.percentile(s, 50)),
        "p75": float(np.percentile(s, 75)),
    }

# =========================
# Statistics by Feature
# =========================
st.header("📈 Statistics by Feature")

if df_sample.empty:
    st.warning("There is no df_sample in the profile to calculate statistics.")
else:
    for _, col in columns.iterrows():
        col_name = col["column_name"]
        col_type = col["inferred_type"]

        st.subheader(f"🔹 {col_name}")
        st.caption(f"Tipo inferido: {col_type}")

        if col_name not in df_sample.columns:
            st.info("There is no sample data for this column.")
            continue

        s = df_sample[col_name]

        # ---------- NUMERIC ----------
        if col_type == "numeric":
            stats = numeric_stats(s)
            if not stats:
                st.info("There are no valid numeric values.")
                continue

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Min", f"{stats['min']:.2f}")
            c2.metric("Max", f"{stats['max']:.2f}")
            c3.metric("Mean", f"{stats['mean']:.2f}")
            c4.metric("Std", f"{stats['std']:.2f}")

            st.markdown(
                f"""
                **Percentiles**
                - P25: {stats['p25']:.2f}
                - P50 (Mediana): {stats['p50']:.2f}
                - P75: {stats['p75']:.2f}
                """
            )

            chart = alt.Chart(pd.DataFrame({col_name: s})).mark_bar().encode(
                x=alt.X(col_name, bin=True),
                y="count()"
            ).properties(height=250)

            st.altair_chart(chart, use_container_width=True)

        # ---------- STRING ----------
        elif col_type == "string":
            vc = s.astype(str).value_counts().head(15).reset_index()
            vc.columns = [col_name, "count"]

            st.metric("Valores únicos", s.nunique())
            if not s.mode().empty:
                st.metric("Moda", s.mode().iloc[0])

            chart = alt.Chart(vc).mark_bar().encode(
                x=alt.X(col_name, sort="-y"),
                y="count",
                tooltip=[col_name, "count"]
            ).properties(height=250)

            st.altair_chart(chart, use_container_width=True)

        # ---------- DATETIME ----------
        elif col_type == "datetime":
            s_dt = pd.to_datetime(s, errors="coerce").dropna()
            if s_dt.empty:
                st.info(" There are no valid dates.")
                continue

            c1, c2 = st.columns(2)
            c1.metric("Fecha mínima", s_dt.min().strftime("%Y-%m-%d"))
            c2.metric("Fecha máxima", s_dt.max().strftime("%Y-%m-%d"))

            chart = alt.Chart(pd.DataFrame({"date": s_dt})).mark_bar().encode(
                x=alt.X("date:T", bin=alt.Bin(maxbins=40)),
                y="count()"
            ).properties(height=250)

            st.altair_chart(chart, use_container_width=True)

        else:
            st.info("Data type not supported.")

st.markdown("---")
st.caption(f"Perfil generado: {profile.get('execution_date','')}")
