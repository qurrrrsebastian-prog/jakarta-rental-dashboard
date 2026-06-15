"""
Phase 1 Theme: Ocean Blue. Author: Avatar Putra Sigit.
"""
import streamlit as st


def inject_phase1_theme() -> None:
    """Inject custom CSS for Phase 1 Data & Analytics theme."""
    st.markdown("""
    <style>
        /* Global Theme */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        }
        .main .block-container {
            background: rgba(15, 23, 42, 0.95);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        /* Typography */
        h1, h2, h3 {
            color: #e2e8f0 !important;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        h1 { font-weight: 700; letter-spacing: -0.02em; }
        p, label, .stMarkdown { color: #cbd5e1 !important; }

        /* Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #0ea5e9, #0284c7) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100%;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(14, 165, 233, 0.4) !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0c4a6e 0%, #0f172a 100%) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.1);
        }
        [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0 !important; }

        /* Cards / Metrics */
        [data-testid="stMetric"] {
            background: rgba(30, 58, 95, 0.6) !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            border: 1px solid rgba(148, 163, 184, 0.1) !important;
        }
        [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
        [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 700 !important; }

        /* DataFrames */
        .stDataFrame {
            background: rgba(30, 58, 95, 0.4) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.1) !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: rgba(30, 58, 95, 0.6) !important;
            border-radius: 12px !important;
            color: #e2e8f0 !important;
            font-weight: 600 !important;
        }
        .streamlit-expanderContent {
            background: rgba(15, 23, 42, 0.8) !important;
            border-radius: 0 0 12px 12px !important;
        }

        /* Inputs */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
            background: rgba(30, 58, 95, 0.6) !important;
            color: #e2e8f0 !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 10px !important;
        }

        /* Spinner / Loading */
        .stSpinner > div {
            border-top-color: #38bdf8 !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

        /* Responsive Mobile */
        @media (max-width: 768px) {
            .main .block-container { padding: 1rem !important; }
            h1 { font-size: 1.5rem !important; }
            .stButton>button { font-size: 14px !important; padding: 0.5rem 1rem !important; }
            [data-testid="stMetric"] { padding: 0.5rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)


def show_loading_skeleton(text: str = "Loading...") -> None:
    """Show professional loading state."""
    st.markdown(f"""
    <div style="padding: 2rem; text-align: center;">
        <div style="font-size: 1.2rem; color: #38bdf8; margin-bottom: 1rem;">⏳ {text}</div>
        <div style="width: 100%; height: 4px; background: rgba(30,58,95,0.6); border-radius: 2px; overflow: hidden;">
            <div style="width: 50%; height: 100%; background: linear-gradient(90deg, #0ea5e9, #38bdf8); border-radius: 2px; animation: pulse 1.5s infinite;"></div>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ transform: translateX(-100%); }}
                100% {{ transform: translateX(200%); }}
            }}
        </style>
    </div>
    """, unsafe_allow_html=True)
