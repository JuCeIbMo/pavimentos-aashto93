"""Tema visual de la aplicación: CSS global + aplicación del estilo."""

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {
  --amber: #E9A800;
  --amber-2: #F5B301;
  --amber-dark: #C78E00;
  --ink: #101828;
  --muted: #667085;
  --bg: #F5F6F8;
  --card: #FFFFFF;
  --line: #E7E9EE;
}

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; }

h1, h2, h3, h4 { font-family: 'Sora', 'Inter', sans-serif; letter-spacing: -0.02em; color: var(--ink); }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E1219 0%, #151A24 100%);
  border-right: 1px solid #232A36;
}
[data-testid="stSidebar"] > div { background: transparent; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown { color: #E7E9EE; }

.brand { display: flex; align-items: center; gap: .75rem; padding: .25rem 0 .9rem; }
.brand-mark { width: 2.6rem; height: 2.6rem; border-radius: .8rem; background: linear-gradient(135deg,#F5B301,#E09E00); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; box-shadow: 0 4px 14px rgba(233,168,0,.4); }
.brand-name { font-family: 'Sora', sans-serif; font-weight: 800; letter-spacing: .06em; color: #fff; font-size: 1.02rem; }
.brand-sub { color: #8A93A3; font-size: .76rem; }

[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: .55rem .8rem; border-radius: .6rem; margin: .12rem 0;
  border: 1px solid transparent; color: #C6CCD6; transition: all .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.05); }
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
  background: rgba(233,168,0,.14); border-color: rgba(233,168,0,.35); color: #fff;
}
[data-testid="stSidebar"] [role="radiogroup"] label p { color: inherit !important; }

/* ---------- Botones ---------- */
.stButton button, .stDownloadButton button {
  border-radius: .65rem; font-weight: 600; border: 1px solid var(--line);
  background: #fff; color: var(--ink); padding: .55rem 1.1rem; transition: all .15s ease;
}
.stButton button:hover, .stDownloadButton button:hover { border-color: var(--amber); color: var(--amber-dark); }
.stButton button[kind="primary"] {
  background: linear-gradient(180deg, #F5B301, #E09E00); border: none; color: #1A1400;
  box-shadow: 0 4px 14px rgba(233,168,0,.35);
}
.stButton button[kind="primary"]:hover { background: #F5B301; }

/* ---------- KPI cards ---------- */
.kpi-card {
  background: var(--card); border: 1px solid var(--line); border-radius: 1rem;
  padding: 1.1rem 1.2rem; min-height: 6.6rem; box-shadow: 0 1px 2px rgba(16,24,40,.04);
}
.kpi-label { font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.kpi-value { font-size: 1.85rem; font-weight: 800; color: var(--ink); margin: .2rem 0; font-variant-numeric: tabular-nums; letter-spacing: -.02em; line-height: 1.1; }
.kpi-sub { font-size: .8rem; color: var(--muted); }

/* ---------- Page head ---------- */
.page-head { display: flex; align-items: center; gap: 1rem; margin: .25rem 0 1.25rem; }
.page-badge { width: 3rem; height: 3rem; border-radius: .85rem; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg,#F5B301,#E09E00); color: #1A1400; font-family: 'Sora'; font-weight: 800; font-size: 1.1rem; box-shadow: 0 6px 16px rgba(233,168,0,.35); }
.page-title { font-size: 1.6rem; font-weight: 800; letter-spacing: -.02em; margin: 0; color: var(--ink); line-height: 1.15; }
.page-sub { color: var(--muted); margin: .25rem 0 0; }

/* ---------- Secciones ---------- */
.section-title { font-family: 'Sora'; font-size: 1rem; font-weight: 700; color: var(--ink); margin: 0 0 .15rem; }
.section-sub { color: var(--muted); font-size: .85rem; margin: 0 0 .6rem; }

/* ---------- Hero (Inicio) ---------- */
.hero {
  background: linear-gradient(135deg, #0E1219 0%, #1A2230 55%, #243042 100%);
  border-radius: 1.25rem; padding: 2.6rem 2.75rem; color: #fff; position: relative; overflow: hidden; margin-bottom: 1.5rem;
}
.hero-kicker { font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--amber-2); }
.hero h1 { color: #fff; font-size: 2.35rem; font-weight: 800; letter-spacing: -.03em; margin: .4rem 0 .6rem; line-height: 1.05; }
.hero p { color: #C6CCD6; font-size: 1.05rem; max-width: 48rem; margin: 0 0 1.25rem; }
.road-line { height: 4px; width: 16rem; background-image: repeating-linear-gradient(90deg, var(--amber-2) 0 20px, transparent 20px 34px); border-radius: 2px; }
.hero-chips { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: 1.4rem; }
.chip { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 2rem; padding: .3rem .8rem; font-size: .8rem; color: #E7E9EE; }

/* ---------- Step cards (Inicio) ---------- */
.step-num { color: var(--amber-dark); font-weight: 800; font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
.step-title { font-weight: 700; color: var(--ink); margin: .2rem 0 .3rem; font-size: 1.05rem; }
.step-desc { color: var(--muted); font-size: .87rem; line-height: 1.45; }

/* Botones de la barra lateral: texto oscuro legible sobre fondo claro */
[data-testid="stSidebar"] .stButton button p, [data-testid="stSidebar"] .stDownloadButton button p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] p, [data-testid="stSidebar"] [data-testid="stFileUploader"] small,
[data-testid="stSidebar"] [data-testid="stFileUploader"] span { color: #101828 !important; }
[data-testid="stSidebar"] .stDownloadButton button { background: #E9A800; border-color: #E9A800; }

/* ---------- Tablas ---------- */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: .8rem; overflow: hidden; }

/* ---------- Expander ---------- */
[data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: .7rem; }
"""


def aplicar_tema() -> None:
    """Inyecta el CSS global. Debe llamarse en cada recarga: Streamlit borra los
    elementos que no se vuelven a dibujar, incluido el <style>."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
