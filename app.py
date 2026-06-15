"""Jakarta Rental Dashboard — Bintang 5.

Interactive Streamlit dashboard for exploring rental property listings
across Greater Jakarta: filters, KPI cards, four analytical views
(scatter, bar, pie, correlation heatmap), a folium sebaran map, and
dynamically computed insights.

Upgraded with the shared "Phase 1" architecture: Ocean-Blue theme, SQLite
search history, input sanitization, and a loading skeleton. All original
analysis logic is preserved unchanged.

Run with: ``streamlit run app.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import folium
from streamlit_folium import st_folium

from core.database import init_db, save_query, get_history, seed_dummy_data, get_dummy_data
from core.security import sanitize_input, mask_api_key, generate_session_id
from core.theme import inject_phase1_theme, show_loading_skeleton
from data.seeder import seed_apartments

DATA_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jakarta_rentals.csv")
GENERATOR_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "generator.py")

# Approximate area centroids (lat, lon) for the sebaran map. Listings are
# jittered deterministically around these so the map is stable across reruns.
AREA_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "Jakarta Pusat": (-6.1865, 106.8340),
    "Jakarta Selatan": (-6.2615, 106.8106),
    "Jakarta Utara": (-6.1214, 106.8890),
    "Jakarta Timur": (-6.2250, 106.9004),
    "Jakarta Barat": (-6.1670, 106.7637),
    "Bekasi": (-6.2383, 106.9756),
    "Depok": (-6.4025, 106.7942),
    "Tangerang": (-6.1783, 106.6319),
}

st.set_page_config(page_title="Jakarta Rental Dashboard", layout="wide")
inject_phase1_theme()


def inject_ui_layout_fixes() -> None:
    """Inject layout-only CSS (no color changes): KPI text + responsive mobile.

    On mobile (<768px) the KPI cards reflow into a 2x2 grid and the folium
    map iframe shrinks to the viewport width.
    """
    st.markdown(
        """
        <style>
            [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
                white-space: normal !important; overflow: visible !important;
                font-size: 0.85rem !important; line-height: 1.2 !important;
            }
            [data-testid="stMetricValue"] {
                white-space: normal !important; overflow: visible !important;
                font-size: 1.5rem !important;
            }
            iframe { max-width: 100% !important; }
            @media (max-width: 768px) {
                [data-testid="stHorizontalBlock"] {
                    flex-wrap: wrap !important; gap: 0.5rem !important;
                }
                [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                    flex: 1 1 45% !important; min-width: 45% !important;
                }
                iframe { height: 320px !important; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_ui_layout_fixes()


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


def _price_color(price: float, thresholds: Tuple[float, float]) -> str:
    """Return a marker color based on price tier (low/mid/high)."""
    low, high = thresholds
    if price <= low:
        return "#22c55e"
    if price >= high:
        return "#ef4444"
    return "#eab308"


def render_map(df: pd.DataFrame) -> None:
    """Render a folium sebaran map of the (filtered) listings.

    Listings are placed at deterministically jittered positions around their
    area centroid and colour-coded by price tier. Capped at 250 markers for
    responsiveness.

    Args:
        df: Filtered dataset with ``lokasi`` and ``harga_sewa_bulan``.
    """
    try:
        import random

        if df.empty:
            st.info("Tidak ada listing untuk dipetakan.")
            return

        low = float(df["harga_sewa_bulan"].quantile(0.33))
        high = float(df["harga_sewa_bulan"].quantile(0.66))

        fmap = folium.Map(location=[-6.21, 106.84], zoom_start=11, tiles="CartoDB dark_matter")
        sample = df.head(250)
        for _, row in sample.iterrows():
            base = AREA_CENTROIDS.get(str(row["lokasi"]), (-6.21, 106.84))
            rng = random.Random(int(row.get("id", 0)))
            lat = base[0] + rng.uniform(-0.025, 0.025)
            lon = base[1] + rng.uniform(-0.025, 0.025)
            price = float(row["harga_sewa_bulan"])
            popup = folium.Popup(
                f"<b>{sanitize_input(str(row.get('nama_property', '-')), 80)}</b><br>"
                f"{row['lokasi']} • {row.get('tipe', '-')}<br>"
                f"Rp {price:,.0f}/bln • {row['luas_m2']:.0f} m²",
                max_width=240,
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color=_price_color(price, (low, high)),
                fill=True,
                fill_opacity=0.75,
                weight=1,
                popup=popup,
            ).add_to(fmap)

        st_folium(fmap, height=480, width=None, returned_objects=[])
        st.caption(
            "🟢 ≤ P33 harga • 🟡 menengah • 🔴 ≥ P66 harga · "
            f"menampilkan {len(sample)} dari {len(df)} listing"
        )
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Peta gagal dirender: {exc}")


def render_recent_history() -> None:
    """Render the recent-search-history section in the sidebar."""
    try:
        st.sidebar.divider()
        st.sidebar.header("🕒 Recent History")
        history = get_history(limit=5)
        if not history:
            st.sidebar.caption("Belum ada riwayat pencarian.")
            return
        for row in history:
            st.sidebar.markdown(
                f"**{str(row.get('timestamp', ''))[:16]}**  \n"
                f"{row.get('query', '')}  \n"
                f"<span style='color:#94a3b8'>{row.get('result_summary', '')}</span>",
                unsafe_allow_html=True,
            )
    except Exception as exc:  # pragma: no cover - defensive
        st.sidebar.caption(f"History error: {exc}")


def main() -> None:
    """Render the dashboard."""
    try:
        # ----- Shared-architecture bootstrap -----
        init_db()
        # Generate apartments.csv + seed dummy_data on first run (idempotent).
        seed_apartments()
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = generate_session_id()
        session_id: str = st.session_state["session_id"]

        st.title("🏙️ Jakarta Rental Dashboard")
        st.caption("Analisis 800 listing sewa apartemen di Jabodetabek")

        # ----- Data load (with skeleton) -----
        placeholder = st.empty()
        with placeholder.container():
            show_loading_skeleton("Memuat data listing...")
        df = load_data()
        placeholder.empty()
        if df is None or df.empty:
            st.stop()

        # ----- Sidebar filters (sanitized) -----
        st.sidebar.header("🔎 Filter")
        lokasi_raw = st.sidebar.multiselect("Lokasi", sorted(df["lokasi"].unique()))
        tipe_raw = st.sidebar.multiselect("Tipe Unit", sorted(df["tipe"].unique()))
        # Sanitize selections defensively before they drive queries/filters.
        lokasi = [sanitize_input(x, max_length=40) for x in lokasi_raw]
        tipe = [sanitize_input(x, max_length=20) for x in tipe_raw]
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

        # ----- Recent search history (from SQLite) -----
        render_recent_history()

        # ----- Persist this search to history -----
        query_desc = sanitize_input(
            f"lokasi={lokasi or 'all'}, tipe={tipe or 'all'}, "
            f"harga<= {harga_max}, luas>= {luas_min}, mrt={dekat_mrt}",
            max_length=160,
        )
        avg_price_all = filtered["harga_sewa_bulan"].mean() if not filtered.empty else 0
        save_query(query_desc, f"{len(filtered)} listing | avg Rp {avg_price_all:,.0f}", session_id)

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

        # ----- Tabs (existing 4 views + new sebaran map) -----
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📈 Harga vs Luas", "📊 Harga per Lokasi", "🥧 Komposisi Tipe", "🔥 Korelasi", "🗺️ Peta Sebaran"]
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
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch")

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
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch")

        with tab3:
            tipe_counts = filtered["tipe"].value_counts().reset_index()
            tipe_counts.columns = ["tipe", "jumlah"]
            fig = px.pie(
                tipe_counts, names="tipe", values="jumlah", title="Komposisi Tipe Unit", hole=0.35
            )
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch")

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
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch")

        with tab5:
            map_placeholder = st.empty()
            with map_placeholder.container():
                show_loading_skeleton("Merender peta sebaran...")
            map_placeholder.empty()
            render_map(filtered)

        with st.expander("📋 Lihat Data Mentah"):
            st.dataframe(filtered, width="stretch")

    except Exception as exc:
        st.error(f"Terjadi kesalahan pada dashboard: {exc}")


if __name__ == "__main__":
    main()
