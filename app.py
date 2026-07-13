import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json, os, time, math

from core.convergence import S3ConvergenceEngine
from core.allocator import S3AntiFragileAllocator
from config import MONITORED_ASSETS, REGIMES, THRESHOLDS, SYMBOL_MAP

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HYDRA-S3 | ENTERPRISE QUANT TERMINAL",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="expanded",
)

STATE_FILE = "enterprise_state.json"

# ── MASTER CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

/* ── ROOT OVERRIDES ─────────────────────────── */
html, body, .main, [class*="css"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    background-color: #05070a !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0a0d14 !important;
    border-right: 1px solid #1c2333 !important;
}
[data-testid="stSidebar"] > div:first-child { background-color: #0a0d14 !important; }
section[data-testid="stSidebar"] * { color: #e6edf3 !important; }

/* ── HIDE DEFAULT STREAMLIT CHROME ─────────── */
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 0.5rem !important; max-width: 100% !important; }

/* ── SCROLLBARS ─────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

/* ── TYPOGRAPHY ─────────────────────────────── */
.mono { font-family: 'JetBrains Mono', monospace !important; }
.t-xs  { font-size: 11px; }
.t-sm  { font-size: 12px; }
.t-md  { font-size: 14px; }
.t-lg  { font-size: 16px; }
.t-xl  { font-size: 20px; }
.t-xxl { font-size: 28px; font-weight: 800; }
.muted { color: #6e7681 !important; }
.accent { color: #00ffcc !important; }
.danger { color: #ff4444 !important; }
.warn   { color: #f0a430 !important; }
.safe   { color: #3fb950 !important; }
.blue   { color: #388bfd !important; }

/* ── TERMINAL HEADER BAR ────────────────────── */
.terminal-header {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 100%);
    border-bottom: 2px solid #00ffcc;
    padding: 14px 24px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex; align-items: center; justify-content: space-between;
}
.terminal-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px; font-weight: 700;
    color: #00ffcc; letter-spacing: 3px;
}
.terminal-timestamp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: #6e7681;
}

/* ── KPI CARDS ──────────────────────────────── */
.kpi-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-top: 2px solid #00ffcc;
    border-radius: 4px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, rgba(0,255,204,0.03) 0%, transparent 60%);
    pointer-events: none;
}
.kpi-label { font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #6e7681; margin-bottom: 6px; }
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: clamp(14px, 1.5vw, 22px); font-weight: 700; color: #00ffcc; line-height: 1.1;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kpi-delta { font-size: 11px; margin-top: 4px; color: #6e7681; }
.kpi-card.danger-card { border-top-color: #ff4444; }
.kpi-card.danger-card .kpi-value { color: #ff4444; }
.kpi-card.warn-card { border-top-color: #f0a430; }
.kpi-card.warn-card .kpi-value { color: #f0a430; }
.kpi-card.blue-card { border-top-color: #388bfd; }
.kpi-card.blue-card .kpi-value { color: #388bfd; }
.kpi-card.safe-card { border-top-color: #3fb950; }
.kpi-card.safe-card .kpi-value { color: #3fb950; }

/* ── S-ALERT BANNER ─────────────────────────── */
.s-alert {
    background: linear-gradient(90deg, #1a0000, #2d0000, #1a0000);
    border: 1px solid #ff0033;
    border-left: 4px solid #ff0033;
    color: #ff4444;
    padding: 14px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px; font-weight: 700; letter-spacing: 2px;
    animation: pulse-alert 1.4s ease-in-out infinite;
    margin-bottom: 16px;
    border-radius: 2px;
}
@keyframes pulse-alert {
    0%,100% { opacity:1; box-shadow: 0 0 0 rgba(255,0,51,0.4); }
    50% { opacity:.85; box-shadow: 0 0 20px rgba(255,0,51,0.3); }
}

/* ── SECTION HEADERS ────────────────────────── */
.section-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 700; letter-spacing: 3px;
    color: #6e7681; text-transform: uppercase;
    border-bottom: 1px solid #21262d;
    padding-bottom: 8px; margin-bottom: 16px;
}

/* ── MATRIX TABLE ───────────────────────────── */
.matrix-wrap { overflow-x: auto; border: 1px solid #21262d; border-radius: 4px; }
.matrix-table {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 13px;
    background: #0d1117;
}
.matrix-table thead tr { background: #0a0d14; border-bottom: 2px solid #21262d; }
.matrix-table th {
    padding: 10px 16px; text-align: left;
    font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #6e7681;
}
.matrix-table tbody tr { border-bottom: 1px solid #161b22; transition: background .15s; }
.matrix-table tbody tr:hover { background: #161b22; }
.matrix-table td { padding: 12px 16px; }
.asset-name { font-weight: 700; color: #e6edf3; font-size: 14px; }
.score-val { color: #00ffcc; font-weight: 600; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 3px;
    font-size: 11px; font-weight: 700; letter-spacing: 1px;
}
.badge-inevitable { background:#1a0008; color:#ff4444; border:1px solid #ff2244; animation:pulse-badge 1.4s infinite; }
.badge-high       { background:#001a14; color:#00ffcc; border:1px solid #00cc99; }
.badge-noise      { background:#0d1117; color:#6e7681; border:1px solid #30363d; }
.badge-gap        { background:#0d1117; color:#f0a430; border:1px solid #f0a430; }
.badge-regime-c   { background:#1a0000; color:#ff6b6b; border:1px solid #662222; }
.badge-regime-e   { background:#001a06; color:#3fb950; border:1px solid #226633; }
.badge-regime-s   { background:#0d1117; color:#8b949e; border:1px solid #30363d; }
.badge-long       { background:#001a06; color:#3fb950; border:1px solid #226633; }
.badge-short      { background:#1a0000; color:#ff6b6b; border:1px solid #662222; }
.badge-neutral    { background:#0d1117; color:#8b949e; border:1px solid #30363d; }
@keyframes pulse-badge {
    0%,100%{box-shadow:0 0 0 rgba(255,34,68,0);} 50%{box-shadow:0 0 8px rgba(255,34,68,0.4);}
}

/* ── SIDEBAR NAV ────────────────────────────── */
[data-testid="stRadio"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important; letter-spacing: 1px !important;
    padding: 6px 0 !important; color: #8b949e !important;
}
[data-testid="stRadio"] label:has(input:checked) { color: #00ffcc !important; }

/* ── BUTTONS ────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg,#1f6feb,#0d4fa8) !important;
    color: #fff !important; border: 1px solid #388bfd !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: 1px !important; border-radius: 3px !important;
    padding: 6px 16px !important; width: 100% !important;
    transition: all .2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#388bfd,#1f6feb) !important;
    box-shadow: 0 0 12px rgba(56,139,253,0.4) !important;
    transform: translateY(-1px) !important;
}
.execute-btn > button {
    background: linear-gradient(135deg,#0d2b00,#1a3d00) !important;
    border-color: #3fb950 !important; color: #3fb950 !important;
}
.sell-btn > button {
    background: linear-gradient(135deg,#2d0000,#3d0000) !important;
    border-color: #ff4444 !important; color: #ff4444 !important;
}

/* ── METRICS ────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 24px !important; font-weight: 700 !important; color: #00ffcc !important;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important; letter-spacing: 2px !important;
    color: #6e7681 !important; font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: 12px !important; }
[data-testid="metric-container"] {
    background: #0d1117 !important; border: 1px solid #21262d !important;
    border-top: 2px solid #00ffcc !important; padding: 16px !important;
    border-radius: 4px !important;
}

/* ── DATAFRAME ──────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #21262d !important; border-radius: 4px !important;
}
.dvn-scroller { background: #0d1117 !important; }

/* ── SELECTBOX / INPUTS ─────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div > input {
    background: #0d1117 !important; border-color: #30363d !important;
    color: #e6edf3 !important; font-family: 'JetBrains Mono', monospace !important;
}

/* ── DIVIDER ────────────────────────────────── */
hr { border-color: #21262d !important; margin: 12px 0 !important; }

/* ── STATUS DOT ─────────────────────────────── */
.dot-live { display:inline-block;width:8px;height:8px;border-radius:50%;
    background:#3fb950;box-shadow:0 0 6px #3fb950;animation:dot-pulse 2s infinite;margin-right:6px; }
.dot-off  { display:inline-block;width:8px;height:8px;border-radius:50%;
    background:#ff4444;margin-right:6px; }
@keyframes dot-pulse { 0%,100%{opacity:1;}50%{opacity:0.4;} }

/* ── FORM ───────────────────────────────────── */
[data-testid="stForm"] {
    background: #0d1117 !important; border: 1px solid #21262d !important;
    border-radius: 4px !important; padding: 20px !important;
}

/* ── INFO / SUCCESS / WARNING ───────────────── */
[data-testid="stAlert"] {
    background: #0d1117 !important; border-color: #30363d !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── API HEALTH CARD ────────────────────────── */
.api-card {
    background: #0d1117; border: 1px solid #21262d; border-radius: 4px;
    padding: 14px; text-align: center; position: relative;
}
.api-name { font-size:10px;letter-spacing:2px;color:#6e7681;font-weight:700;margin-bottom:6px; }
.api-status-on  { color:#3fb950;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px; }
.api-status-off { color:#ff4444;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px; }
.api-status-unk { color:#f0a430;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px; }

/* ── TRADE ROWS ─────────────────────────────── */
.trade-row-pos { color: #3fb950 !important; }
.trade-row-neg { color: #ff4444 !important; }

/* ── SIDEBAR BRAND ──────────────────────────── */
.sidebar-brand {
    text-align:center; padding: 20px 0 16px;
    border-bottom: 1px solid #1c2333; margin-bottom: 16px;
}
.sidebar-brand h1 {
    font-family:'JetBrains Mono',monospace;
    font-size:24px;font-weight:700;color:#00ffcc;
    letter-spacing:3px;margin:0;
}
.sidebar-brand p { font-size:10px;color:#6e7681;letter-spacing:2px;margin:4px 0 0; }

/* ── STAT PILL ──────────────────────────────── */
.stat-pill {
    display:inline-flex;align-items:center;gap:8px;
    background:#0d1117;border:1px solid #21262d;border-radius:3px;
    padding:8px 14px;margin:4px 0;width:100%;
}
.stat-pill-label { font-size:10px;color:#6e7681;letter-spacing:1px;flex:1; }
.stat-pill-val   { font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;color:#e6edf3; }
</style>
""", unsafe_allow_html=True)


# ── STATE MANAGEMENT ─────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "equity": 100000.0, "initial_capital": 100000.0,
        "trades": [], "opportunities": [],
        "history": {a: [] for a in MONITORED_ASSETS},
        "settings": THRESHOLDS,
        "api_health": {k: "Unknown" for k in ["NASA","EIA","OpenAQ","ETH","RealYield","OBI"]}
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def fmt_usd(v): return f"${v:,.2f}"
def fmt_pct(v): return f"{v:.2f}%"
def fmt_score(v): return f"{v:.4f}"

if 'state' not in st.session_state:
    st.session_state.state = load_state()

@st.cache_resource
def get_engines():
    return {
        "engine":    S3ConvergenceEngine(),
        "allocator": S3AntiFragileAllocator(initial_capital=load_state()['equity'])
    }

engines   = get_engines()
engine    = engines["engine"]
allocator = engines["allocator"]

state = st.session_state.state

# ── COMPUTED STATS ────────────────────────────────────────────────────────────
trades      = state['trades']
n_trades    = len(trades)
pnl_list    = [t.get('pnl', 0) for t in trades]
total_pnl   = sum(pnl_list)
win_rate    = (sum(1 for p in pnl_list if p > 0) / max(1, n_trades)) * 100
current_eq  = state['equity']
eq_curve    = [state['initial_capital']] + [state['initial_capital'] + sum(pnl_list[:i+1]) for i in range(n_trades)]
max_eq      = max(eq_curve)
min_eq      = min(eq_curve)
drawdowns   = [(eq_curve[i] - max(eq_curve[:i+1])) / max(1, max(eq_curve[:i+1])) * 100 for i in range(len(eq_curve))]
max_dd      = min(drawdowns) if drawdowns else 0.0
returns_arr = np.diff(eq_curve) / np.array(eq_curve[:-1]) if len(eq_curve) > 1 else np.array([0.0])
sharpe      = (np.mean(returns_arr) / max(np.std(returns_arr), 1e-9)) * np.sqrt(252) if len(returns_arr) >= 5 else 0.0
best_trade  = max(pnl_list) if pnl_list else 0.0
worst_trade = min(pnl_list) if pnl_list else 0.0

inevitable_assets = [
    o['asset'] for o in state['opportunities']
    if o['status'] == "INEVITABLE"
    and (datetime.utcnow().timestamp() - datetime.fromisoformat(o['timestamp']).timestamp() < 3600)
]

# Daemon freshness
try:
    daemon_age = time.time() - os.path.getmtime(STATE_FILE)
    daemon_live = daemon_age < 60
except:
    daemon_live = False

NOW_STR = datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S  UTC")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h1>🔱 HYDRA-S3</h1>
        <p>ENTERPRISE QUANT OS  v4.0</p>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio("NAVIGATION", [
        "📊  MATRIX DASHBOARD",
        "🎯  OPPORTUNITY HUB",
        "💼  TRADE AUDIT LEDGER",
        "🔬  SURGICAL CAUSAL LAB",
        "⚙️   SYSTEM CONFIGURATION",
    ], label_visibility="collapsed")

    st.markdown("<hr/>", unsafe_allow_html=True)

    dot = '<span class="dot-live"></span>' if daemon_live else '<span class="dot-off"></span>'
    status_txt = "DAEMON ACTIVE (24/7)" if daemon_live else "DAEMON OFFLINE"
    status_col = "#3fb950" if daemon_live else "#ff4444"
    st.markdown(f"""
    <div style="padding:0 4px;">
        <div style="font-size:10px;letter-spacing:2px;color:#6e7681;margin-bottom:10px;">■ SYSTEM STATUS</div>
        <div style="margin-bottom:6px;">{dot}<span style="color:{status_col};font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;">{status_txt}</span></div>
    </div>
    """, unsafe_allow_html=True)

    for label, val in [
        ("ENGINE", "S3-RHGNN v4.0"),
        ("MODE",   "QUANT-AUTOMATION"),
        ("ASSETS", f"{len(MONITORED_ASSETS)} STREAMS"),
        ("EQUITY", fmt_usd(current_eq)),
    ]:
        st.markdown(f"""
        <div class="stat-pill">
            <span class="stat-pill-label">{label}</span>
            <span class="stat-pill-val">{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:#6e7681;text-align:center;font-family:\'JetBrains Mono\',monospace;letter-spacing:1px;">{NOW_STR}</div>', unsafe_allow_html=True)

    if st.button("↺  REFRESH DATA", key="refresh_btn"):
        st.session_state.state = load_state()
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — MATRIX DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if "MATRIX" in nav:

    # ── Header ──
    st.markdown(f"""
    <div class="terminal-header">
        <div class="terminal-title">🔱 HYDRA-S3  ·  QUANT MATRIX DASHBOARD</div>
        <div class="terminal-timestamp">S3-RHGNN v4.0  ·  {NOW_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── S-Alert ──
    if inevitable_assets:
        st.markdown(f"""
        <div class="s-alert">
            🚨  S-ALERT  ·  CONVERGENCE INEVITABLE DETECTED  ·  {" | ".join(set(inevitable_assets))}  ·  IMMEDIATE ATTENTION REQUIRED  🚨
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Row ──
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpis = [
        (k1, "S3 TOTAL EQUITY",       fmt_usd(current_eq),        f"{((current_eq/state['initial_capital'])-1)*100:+.2f}% ALL-TIME", ""),
        (k2, "REALIZED P&L",          fmt_usd(total_pnl),         f"{n_trades} TRADES CLOSED",      "danger-card" if total_pnl < 0 else "safe-card"),
        (k3, "WIN RATE",              fmt_pct(win_rate),          f"{sum(1 for p in pnl_list if p>0)} WINS / {sum(1 for p in pnl_list if p<=0)} LOSSES", ""),
        (k4, "OPPORTUNITIES",         str(len(state['opportunities'])), f"{len(inevitable_assets)} INEVITABLE NOW", "warn-card" if inevitable_assets else ""),
        (k5, "ACTIVE POSITIONS",      str(len(allocator.open_positions)), "LIVE EXPOSURE",              "blue-card"),
        (k6, "MAX DRAWDOWN",          f"{max_dd:.2f}%",           f"SHARPE  {sharpe:.2f}",           "danger-card" if max_dd < -10 else ""),
    ]
    for col, label, value, delta, extra_class in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card {extra_class}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-delta muted">{delta}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Convergence Matrix ──
    st.markdown('<div class="section-header">■ MULTI-ASSET CONVERGENCE MATRIX</div>', unsafe_allow_html=True)

    def regime_badge(r):
        if r == "CONTRACTION": return '<span class="badge badge-regime-c">CONTRACTION</span>'
        if r == "EXPANSION":   return '<span class="badge badge-regime-e">EXPANSION</span>'
        return '<span class="badge badge-regime-s">STABILITY</span>'

    def status_badge(s):
        if s == "INEVITABLE":     return '<span class="badge badge-inevitable">INEVITABLE</span>'
        if s == "HIGH CONVICTION":return '<span class="badge badge-high">HIGH CONVICTION</span>'
        if s == "DATA_GAP":       return '<span class="badge badge-gap">DATA GAP</span>'
        return '<span class="badge badge-noise">NOISE</span>'

    def bias_badge(b):
        if b == "LONG":  return '<span class="badge badge-long">▲ LONG</span>'
        if b == "SHORT": return '<span class="badge badge-short">▼ SHORT</span>'
        return '<span class="badge badge-neutral">— NEUTRAL</span>'

    rows = ""
    for asset in MONITORED_ASSETS:
        hist = state['history'].get(asset, [])
        sym  = SYMBOL_MAP.get(asset, asset)
        if hist:
            latest = hist[-1]
            score  = latest['score']
            regime = latest['regime']
            status = latest['status']
            age_s  = int(datetime.utcnow().timestamp() - datetime.fromisoformat(latest['time']).timestamp()) if 'time' in latest else 0
            age    = f"{age_s}s ago" if age_s < 3600 else f"{age_s//3600}h ago"
            opps   = [o for o in state['opportunities'] if o['asset'] == asset]
            dir_v  = opps[-1]['direction'] if opps else 0
            bias   = "LONG" if dir_v == 1 else "SHORT" if dir_v == -1 else "NEUTRAL"
            score_color = "#ff4444" if status == "INEVITABLE" else "#00ffcc" if status == "HIGH CONVICTION" else "#8b949e"
            rows += f"""
            <tr>
                <td><span class="asset-name">{asset}</span><br/><span class="t-xs muted">{sym}</span></td>
                <td><span class="mono" style="color:{score_color};font-size:15px;font-weight:700;">{score:.4f}</span></td>
                <td>{regime_badge(regime)}</td>
                <td>{status_badge(status)}</td>
                <td>{bias_badge(bias)}</td>
                <td><span class="mono t-xs muted">{age}</span></td>
            </tr>"""
        else:
            rows += f"""
            <tr>
                <td><span class="asset-name">{asset}</span><br/><span class="t-xs muted">{sym}</span></td>
                <td colspan="5" style="text-align:center;padding:16px;">
                    <span class="badge badge-gap">AWAITING DAEMON DATA</span>
                </td>
            </tr>"""

    st.markdown(f"""
    <div class="matrix-wrap">
    <table class="matrix-table">
      <thead><tr>
        <th>ASSET</th><th>CONV. SCORE</th><th>REGIME</th>
        <th>STATUS</th><th>BIAS</th><th>LAST UPDATE</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Execute Panel ──
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">■ TRADE EXECUTION PANEL</div>', unsafe_allow_html=True)
    ex_cols = st.columns(len(MONITORED_ASSETS))
    for i, asset in enumerate(MONITORED_ASSETS):
        with ex_cols[i]:
            hist = state['history'].get(asset, [])
            score  = hist[-1]['score'] if hist else 0.0
            opps   = [o for o in state['opportunities'] if o['asset'] == asset]
            dir_v  = opps[-1]['direction'] if opps else 0
            regime_int = 0
            if hist:
                rn = hist[-1].get('regime', 'STABILITY')
                regime_int = 2 if rn=="CONTRACTION" else 1 if rn=="EXPANSION" else 0
            enabled = score >= 0.80 and dir_v != 0
            label   = f"{'▲ BUY' if dir_v==1 else '▼ SELL' if dir_v==-1 else '— HOLD'}  {asset}"
            price_proxy = {"XAUUSD":3000,"XAGUSD":60,"HG=F":6,"EURUSD":1.08,"AUDUSD":0.65}.get(asset,100)
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:11px;color:#6e7681;margin-bottom:4px;">{asset}  ·  SCORE {score:.3f}</div>', unsafe_allow_html=True)
            btn_class = "execute-btn" if dir_v == 1 else "sell-btn" if dir_v == -1 else ""
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"exec_{asset}", disabled=not enabled):
                trade = allocator.execute_trade(asset, dir_v, score, regime_int, price_proxy)
                if trade:
                    trade['timestamp'] = datetime.utcnow().isoformat()
                    trade['pnl'] = 0.0
                    trade['asset'] = asset
                    state['trades'].append(trade)
                    state['equity'] = allocator.equity
                    save_state(state)
                    st.success(f"✅ {asset} position opened")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Live Causal Flows ──
    top_opps = sorted(state['opportunities'], key=lambda x: x['score'], reverse=True)[:3]
    if top_opps:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ LIVE CAUSAL MANIFOLDS  ·  TOP CONVERGENCES</div>', unsafe_allow_html=True)
        flow_cols = st.columns(len(top_opps))
        for i, opp in enumerate(top_opps):
            with flow_cols[i]:
                ws = opp['manifold_snapshot']
                valid = {k: v for k, v in ws.items() if v is not None}
                fig = go.Figure(go.Bar(
                    x=list(valid.keys()), y=list(valid.values()),
                    marker=dict(
                        color=list(valid.values()),
                        colorscale=[[0,"#1a0000"],[0.5,"#1f6feb"],[1,"#00ffcc"]],
                        line=dict(color="#30363d", width=1)
                    )
                ))
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    height=180, margin=dict(l=8,r=8,t=30,b=8),
                    title=dict(text=f"{opp['asset']}  ·  {opp['score']:.4f}", font=dict(family="JetBrains Mono",size=11,color="#00ffcc"), x=0),
                    xaxis=dict(tickfont=dict(family="JetBrains Mono",size=9,color="#8b949e"), gridcolor="#161b22"),
                    yaxis=dict(tickfont=dict(family="JetBrains Mono",size=9,color="#8b949e"), gridcolor="#161b22"),
                    showlegend=False,
                )
                st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — OPPORTUNITY HUB
# ═══════════════════════════════════════════════════════════════════════════════
elif "OPPORTUNITY" in nav:

    st.markdown(f"""
    <div class="terminal-header">
        <div class="terminal-title">🎯 OPPORTUNITY HUB</div>
        <div class="terminal-timestamp">ALL-ASSET SETUP LEDGER  ·  {NOW_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    opps = state['opportunities']
    if not opps:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;background:#0d1117;border:1px solid #21262d;border-radius:4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:16px;color:#6e7681;letter-spacing:3px;">
                NO OPPORTUNITIES DETECTED
            </div>
            <div style="font-size:12px;color:#484f58;margin-top:8px;">
                Start the live daemon to begin monitoring
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Filters ──
        f1, f2, f3 = st.columns([2,2,2])
        with f1:
            asset_filter = st.multiselect("FILTER BY ASSET", MONITORED_ASSETS, default=MONITORED_ASSETS, label_visibility="collapsed")
        with f2:
            status_opts = list(set(o['status'] for o in opps))
            status_filter = st.multiselect("FILTER BY STATUS", status_opts, default=status_opts, label_visibility="collapsed")
        with f3:
            min_score = st.slider("MIN SCORE", 0.0, 1.0, 0.0, 0.01)

        filtered = [o for o in opps
                    if o['asset'] in asset_filter
                    and o['status'] in status_filter
                    and o['score'] >= min_score]

        # ── Summary KPIs ──
        st.markdown("<br/>", unsafe_allow_html=True)
        sc1, sc2, sc3, sc4 = st.columns(4)
        inevitable_ct = sum(1 for o in filtered if o['status']=="INEVITABLE")
        high_ct       = sum(1 for o in filtered if o['status']=="HIGH CONVICTION")
        avg_score     = np.mean([o['score'] for o in filtered]) if filtered else 0
        top_asset     = max(set(o['asset'] for o in filtered), key=lambda a: sum(o['score'] for o in filtered if o['asset']==a)) if filtered else "—"
        for col, lbl, val, cls in [
            (sc1,"TOTAL SETUPS",    str(len(filtered)),      ""),
            (sc2,"INEVITABLE",      str(inevitable_ct),      "danger-card" if inevitable_ct else ""),
            (sc3,"HIGH CONVICTION", str(high_ct),            "safe-card" if high_ct else ""),
            (sc4,"AVG SCORE",       f"{avg_score:.4f}",      ""),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi-card {cls}">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-value">{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ ALL-ASSET SETUP LEDGER</div>', unsafe_allow_html=True)

        df = pd.DataFrame(filtered)
        df_disp = df[['id','asset','timestamp','score','regime','status','direction']].copy()
        df_disp['timestamp'] = pd.to_datetime(df_disp['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df_disp['score']     = df_disp['score'].round(4)
        df_disp['direction'] = df_disp['direction'].map({1:"▲ LONG", -1:"▼ SHORT", 0:"— NEUTRAL"})
        df_disp.columns      = ['ID','ASSET','TIMESTAMP','SCORE','REGIME','STATUS','DIRECTION']
        st.dataframe(df_disp, width="stretch", height=280)

        # ── Deep-Dive ──
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ SURGICAL DEEP-DIVE ANALYSIS</div>', unsafe_allow_html=True)
        opp_ids = [o['id'] for o in filtered]
        sel_id  = st.selectbox("SELECT OPPORTUNITY", opp_ids, label_visibility="collapsed")
        if sel_id:
            opp = next(o for o in filtered if o['id'] == sel_id)
            da, db, dc, dd = st.columns(4)
            for col, lbl, val, cls in [
                (da,"CONVERGENCE SCORE", fmt_score(opp['score']),  "danger-card" if opp['score']>=0.95 else "safe-card"),
                (db,"CAUSAL REGIME",     opp['regime'],            ""),
                (dc,"S3 STATUS",         opp['status'],            "danger-card" if opp['status']=="INEVITABLE" else ""),
                (dd,"DIRECTION",         "▲ LONG" if opp['direction']==1 else "▼ SHORT" if opp['direction']==-1 else "— NEUTRAL", "safe-card" if opp['direction']==1 else "danger-card" if opp['direction']==-1 else ""),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="kpi-card {cls}">
                        <div class="kpi-label">{lbl}</div>
                        <div class="kpi-value" style="font-size:18px;">{val}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)
            ws     = opp['manifold_snapshot']
            valid  = {k: v for k, v in ws.items() if v is not None}
            ch1, ch2 = st.columns(2)
            with ch1:
                fig = go.Figure(go.Bar(
                    x=list(valid.keys()), y=list(valid.values()),
                    marker=dict(color=list(valid.values()), colorscale="teal",
                                line=dict(color="#30363d",width=1)),
                    text=[f"{v:.4f}" for v in valid.values()], textposition="outside",
                    textfont=dict(family="JetBrains Mono", size=10, color="#8b949e"),
                ))
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    title=dict(text="CAUSAL SIGNAL MANIFOLD", font=dict(family="JetBrains Mono",size=11,color="#8b949e"),x=0),
                    height=300, margin=dict(l=8,r=8,t=40,b=8),
                    xaxis=dict(tickfont=dict(family="JetBrains Mono",size=10,color="#8b949e"),gridcolor="#161b22"),
                    yaxis=dict(tickfont=dict(family="JetBrains Mono",size=10,color="#8b949e"),gridcolor="#161b22",range=[0,1.1]),
                    showlegend=False,
                )
                st.plotly_chart(fig, width="stretch")
            with ch2:
                cats   = list(valid.keys())
                vals_r = [valid[k] for k in cats]
                fig_r  = go.Figure(go.Scatterpolar(
                    r=vals_r + [vals_r[0]], theta=cats + [cats[0]],
                    fill='toself',
                    fillcolor='rgba(0,255,204,0.1)',
                    line=dict(color='#00ffcc', width=2),
                    marker=dict(size=6, color='#00ffcc'),
                ))
                fig_r.update_layout(
                    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    title=dict(text="SIGNAL RADAR", font=dict(family="JetBrains Mono",size=11,color="#8b949e"),x=0),
                    height=300, margin=dict(l=8,r=8,t=40,b=8),
                    polar=dict(
                        bgcolor="#0d1117",
                        radialaxis=dict(visible=True, range=[0,1], tickfont=dict(size=8,color="#6e7681"), gridcolor="#21262d"),
                        angularaxis=dict(tickfont=dict(family="JetBrains Mono",size=10,color="#8b949e"), gridcolor="#21262d"),
                    ),
                    showlegend=False,
                )
                st.plotly_chart(fig_r, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — TRADE AUDIT LEDGER
# ═══════════════════════════════════════════════════════════════════════════════
elif "TRADE" in nav:

    st.markdown(f"""
    <div class="terminal-header">
        <div class="terminal-title">💼 TRADE AUDIT LEDGER</div>
        <div class="terminal-timestamp">PORTFOLIO PERFORMANCE ENGINE  ·  {NOW_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary KPIs ──
    t1,t2,t3,t4,t5,t6 = st.columns(6)
    for col,lbl,val,cls in [
        (t1, "TOTAL EQUITY",   fmt_usd(current_eq),          ""),
        (t2, "TOTAL P&L",      fmt_usd(total_pnl),           "safe-card" if total_pnl>=0 else "danger-card"),
        (t3, "WIN RATE",       fmt_pct(win_rate),            "safe-card" if win_rate>=50 else "danger-card"),
        (t4, "SHARPE RATIO",   f"{sharpe:.3f}",              "safe-card" if sharpe>=1 else "warn-card" if sharpe>=0 else "danger-card"),
        (t5, "MAX DRAWDOWN",   f"{max_dd:.2f}%",             "danger-card" if max_dd<-10 else "warn-card" if max_dd<-5 else ""),
        (t6, "TOTAL TRADES",   str(n_trades),                "blue-card"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls}">
                <div class="kpi-label">{lbl}</div>
                <div class="kpi-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if not trades:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;background:#0d1117;border:1px solid #21262d;border-radius:4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:16px;color:#6e7681;letter-spacing:3px;">NO TRADES EXECUTED</div>
            <div style="font-size:12px;color:#484f58;margin-top:8px;">Use the Matrix Dashboard execution panel to open positions</div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Equity + Drawdown Chart ──
        st.markdown('<div class="section-header">■ PORTFOLIO EQUITY CURVE  &  DRAWDOWN ANALYSIS</div>', unsafe_allow_html=True)
        fig = make_subplots(rows=2, cols=1, row_heights=[0.65, 0.35], vertical_spacing=0.06,
                            shared_xaxes=True)
        x_idx = list(range(len(eq_curve)))
        fig.add_trace(go.Scatter(
            x=x_idx, y=eq_curve, mode='lines',
            line=dict(color='#00ffcc', width=2),
            fill='tozeroy', fillcolor='rgba(0,255,204,0.08)',
            name='EQUITY',
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=x_idx, y=[state['initial_capital']]*len(x_idx),
            line=dict(color='#30363d', dash='dot', width=1), name='INITIAL CAPITAL', showlegend=False,
        ), row=1, col=1)
        dd_colors = ['#ff4444' if d < -5 else '#f0a430' if d < 0 else '#3fb950' for d in drawdowns]
        fig.add_trace(go.Bar(
            x=x_idx, y=drawdowns, marker_color=dd_colors,
            name='DRAWDOWN %', showlegend=False,
        ), row=2, col=1)
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            height=380, margin=dict(l=8,r=8,t=8,b=8),
            legend=dict(font=dict(family="JetBrains Mono",size=10,color="#8b949e"),
                        bgcolor="#0d1117", bordercolor="#30363d", borderwidth=1, x=0.01, y=0.99),
            xaxis2=dict(gridcolor="#161b22", tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681")),
            yaxis=dict(gridcolor="#161b22", tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681"),
                       tickprefix="$", tickformat=",.0f"),
            yaxis2=dict(gridcolor="#161b22", tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681"),
                        ticksuffix="%"),
        )
        st.plotly_chart(fig, width="stretch")

        # ── Trade Stats ──
        st.markdown("<br/>", unsafe_allow_html=True)
        ts1, ts2 = st.columns(2)
        with ts1:
            st.markdown('<div class="section-header">■ PERFORMANCE METRICS</div>', unsafe_allow_html=True)
            for lbl, val in [
                ("BEST TRADE",    fmt_usd(best_trade)),
                ("WORST TRADE",   fmt_usd(worst_trade)),
                ("AVG WIN",       fmt_usd(np.mean([p for p in pnl_list if p>0]) if any(p>0 for p in pnl_list) else 0)),
                ("AVG LOSS",      fmt_usd(np.mean([p for p in pnl_list if p<0]) if any(p<0 for p in pnl_list) else 0)),
                ("PROFIT FACTOR", f"{abs(sum(p for p in pnl_list if p>0)/max(abs(sum(p for p in pnl_list if p<0)),0.01)):.2f}x"),
                ("TOTAL RETURN",  f"{((current_eq/state['initial_capital'])-1)*100:+.2f}%"),
            ]:
                st.markdown(f"""
                <div class="stat-pill">
                    <span class="stat-pill-label">{lbl}</span>
                    <span class="stat-pill-val">{val}</span>
                </div>""", unsafe_allow_html=True)

        with ts2:
            st.markdown('<div class="section-header">■ P&L DISTRIBUTION</div>', unsafe_allow_html=True)
            if pnl_list:
                fig_hist = go.Figure(go.Histogram(
                    x=pnl_list, nbinsx=20,
                    marker=dict(color=['#3fb950' if p>=0 else '#ff4444' for p in sorted(pnl_list)],
                                line=dict(color="#0d1117",width=1)),
                ))
                fig_hist.update_layout(
                    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    height=260, margin=dict(l=8,r=8,t=8,b=8),
                    xaxis=dict(gridcolor="#161b22",tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681"),tickprefix="$"),
                    yaxis=dict(gridcolor="#161b22",tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681")),
                    showlegend=False,
                )
                st.plotly_chart(fig_hist, width="stretch")

        # ── Trade Table ──
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ FULL TRADE AUDIT LOG</div>', unsafe_allow_html=True)
        df_t = pd.DataFrame(trades)
        cols_show = [c for c in ['asset','instrument','direction','entry_price','size','sl_price','tp_price','pnl','timestamp'] if c in df_t.columns]
        df_show = df_t[cols_show].copy()
        if 'direction' in df_show.columns:
            df_show['direction'] = df_show['direction'].map({1:"▲ LONG",-1:"▼ SHORT",0:"— NEUTRAL"})
        if 'pnl' in df_show.columns:
            df_show['pnl'] = df_show['pnl'].apply(lambda x: f"+${x:.2f}" if x>=0 else f"-${abs(x):.2f}")
        for c in ['entry_price','sl_price','tp_price']:
            if c in df_show.columns:
                df_show[c] = df_show[c].apply(lambda x: f"${x:,.4f}")
        if 'size' in df_show.columns:
            df_show['size'] = df_show['size'].apply(lambda x: f"{x:.4f}")
        df_show.columns = [c.upper().replace('_',' ') for c in df_show.columns]
        st.dataframe(df_show, width="stretch", height=300)


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — SURGICAL CAUSAL LAB
# ═══════════════════════════════════════════════════════════════════════════════
elif "CAUSAL" in nav:

    st.markdown(f"""
    <div class="terminal-header">
        <div class="terminal-title">🔬 SURGICAL CAUSAL LAB</div>
        <div class="terminal-timestamp">SIGNAL ANALYSIS ENGINE  ·  {NOW_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── API Health Matrix ──
    st.markdown('<div class="section-header">■ LIVE API HEALTH MATRIX</div>', unsafe_allow_html=True)
    health = state['api_health']
    api_descs = {"NASA":"FIRMS Fire Data","EIA":"Energy Prices","OpenAQ":"Industrial AQ",
                 "ETH":"Chain Liquidity","RealYield":"TIPS 10Y","OBI":"Order Book Imbalance"}
    hcols = st.columns(len(health))
    for i, (api, status) in enumerate(health.items()):
        with hcols[i]:
            if status == "ONLINE":
                cls, dot_c = "api-status-on",  "#3fb950"
                dot = '<span class="dot-live"></span>'
            elif status in ("GAP","Unknown"):
                cls, dot_c = "api-status-unk",  "#f0a430"
                dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#f0a430;margin-right:6px;"></span>'
            else:
                cls, dot_c = "api-status-off",  "#ff4444"
                dot = '<span class="dot-off"></span>'
            st.markdown(f"""
            <div class="api-card">
                <div class="api-name">{api}</div>
                <div style="margin-bottom:4px;">{dot}<span class="{cls}">{status}</span></div>
                <div class="t-xs muted">{api_descs.get(api,'')}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Asset Score History ──
    st.markdown('<div class="section-header">■ CONVERGENCE SCORE HISTORY  ·  SELECT ASSET STREAM</div>', unsafe_allow_html=True)
    sel_asset = st.selectbox("ASSET STREAM", MONITORED_ASSETS, label_visibility="collapsed")

    hist = state['history'].get(sel_asset, [])
    if hist:
        df_h = pd.DataFrame(hist)
        df_h['time'] = pd.to_datetime(df_h['time'])

        ch_a, ch_b = st.columns([3,1])
        with ch_a:
            fig = go.Figure()
            score_colors = ['#ff4444' if s >= 0.95 else '#00ffcc' if s >= 0.80 else '#8b949e' for s in df_h['score']]
            fig.add_trace(go.Scatter(
                x=df_h['time'], y=df_h['score'],
                mode='lines+markers',
                line=dict(color='#00ffcc', width=1.5),
                marker=dict(color=score_colors, size=5, line=dict(color="#0d1117",width=1)),
                fill='tozeroy', fillcolor='rgba(0,255,204,0.05)',
                name='CONV. SCORE',
            ))
            fig.add_hline(y=0.95, line_dash="dot", line_color="#ff4444", line_width=1,
                          annotation_text="INEVITABLE", annotation_font=dict(family="JetBrains Mono",size=9,color="#ff4444"))
            fig.add_hline(y=0.80, line_dash="dot", line_color="#00ffcc", line_width=1,
                          annotation_text="HIGH CONVICTION", annotation_font=dict(family="JetBrains Mono",size=9,color="#00ffcc"))
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                height=300, margin=dict(l=8,r=8,t=8,b=8),
                xaxis=dict(gridcolor="#161b22",tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681")),
                yaxis=dict(gridcolor="#161b22",tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681"),range=[0,1.05]),
                showlegend=False,
            )
            st.plotly_chart(fig, width="stretch")

        with ch_b:
            # Score distribution
            status_counts = df_h['status'].value_counts() if 'status' in df_h.columns else pd.Series()
            if not status_counts.empty:
                colors_map = {"INEVITABLE":"#ff4444","HIGH CONVICTION":"#00ffcc","NOISE":"#6e7681","DATA_GAP":"#f0a430"}
                fig_pie = go.Figure(go.Pie(
                    labels=status_counts.index.tolist(),
                    values=status_counts.values.tolist(),
                    marker=dict(colors=[colors_map.get(s,"#30363d") for s in status_counts.index],
                                line=dict(color="#0d1117",width=2)),
                    hole=0.6,
                    textfont=dict(family="JetBrains Mono",size=10),
                    textinfo="percent+label",
                ))
                fig_pie.update_layout(
                    template="plotly_dark", paper_bgcolor="#0d1117",
                    height=300, margin=dict(l=8,r=8,t=8,b=8),
                    showlegend=False,
                    annotations=[dict(text="STATUS<br>MIX",x=0.5,y=0.5,font_size=10,
                                      font=dict(family="JetBrains Mono",color="#6e7681"),showarrow=False)],
                )
                st.plotly_chart(fig_pie, width="stretch")

        # ── Stats ──
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ STREAM STATISTICS</div>', unsafe_allow_html=True)
        ss1, ss2, ss3, ss4 = st.columns(4)
        for col, lbl, val in [
            (ss1, "DATA POINTS",   str(len(df_h))),
            (ss2, "PEAK SCORE",    f"{df_h['score'].max():.4f}"),
            (ss3, "MEAN SCORE",    f"{df_h['score'].mean():.4f}"),
            (ss4, "INEVITABLE CT", str(len(df_h[df_h['score']>=0.95])) if 'score' in df_h.columns else "0"),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-value" style="font-size:20px;">{val}</div>
                </div>""", unsafe_allow_html=True)

        # ── Raw history table ──
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">■ RAW HISTORY STREAM</div>', unsafe_allow_html=True)
        df_disp = df_h[['time','score','status','regime']].copy() if 'regime' in df_h.columns else df_h[['time','score','status']].copy()
        df_disp['score'] = df_disp['score'].round(4)
        df_disp.columns  = [c.upper() for c in df_disp.columns]
        st.dataframe(df_disp.sort_values('TIME', ascending=False).head(200), width="stretch", height=260)
    else:
        st.markdown(f"""
        <div style="text-align:center;padding:80px 0;background:#0d1117;border:1px solid #21262d;border-radius:4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:16px;color:#6e7681;letter-spacing:3px;">
                NO DATA STREAM FOR {sel_asset}
            </div>
            <div style="font-size:12px;color:#484f58;margin-top:8px;">Start the live daemon to begin collecting signal data</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 5 — SYSTEM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
elif "CONFIGURATION" in nav:

    st.markdown(f"""
    <div class="terminal-header">
        <div class="terminal-title">⚙️  SYSTEM CONFIGURATION</div>
        <div class="terminal-timestamp">PARAMETER CONTROL CENTER  ·  {NOW_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    cfg = state['settings']

    # ── Current Parameter Visualization ──
    st.markdown('<div class="section-header">■ CURRENT THRESHOLD PROFILE</div>', unsafe_allow_html=True)
    gauge_cols = st.columns(3)
    gauge_data = [
        ("INEVITABLE SCORE",   cfg['INEVITABLE_SCORE'],   0.0, 1.0, "#ff4444"),
        ("CONTRACTION YIELD",  cfg['CONTRACTION_YIELD'],  0.0, 2.0, "#f0a430"),
        ("HARD STOP %",        cfg['HARD_STOP_PCT']*100,  0.0, 5.0, "#388bfd"),
    ]
    for i, (gc, (lbl, val, lo, hi, col)) in enumerate(zip(gauge_cols, gauge_data)):
        with gc:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=val,
                title=dict(text=lbl, font=dict(family="JetBrains Mono",size=10,color="#6e7681")),
                number=dict(font=dict(family="JetBrains Mono",size=22,color=col)),
                gauge=dict(
                    axis=dict(range=[lo, hi], tickfont=dict(family="JetBrains Mono",size=9,color="#6e7681"),
                              tickcolor="#30363d", gridcolor="#21262d"),
                    bar=dict(color=col, thickness=0.3),
                    bgcolor="#0d1117", bordercolor="#30363d", borderwidth=1,
                    steps=[dict(range=[lo, hi], color="#161b22")],
                    threshold=dict(line=dict(color=col,width=2), thickness=0.75, value=val),
                )
            ))
            fig_g.update_layout(
                paper_bgcolor="#0d1117", height=200, margin=dict(l=16,r=16,t=40,b=8),
                font=dict(color="#e6edf3"),
            )
            st.plotly_chart(fig_g, width="stretch")

    # ── Parameter Form ──
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">■ PARAMETER CONTROL PANEL</div>', unsafe_allow_html=True)

    with st.form("config_form"):
        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown('<div class="section-header">CONTRACTION ENGINE</div>', unsafe_allow_html=True)
            t_con_yield = st.number_input("CONTRACTION YIELD THRESHOLD", value=float(cfg['CONTRACTION_YIELD']),
                                          min_value=0.0, max_value=5.0, step=0.05, format="%.2f")
            t_con_obi   = st.number_input("CONTRACTION OBI THRESHOLD",   value=float(cfg['CONTRACTION_OBI']),
                                          min_value=-1.0, max_value=0.0, step=0.05, format="%.2f")
            t_inev      = st.number_input("INEVITABLE SCORE THRESHOLD",  value=float(cfg['INEVITABLE_SCORE']),
                                          min_value=0.50, max_value=1.00, step=0.01, format="%.2f")
        with fc2:
            st.markdown('<div class="section-header">EXPANSION ENGINE</div>', unsafe_allow_html=True)
            t_exp_yield = st.number_input("EXPANSION YIELD THRESHOLD",   value=float(cfg['EXPANSION_YIELD']),
                                          min_value=-2.0, max_value=0.0, step=0.05, format="%.2f")
            t_exp_obi   = st.number_input("EXPANSION OBI THRESHOLD",     value=float(cfg['EXPANSION_OBI']),
                                          min_value=0.0, max_value=1.0, step=0.05, format="%.2f")
            t_stop      = st.number_input("HARD STOP % (RISK CONTROL)",  value=float(cfg['HARD_STOP_PCT']),
                                          min_value=0.001, max_value=0.10, step=0.001, format="%.3f")

        submitted = st.form_submit_button("💾  DEPLOY SYSTEM PARAMETERS", use_container_width=True)
        if submitted:
            state['settings'] = {
                'CONTRACTION_YIELD': t_con_yield, 'CONTRACTION_OBI': t_con_obi,
                'EXPANSION_YIELD':   t_exp_yield, 'EXPANSION_OBI':   t_exp_obi,
                'INEVITABLE_SCORE':  t_inev,      'HARD_STOP_PCT':   t_stop,
            }
            save_state(state)
            st.success("✅  SYSTEM PARAMETERS DEPLOYED  ·  Engine reconfigured successfully.")

    # ── System Info ──
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">■ SYSTEM INFORMATION</div>', unsafe_allow_html=True)
    si1, si2 = st.columns(2)
    with si1:
        for lbl, val in [
            ("ENGINE",          "S3-RHGNN v4.0"),
            ("ARCHITECTURE",    "RecursiveHyperGraph + Manifold"),
            ("INPUT DIMENSION", "100"),
            ("HIDDEN DIMENSION","256"),
            ("GRAPH LAYERS",    "4"),
            ("ASSETS MONITORED",str(len(MONITORED_ASSETS))),
        ]:
            st.markdown(f"""
            <div class="stat-pill">
                <span class="stat-pill-label">{lbl}</span>
                <span class="stat-pill-val accent">{val}</span>
            </div>""", unsafe_allow_html=True)
    with si2:
        for lbl, val in [
            ("SIGNAL SOURCES",  "6 (NASA·EIA·OpenAQ·ETH·TIPS·OBI)"),
            ("POLLING INTERVAL","10 seconds"),
            ("MAX LEVERAGE",    "100x (INEVITABLE)  ·  50x (HIGH)"),
            ("POSITION RISK",   "2% per trade"),
            ("WEIGHTS FILE",    "s3_weights.pth"),
            ("STATE FILE",      STATE_FILE),
        ]:
            st.markdown(f"""
            <div class="stat-pill">
                <span class="stat-pill-label">{lbl}</span>
                <span class="stat-pill-val">{val}</span>
            </div>""", unsafe_allow_html=True)


# ── AUTO-SAVE ─────────────────────────────────────────────────────────────────
save_state(st.session_state.state)
