"""Jakarta Rental Dashboard.

Interactive Streamlit dashboard for exploring rental property listings
across Greater Jakarta: filters, KPI cards, and four analytical views
(scatter, bar, pie, correlation heatmap) plus dynamically computed insights.

Run with: ``streamlit run app.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jakarta_rentals.csv")
GENERATOR_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "generator.py")

st.set_page_config(page_title="Jakarta Rental Dashboard", layout="wide")


@st.cache_data
def load_data() -> Optional[pd.DataFrame]:
    """Load the rental dataset, generating it first if missing.

    Returns:
        The dataset as a DataFrame, or ``None`` if loading failed.
    """
    try:
        if not os.path.exists(DATA_PATH):
            # Auto-run the generator so the app works on a fresh clone.
            exit_code = os.system(f'"{sys.executable}" "{GENERATOR_PATH}"')
            if exit_code != 0:
                subprocess.run([sys.executable, GENERATOR_PATH], check=True)
        return pd.read_csv(DATA_PATH)
    except (OSError, subprocess.CalledProcessError, pd.errors.ParserError) as exc:
        st.error(f"Gagal memuat data: {exc}")
        return None


def apply_filters(
    df: pd.DataFrame,
    lokasi: List[str],
    tipe: List[str],
    harga_max: int,
    luas_min: float,
    dekat_mrt: bool,
) -> pd.DataFrame:
    """Apply sidebar filters to the dataset.

    Args:
        df: Full dataset.
        lokasi: Selected locations (empty = all).
        tipe: Selected unit types (empty = all).
        harga_max: Maximum monthly rent in IDR.
        luas_min: Minimum unit area in m2.
        dekat_mrt: If True, keep only listings within 1 km of an MRT station.

    Returns:
        The filtered DataFrame (may be empty).
    """
    try:
        filtered = df.copy()
        if lokasi:
            filtered = filtered[filtered["lokasi"].isin(lokasi)]
        if tipe:
            filtered = filtered[filtered["tipe"].isin(tipe)]
        filtered = filtered[filtered["harga_sewa_bulan"] <= harga_max]
        filtered = filtered[filtered["luas_m2"] >= luas_min]
        if dekat_mrt:
            filtered = filtered[filtered["jarak_ke_mrt_km"] < 1.0]
        return filtered
    except KeyError as exc:
        st.error(f"Kolom tidak ditemukan saat memfilter: {exc}")
        return df


def compute_insights(df: pd.DataFrame) -> List[str]:
    """Compute three dynamic insights from the (filtered) dataset.

    Args:
        df: Filtered dataset.

    Returns:
        A list of insight strings; an explanatory message if data is empty.
    """
    try:
        if df.empty:
            return ["Tidak ada data yang cocok dengan filter saat ini."]

        loc_mean = df.groupby("lokasi")["harga_sewa_bulan"].mean()
        most_expensive_loc = loc_mean.idxmax()

        near = df[df["jarak_ke_mrt_km"] < 1.0]["harga_sewa_bulan"].mean()
        far = df[df["jarak_ke_mrt_km"] >= 1.0]["harga_sewa_bulan"].mean()
        mrt_premium = ((near - far) / far * 100) if far and not np.isnan(near) else 0.0

        df_valid = df[df["luas_m2"] > 0]
        per_m2 = (df_valid["harga_sewa_bulan"] / df_valid["luas_m2"]).mean()

        return [
            f"📍 Lokasi termahal: **{most_expensive_loc}** "
            f"(rata-rata Rp {loc_mean.max():,.0f}/bulan)",
            f"🚇 Premium dekat MRT (<1 km): **{mrt_premium:+.1f}%** vs listing lainnya",
            f"📐 Harga rata-rata per m²: **Rp {per_m2:,.0f}/bulan**",
        ]
    except (KeyError, ZeroDivisionError) as exc:
        return [f"Gagal menghitung insight: {exc}"]


def main() -> None:
    """Render the dashboard."""
    try:
        st.title("🏙️ Jakarta Rental Dashboard")
        st.caption("Analisis 800 listing sewa apartemen di Jabodetabek")

        df = load_data()
        if df is None or df.empty:
            st.stop()

        # ----- Sidebar filters -----
        st.sidebar.header("🔎 Filter")
        lokasi = st.sidebar.multiselect("Lokasi", sorted(df["lokasi"].unique()))
        tipe = st.sidebar.multiselect("Tipe Unit", sorted(df["tipe"].unique()))
        harga_max = st.sidebar.slider(
            "Harga Maksimum (Rp)", 0, 20_000_000, 20_000_000, step=500_000
        )
        luas_min = st.sidebar.number_input("Luas Minimum (m²)", min_value=0.0, value=0.0, step=5.0)
        dekat_mrt = st.sidebar.checkbox("Hanya dekat MRT (< 1 km)")

        filtered = apply_filters(df, lokasi, tipe, harga_max, luas_min, dekat_mrt)

        # ----- Sidebar insights -----
        st.sidebar.markdown("---")
        st.sidebar.subheader("💡 Insight")
        for insight in compute_insights(filtered):
            st.sidebar.info(insight)

        # ----- KPI cards -----
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Listings", f"{len(filtered):,}")
        avg_price = filtered["harga_sewa_bulan"].mean() if not filtered.empty else 0
        col2.metric("Rata-rata Harga", f"Rp {avg_price:,.0f}")
        near_mrt = int((filtered["jarak_ke_mrt_km"] < 1.0).sum()) if not filtered.empty else 0
        col3.metric("Listing Dekat MRT", f"{near_mrt:,}")

        if filtered.empty:
            st.warning("Tidak ada listing yang cocok dengan filter. Longgarkan kriteria Anda.")
            st.stop()

        # ----- Tabs -----
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📈 Harga vs Luas", "📊 Harga per Lokasi", "🥧 Komposisi Tipe", "🔥 Korelasi"]
        )

        with tab1:
            fig = px.scatter(
                filtered,
                x="luas_m2",
                y="harga_sewa_bulan",
                color="lokasi",
                hover_data=["nama_property", "tipe", "rating_review"],
                title="Harga Sewa vs Luas Unit",
                labels={"luas_m2": "Luas (m²)", "harga_sewa_bulan": "Harga Sewa/Bulan (Rp)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            mean_by_loc = (
                filtered.groupby("lokasi")["harga_sewa_bulan"]
                .mean()
                .sort_values(ascending=False)
                .reset_index()
            )
            fig = px.bar(
                mean_by_loc,
                x="lokasi",
                y="harga_sewa_bulan",
                color="lokasi",
                title="Rata-rata Harga Sewa per Lokasi",
                labels={"lokasi": "Lokasi", "harga_sewa_bulan": "Rata-rata Harga (Rp)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            tipe_counts = filtered["tipe"].value_counts().reset_index()
            tipe_counts.columns = ["tipe", "jumlah"]
            fig = px.pie(
                tipe_counts, names="tipe", values="jumlah", title="Komposisi Tipe Unit", hole=0.35
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            numeric_cols = ["luas_m2", "harga_sewa_bulan", "jarak_ke_mrt_km", "rating_review"]
            corr = filtered[numeric_cols].corr()
            fig = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="Korelasi Antar Variabel Numerik",
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Lihat Data Mentah"):
            st.dataframe(filtered, use_container_width=True)

    except Exception as exc:
        st.error(f"Terjadi kesalahan pada dashboard: {exc}")


if __name__ == "__main__":
    main()
