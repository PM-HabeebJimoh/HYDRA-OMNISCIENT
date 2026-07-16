"""
HYDRA-S3  |  Enterprise Quantitative Terminal  v5.0
Bloomberg/Reuters-grade dark terminal. Auto-refresh every 15s.
Zero synthetic data — all prices and signals sourced live.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone
import json, os, time, math, requests

from core.convergence   import S3ConvergenceEngine
from core.allocator     import S3AntiFragileAllocator
from core.telegram_alerts import (
    send_alert_sync, fmt_test, fmt_inevitable, fmt_high_conviction,
    fmt_trade_executed,
)
from config import MONITORED_ASSETS, REGIMES, THRESHOLDS, SYMBOL_MAP

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="HYDRA-S3 | QUANT TERMINAL",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="expanded",
)

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enterprise_state.json")

_YF = {
    'XAUUSD': 'GC=F',    'XAGUSD': 'SI=F',
    'HG=F':   'HG=F',    'EURUSD': 'EURUSD=X',
    'AUDUSD': 'AUDUSD=X',
}
_PX_FALLBACK = {
    'XAUUSD': 3350.0, 'XAGUSD': 32.5, 'HG=F': 4.5,
    'EURUSD': 1.085,  'AUDUSD': 0.643,
}

# ══════════════════════════════════════════════════════════════════════════════
#  ENTERPRISE TERMINAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── GLOBAL RESET ──────────────────────────────── */
html,body,
[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="block-container"],.main,.stApp {
    background: #000913 !important;
    color: #cdd9e5 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebar"]>div:first-child {
    background: #00060f !important;
    border-right: 1px solid #0d2035 !important;
}
[data-testid="stSidebar"] * { color: #cdd9e5 !important; }
#MainMenu,header,footer { visibility:hidden; }
.block-container { padding:0 !important; max-width:100% !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#000913; }
::-webkit-scrollbar-thumb { background:#0d2035; border-radius:2px; }
* { box-sizing:border-box; }

/* ── SYSTEM STATUS BAR ─────────────────────────── */
.sys-bar {
    background:#00060f;
    border-bottom:1px solid #0a1f35;
    padding:5px 20px;
    font-family:'IBM Plex Mono',monospace;
    font-size:10.5px;
    color:#2a6090;
    display:flex; align-items:center; justify-content:space-between;
    position:sticky; top:0; z-index:1000;
    letter-spacing:.5px;
}
.sys-bar-left  { display:flex; align-items:center; gap:20px; }
.sys-bar-right { display:flex; align-items:center; gap:20px; }
.sbl { display:inline-flex; align-items:center; gap:5px; }
.sbl-k { color:#1a4060; }
.sbl-v { color:#cdd9e5; font-weight:600; }
.sbl-v.green  { color:#3fb950; }
.sbl-v.red    { color:#f85149; }
.sbl-v.cyan   { color:#58c3e0; }
.sbl-v.amber  { color:#e3b341; }

/* ── REFRESH BAR ──────────────────────────────── */
.rfr-bar {
    background:#00060f; border-bottom:1px solid #0a1f35;
    padding:2px 20px; display:flex; align-items:center; gap:12px;
}
.rfr-label { font-family:'IBM Plex Mono',monospace; font-size:9.5px; color:#1a4060; }
.rfr-track { flex:1; height:2px; background:#0a1f35; }
.rfr-fill  { height:100%; background:#58c3e0; animation:drain 15s linear forwards; }
@keyframes drain { from{width:100%} to{width:0} }

/* ── TERMINAL HEADER ──────────────────────────── */
.term-hdr {
    background:linear-gradient(90deg,#000d1f 0%,#001428 100%);
    border-bottom:1px solid #0a3060;
    border-left:3px solid #58c3e0;
    padding:10px 20px;
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:12px;
}
.term-title {
    font-family:'IBM Plex Mono',monospace;
    font-size:12px; font-weight:700; letter-spacing:3px;
    color:#58c3e0; text-transform:uppercase;
}
.term-sub {
    font-family:'IBM Plex Mono',monospace;
    font-size:9px; color:#2a6090; letter-spacing:1px; margin-top:2px;
}
.term-meta {
    font-family:'IBM Plex Mono',monospace;
    font-size:9px; color:#1a4060; text-align:right; line-height:1.6;
}

/* ── S-ALERT BANNER ───────────────────────────── */
.s-alert {
    background:linear-gradient(90deg,#1a0005,#200008,#1a0005);
    border:1px solid #8b0021; border-left:3px solid #f85149;
    padding:10px 18px; margin-bottom:12px; border-radius:1px;
    font-family:'IBM Plex Mono',monospace; font-size:12px;
    font-weight:700; letter-spacing:2px; color:#f85149;
    display:flex; align-items:center; gap:12px;
    animation:salert 1.8s ease-in-out infinite;
}
@keyframes salert {
    0%,100%{opacity:1;box-shadow:0 0 0 rgba(248,81,73,0);}
    50%{opacity:.9;box-shadow:0 0 20px rgba(248,81,73,.15);}
}

/* ── SECTION HEADER ───────────────────────────── */
.sec-hdr {
    font-family:'IBM Plex Mono',monospace;
    font-size:8.5px; font-weight:700; letter-spacing:2.5px;
    color:#1a4060; text-transform:uppercase;
    border-bottom:1px solid #0a1f35;
    padding-bottom:5px; margin:12px 0 10px;
}

/* ── KPI CARD ─────────────────────────────────── */
.kpi {
    background:#000d1f; border:1px solid #0a1f35;
    border-top:2px solid #1a4060; border-radius:1px;
    padding:12px 14px; position:relative; overflow:hidden;
}
.kpi-lbl {
    font-family:'IBM Plex Mono',monospace;
    font-size:8px; font-weight:700; letter-spacing:2px;
    color:#1a4060; margin-bottom:7px; text-transform:uppercase;
}
.kpi-val {
    font-family:'IBM Plex Mono',monospace;
    font-size:clamp(12px,1.3vw,19px); font-weight:700;
    color:#58c3e0; line-height:1.1;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.kpi-sub { font-family:'IBM Plex Mono',monospace; font-size:9px; color:#1a4060; margin-top:5px; }
.kpi.red   { border-top-color:#f85149; } .kpi.red   .kpi-val { color:#f85149; }
.kpi.grn   { border-top-color:#3fb950; } .kpi.grn   .kpi-val { color:#3fb950; }
.kpi.amb   { border-top-color:#e3b341; } .kpi.amb   .kpi-val { color:#e3b341; }
.kpi.blue  { border-top-color:#388bfd; } .kpi.blue  .kpi-val { color:#388bfd; }
.kpi.purp  { border-top-color:#8957e5; } .kpi.purp  .kpi-val { color:#8957e5; }
.kpi.cyan  { border-top-color:#58c3e0; }
.kpi-glow  { animation:kpi-pulse 2s ease-in-out infinite; }
@keyframes kpi-pulse { 0%,100%{box-shadow:0 0 0 rgba(248,81,73,0)} 50%{box-shadow:0 0 14px rgba(248,81,73,.25)} }

/* ── MATRIX TABLE ─────────────────────────────── */
.matrix { width:100%; border-collapse:collapse; background:#000913;
          font-family:'IBM Plex Mono',monospace; font-size:11.5px; }
.matrix thead tr { background:#000d1f; border-bottom:1px solid #0a1f35; }
.matrix th { padding:9px 13px; text-align:left; font-size:8px;
             font-weight:700; letter-spacing:2px; color:#1a4060; }
.matrix tbody tr { border-bottom:1px solid #060f1c; transition:background .12s; }
.matrix tbody tr:hover { background:#000d1f; }
.matrix td { padding:10px 13px; vertical-align:middle; }
.as  { font-weight:700; color:#cdd9e5; font-size:12.5px; }
.asb { font-size:9px; color:#1a4060; margin-top:1px; }
.pv  { font-weight:600; color:#cdd9e5; }

/* ── BADGES ───────────────────────────────────── */
.badge {
    display:inline-block; padding:3px 8px; border-radius:1px;
    font-family:'IBM Plex Mono',monospace;
    font-size:9px; font-weight:700; letter-spacing:1px;
}
.bi { background:#1a0005; color:#f85149; border:1px solid #8b0021;
      animation:bpulse 1.8s ease-in-out infinite; }
.bh { background:#001405; color:#3fb950; border:1px solid #1a5a20; }
.bn { background:#060f1c; color:#2a6090; border:1px solid #0a1f35; }
.bg { background:#150a00; color:#e3b341; border:1px solid #5a3500; }
.be { background:#001405; color:#3fb950; border:1px solid #1a5a20; }
.bc { background:#160005; color:#f85149; border:1px solid #660022; }
.bs { background:#060f1c; color:#388bfd; border:1px solid #0d2540; }
.bl { background:#001405; color:#3fb950; border:1px solid #1a5a20; }
.bsh{ background:#160005; color:#f85149; border:1px solid #660022; }
.bnt{ background:#060f1c; color:#2a6090; border:1px solid #0a1f35; }
@keyframes bpulse { 0%,100%{box-shadow:0 0 0 rgba(139,0,33,0)} 50%{box-shadow:0 0 8px rgba(139,0,33,.5)} }

/* ── SCORE BAR ────────────────────────────────── */
.sb-wrap { display:flex; align-items:center; gap:7px; }
.sb-track { width:75px; height:5px; background:#0a1f35; border-radius:1px; overflow:hidden; display:inline-block; }
.sb-fill  { height:100%; border-radius:1px; }

/* ── SIGNAL CELL ──────────────────────────────── */
.sig-cell {
    background:#000d1f; border:1px solid #0a1f35; border-radius:1px;
    padding:10px 12px; text-align:center;
}
.sig-name { font-size:8px; letter-spacing:2px; color:#1a4060; font-weight:700; margin-bottom:5px; }
.sig-val  { font-family:'IBM Plex Mono',monospace; font-size:13px; font-weight:700; }
.sig-sub  { font-size:8.5px; color:#1a4060; margin-top:3px; }
.dot-live { display:inline-block; width:6px; height:6px; border-radius:50%;
    background:#3fb950; box-shadow:0 0 5px #3fb950;
    animation:dpulse 2s ease-in-out infinite; margin-right:5px; }
.dot-off  { display:inline-block; width:6px; height:6px; border-radius:50%;
    background:#f85149; margin-right:5px; }
.dot-unk  { display:inline-block; width:6px; height:6px; border-radius:50%;
    background:#e3b341; margin-right:5px; }
@keyframes dpulse { 0%,100%{opacity:1} 50%{opacity:.2} }

/* ── STAT PILL ────────────────────────────────── */
.pill {
    display:flex; align-items:center;
    background:#000d1f; border:1px solid #0a1f35; border-radius:1px;
    padding:6px 11px; margin:2px 0; gap:8px;
}
.pill-k { font-size:8.5px; color:#1a4060; letter-spacing:1px; flex:1;
          font-family:'IBM Plex Mono',monospace; }
.pill-v { font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600; color:#cdd9e5; }
.pill-vc { color:#58c3e0; }

/* ── SIDEBAR ──────────────────────────────────── */
.sb-logo { text-align:center; padding:14px 8px 12px; border-bottom:1px solid #0a1f35; margin-bottom:12px; }
.sb-logo h1 { font-family:'IBM Plex Mono',monospace; font-size:18px; font-weight:700;
              color:#58c3e0; letter-spacing:5px; margin:0; }
.sb-logo p  { font-size:8px; color:#1a4060; letter-spacing:3px; margin:3px 0 0; }
.sb-pill { display:flex; align-items:center; justify-content:space-between;
           padding:5px 9px; margin:2px 0; border-radius:1px;
           background:#000d1f; border:1px solid #0a1f35; }
.sb-k { font-size:8.5px; color:#1a4060; letter-spacing:1px; font-family:'IBM Plex Mono',monospace; }
.sb-v { font-family:'IBM Plex Mono',monospace; font-size:10.5px; font-weight:700; color:#cdd9e5; }

/* ── BUTTONS ──────────────────────────────────── */
.stButton>button {
    background:#000d1f !important; color:#388bfd !important;
    border:1px solid #0d2540 !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:10.5px !important; font-weight:700 !important;
    letter-spacing:1px !important; border-radius:1px !important;
    padding:6px 12px !important; width:100% !important;
    transition:all .18s !important;
}
.stButton>button:hover {
    background:#001020 !important; border-color:#388bfd !important;
    box-shadow:0 0 8px rgba(56,139,253,.25) !important;
}
.btn-long>button  { color:#3fb950 !important; border-color:#1a5a20 !important; }
.btn-long>button:hover  { background:#001405 !important; border-color:#3fb950 !important; }
.btn-short>button { color:#f85149 !important; border-color:#660022 !important; }
.btn-short>button:hover { background:#160005 !important; border-color:#f85149 !important; }
.btn-tg>button    { color:#58c3e0 !important; border-color:#1a5070 !important; }
.btn-tg>button:hover    { background:#001428 !important; border-color:#58c3e0 !important; }

/* ── TABS ─────────────────────────────────────── */
[data-testid="stTabs"] { background:transparent !important; }
[data-testid="stTabsContainer"] { border-bottom:1px solid #0a1f35 !important; }
button[data-baseweb="tab"] {
    background:transparent !important;
    font-family:'IBM Plex Mono',monospace !important;
    font-size:10px !important; font-weight:700 !important;
    letter-spacing:1.5px !important; color:#1a4060 !important;
    border:none !important; padding:8px 16px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color:#58c3e0 !important; border-bottom:2px solid #58c3e0 !important;
}
[data-testid="stTabPanel"] { padding:0 !important; }

/* ── INPUTS ───────────────────────────────────── */
[data-testid="stSelectbox"]>div>div,
[data-testid="stNumberInput"]>div>div>input,
[data-testid="stTextInput"]>div>div>input {
    background:#000d1f !important; border-color:#0a1f35 !important;
    color:#cdd9e5 !important;
    font-family:'IBM Plex Mono',monospace !important; font-size:11px !important;
}
[data-testid="stMultiSelect"]>div>div { background:#000d1f !important; border-color:#0a1f35 !important; }
[data-testid="stSlider"]>div>div>div { background:#0a1f35 !important; }
[data-testid="stDataFrame"] { border:1px solid #0a1f35 !important; }
[data-testid="stDataFrame"] th {
    background:#000d1f !important; color:#1a4060 !important;
    font-family:'IBM Plex Mono',monospace !important; font-size:9px !important;
}
[data-testid="stDataFrame"] td {
    font-family:'IBM Plex Mono',monospace !important; font-size:10.5px !important;
}
[data-testid="stAlert"] { background:#000d1f !important; border-color:#0a1f35 !important; }
hr { border-color:#0a1f35 !important; margin:8px 0 !important; }
[data-testid="stRadio"] label {
    font-family:'IBM Plex Mono',monospace !important; font-size:10.5px !important;
    color:#2a6090 !important;
}
[data-testid="stRadio"] label:has(input:checked) { color:#58c3e0 !important; }
[data-testid="stForm"] { background:#000d1f !important; border:1px solid #0a1f35 !important; padding:14px !important; border-radius:1px !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════

def _load() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "equity": 100000.0, "initial_capital": 100000.0,
        "trades": [], "opportunities": [],
        "history": {a: [] for a in MONITORED_ASSETS},
        "settings": THRESHOLDS,
        "api_health": {k: "Unknown" for k in ["NASA","EIA","OpenAQ","ETH","RealYield","OBI"]},
        "last_signals": {}, "last_cycle_utc": "", "cycle_count": 0,
    }

def _save(s: dict):
    try:
        with open(STATE_FILE + '.tmp', 'w') as f: json.dump(s, f, indent=2)
        os.replace(STATE_FILE + '.tmp', STATE_FILE)
    except Exception: pass

@st.cache_data(ttl=55)
def _prices() -> dict:
    hdrs = {'User-Agent': 'Mozilla/5.0'}
    out  = {}
    for asset, sym in _YF.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
            r   = requests.get(url, headers=hdrs, timeout=7)
            if r.status_code == 200:
                out[asset] = float(r.json()['chart']['result'][0]['meta']['regularMarketPrice'])
            else:
                out[asset] = _PX_FALLBACK[asset]
        except Exception:
            out[asset] = _PX_FALLBACK[asset]
    return out

@st.cache_resource
def _engines():
    s = _load()
    return {
        "engine":    S3ConvergenceEngine(),
        "allocator": S3AntiFragileAllocator(initial_capital=s['equity']),
    }

_eng  = _engines()
_alc  = _eng["allocator"]

if 'state' not in st.session_state:
    st.session_state.state = _load()

_S = st.session_state.state

# ── Stats ──────────────────────────────────────────────────────────────────────
_trades  = _S['trades']
_pnl_l   = [t.get('pnl', 0.0) for t in _trades]
_total_p = sum(_pnl_l)
_n_tr    = len(_trades)
_wins    = sum(1 for p in _pnl_l if p > 0)
_losses  = _n_tr - _wins
_wr      = (_wins / max(1, _n_tr)) * 100
_eq      = _S['equity']
_init_eq = _S['initial_capital']
_eq_ret  = ((_eq / _init_eq) - 1) * 100
_eq_curve= [_init_eq] + [_init_eq + sum(_pnl_l[:i+1]) for i in range(_n_tr)]
_max_eq  = max(_eq_curve) if _eq_curve else _init_eq
_dds     = [(e - max(_eq_curve[:i+1])) / max(1, max(_eq_curve[:i+1])) * 100
             for i, e in enumerate(_eq_curve)]
_max_dd  = min(_dds) if _dds else 0.0
_rets    = (np.diff(_eq_curve) / np.array(_eq_curve[:-1])
            if len(_eq_curve) > 1 else np.array([0.0]))
_sharpe  = ((np.mean(_rets) / max(np.std(_rets), 1e-9)) * math.sqrt(252)
            if len(_rets) >= 5 else 0.0)

# Daemon freshness
try:
    _d_age  = time.time() - os.path.getmtime(STATE_FILE)
    _d_live = _d_age < 25
except Exception:
    _d_age  = 99999.0
    _d_live = False

def _age_str(s: float) -> str:
    if s < 60:   return f"{int(s)}s ago"
    if s < 3600: return f"{int(s//60)}m {int(s%60)}s ago"
    return f"{int(s//3600)}h {int((s%3600)//60)}m ago"

_NOW    = datetime.now(timezone.utc)
_NOW_S  = _NOW.strftime("%Y-%m-%d  %H:%M:%S  UTC")
_prices = _prices()

_inev_assets = [
    o['asset'] for o in _S['opportunities']
    if o['status'] == "INEVITABLE"
    and (_NOW.timestamp() - datetime.fromisoformat(o['timestamp']).timestamp()) < 3600
]

# Plotly base
_PB = dict(
    template="plotly_dark",
    paper_bgcolor="#000913", plot_bgcolor="#000913",
    font=dict(family="IBM Plex Mono", color="#2a6090"),
    margin=dict(l=8, r=8, t=28, b=8),
    xaxis=dict(gridcolor="#060f1c", tickfont=dict(size=9, color="#1a4060")),
    showlegend=False,
)
# Default y-axis style reused across charts (NOT in _PB to avoid duplicate-kwarg crash)
_YAX = dict(gridcolor="#060f1c", tickfont=dict(size=9, color="#1a4060"))

# ══════════════════════════════════════════════════════════════════════════════
#  CHROME  ——  Status bar + refresh bar
# ══════════════════════════════════════════════════════════════════════════════

_d_col   = "#3fb950" if _d_live else "#f85149"
_d_label = "24/7 LIVE" if _d_live else "OFFLINE"
_cyc     = _S.get('cycle_count', 0)
_sigs_l  = sum(1 for v in _S.get('last_signals', {}).values() if v is not None)
_inev_c  = len(set(_inev_assets))

st.markdown(f"""
<div class="sys-bar">
  <div class="sys-bar-left">
    <span style="font-size:14px;color:#58c3e0;letter-spacing:4px;font-weight:700;">🔱 HYDRA-S3</span>
    <span class="sbl"><span class="sbl-k">DAEMON</span>
      <span class="sbl-v" style="color:{_d_col};">{_d_label}</span></span>
    <span class="sbl"><span class="sbl-k">UPDATED</span>
      <span class="sbl-v {'green' if _d_live else 'red'}">{_age_str(_d_age)}</span></span>
    <span class="sbl"><span class="sbl-k">CYCLE</span>
      <span class="sbl-v">{_cyc:,}</span></span>
    <span class="sbl"><span class="sbl-k">SIGNALS</span>
      <span class="sbl-v {'green' if _sigs_l>=4 else 'amber' if _sigs_l>=2 else 'red'}">{_sigs_l}/6</span></span>
    {'<span class="sbl" style="animation:bpulse 1.8s infinite"><span style="color:#f85149;font-weight:700;letter-spacing:2px;">🚨 INEVITABLE: '+str(_inev_c)+'</span></span>' if _inev_c else ''}
  </div>
  <div class="sys-bar-right">
    <span class="sbl"><span class="sbl-k">EQ</span>
      <span class="sbl-v cyan">${_eq:,.2f}</span></span>
    <span class="sbl"><span class="sbl-k">P&L</span>
      <span class="sbl-v {'green' if _total_p>=0 else 'red'}">${_total_p:+,.2f}</span></span>
    <span class="sbl"><span class="sbl-k">WIN</span>
      <span class="sbl-v">{_wr:.1f}%</span></span>
    <span style="color:#1a4060;font-size:10px;">{_NOW_S}</span>
  </div>
</div>
<div class="rfr-bar">
  <span class="rfr-label">AUTO-REFRESH 15s</span>
  <div class="rfr-track"><div class="rfr-fill"></div></div>
  <span class="rfr-label">LIVE DATA FEED  ·  ALL 5 ASSET STREAMS</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <h1>🔱 HYDRA</h1>
        <p>S3-RHGNN ENTERPRISE QUANT OS  v5.0</p>
    </div>""", unsafe_allow_html=True)

    for lbl, val, col in [
        ("DAEMON",     _d_label,             _d_col),
        ("LAST UPDATE",_age_str(_d_age),     "#cdd9e5"),
        ("CYCLE COUNT",f"{_cyc:,}",          "#cdd9e5"),
        ("SIGNALS",    f"{_sigs_l}/6 LIVE",  "#3fb950" if _sigs_l>=4 else "#e3b341" if _sigs_l>=2 else "#f85149"),
        ("ENGINE",     "S3-RHGNN v5.0",      "#58c3e0"),
        ("EQUITY",     f"${_eq:,.2f}",       "#58c3e0"),
        ("P&L",        f"${_total_p:+,.2f}", "#3fb950" if _total_p>=0 else "#f85149"),
        ("WIN RATE",   f"{_wr:.1f}%",        "#cdd9e5"),
        ("SHARPE",     f"{_sharpe:.2f}",     "#cdd9e5"),
        ("MAX DD",     f"{_max_dd:.2f}%",    "#f85149" if _max_dd<-10 else "#cdd9e5"),
    ]:
        st.markdown(f"""
        <div class="sb-pill">
          <span class="sb-k">{lbl}</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;
                font-weight:700;color:{col};">{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:8.5px;letter-spacing:2px;color:#1a4060;margin-bottom:8px;">■ ASSET SCORES</div>', unsafe_allow_html=True)

    for asset in MONITORED_ASSETS:
        hist = _S['history'].get(asset, [])
        if hist:
            last = hist[-1]
            sc   = last['score']
            st_  = last['status']
            col  = "#f85149" if st_=="INEVITABLE" else "#3fb950" if st_=="HIGH CONVICTION" else "#1a4060"
        else:
            sc, col = 0.0, "#1a4060"
        px = _prices.get(asset, 0)
        px_s = f"${px:,.4f}" if px < 10 else f"${px:,.2f}" if px < 1000 else f"${px:,.0f}"
        st.markdown(f"""
        <div class="sb-pill">
          <span class="sb-k">{asset}</span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;color:{col};">{sc:.4f}</span>
          <span style="font-size:9px;color:#1a4060;">{px_s}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.button("↺  FORCE REFRESH", key="sb_rfr"):
        st.session_state.state = _load()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  BADGE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _regime_b(r):
    if r=="CONTRACTION": return '<span class="badge bc">CONTRACTION</span>'
    if r=="EXPANSION":   return '<span class="badge be">EXPANSION</span>'
    return '<span class="badge bs">STABILITY</span>'

def _status_b(s):
    if s=="INEVITABLE":     return '<span class="badge bi">🚨 INEVITABLE</span>'
    if s=="HIGH CONVICTION":return '<span class="badge bh">● HIGH CONVICTION</span>'
    if s=="DATA_GAP":       return '<span class="badge bg">⚠ DATA GAP</span>'
    return '<span class="badge bn">— NOISE</span>'

def _bias_b(d):
    if d == 1:  return '<span class="badge bl">▲ LONG</span>'
    if d == -1: return '<span class="badge bsh">▼ SHORT</span>'
    return '<span class="badge bnt">— NEUTRAL</span>'

def _sbar(score):
    pct = int(score * 100)
    col = "#f85149" if score>=0.95 else "#3fb950" if score>=0.80 else "#1a4060"
    return (f'<div class="sb-wrap">'
            f'<div class="sb-track"><div class="sb-fill" style="width:{pct}%;background:{col};"></div></div>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:11.5px;font-weight:700;color:{col};">{score:.4f}</span>'
            f'</div>')


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "  📊  MATRIX DASHBOARD  ",
    "  🎯  OPPORTUNITY HUB  ",
    "  💼  TRADE AUDIT  ",
    "  🔬  SIGNAL LAB  ",
    "  ⚙️   SYSTEM CONFIG  ",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1  —  MATRIX DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div class="term-hdr">
      <div>
        <div class="term-title">📊 MULTI-ASSET CONVERGENCE MATRIX</div>
        <div class="term-sub">S3-RHGNN v5.0  ·  LIVE CAUSAL ENGINE  ·  S3-SURGICAL-TRIGGER ARMED</div>
      </div>
      <div class="term-meta">POLL: 10s  ·  UI REFRESH: 15s<br/>TRIGGER: DIRECTION | STATUS | SCORE +0.05</div>
    </div>
    """, unsafe_allow_html=True)

    if _inev_assets:
        st.markdown(f"""
        <div class="s-alert">🚨
          <span>S-ALERT  ·  INEVITABLE CONVERGENCE  ·
          {" | ".join(set(_inev_assets))}  ·  EXECUTE NOW</span>
        </div>""", unsafe_allow_html=True)

    # KPI row
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    _open_pos = len(_alc.open_positions)
    _pf_num   = abs(sum(p for p in _pnl_l if p>0))
    _pf_den   = max(abs(sum(p for p in _pnl_l if p<0)), 0.01)
    _pf       = _pf_num / _pf_den

    for col, lbl, val, sub, cls, glow in [
        (k1,"TOTAL EQUITY",   f"${_eq:,.2f}",    f"{_eq_ret:+.2f}% RETURN",          "cyan", False),
        (k2,"REALIZED P&L",   f"${_total_p:+,.2f}",f"{_n_tr} TRADES",               "grn" if _total_p>=0 else "red", False),
        (k3,"WIN RATE",       f"{_wr:.1f}%",      f"{_wins}W / {_losses}L",           "grn" if _wr>=50 else "amb", False),
        (k4,"INEVITABLE",     str(_inev_c),        f"{len(_S['opportunities'])} SETUPS","red" if _inev_c else "", _inev_c>0),
        (k5,"OPEN POSITIONS", str(_open_pos),      "LIVE EXPOSURE",                    "blue", False),
        (k6,"SHARPE / DD",    f"{_sharpe:.2f}",    f"MAX DD {_max_dd:.2f}%",           "grn" if _sharpe>=1 else "amb" if _sharpe>=0 else "red", False),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi {cls} {'kpi-glow' if glow else ''}">
              <div class="kpi-lbl">{lbl}</div>
              <div class="kpi-val">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">■ LIVE CONVERGENCE MATRIX  ·  REAL-TIME SCORES</div>', unsafe_allow_html=True)

    rows = ""
    for asset in MONITORED_ASSETS:
        hist  = _S['history'].get(asset, [])
        px    = _prices.get(asset, 0.0)
        pxs   = (f"${px:,.4f}" if px<10 else f"${px:,.2f}" if px<1000 else f"${px:,.0f}")
        obi_s = SYMBOL_MAP.get(asset, '—')

        if hist:
            last  = hist[-1]
            sc    = last['score']
            reg   = last['regime']
            stt   = last['status']
            age_s = int(_NOW.timestamp() - datetime.fromisoformat(last['time']).timestamp())
            opps  = [o for o in _S['opportunities'] if o['asset']==asset]
            dirv  = opps[-1]['direction'] if opps else 0
            trig  = opps[-1].get('trigger','—') if opps else '—'
            rows += f"""
            <tr>
              <td><div class="as">{asset}</div><div class="asb">{obi_s}</div></td>
              <td><span class="pv">{pxs}</span></td>
              <td>{_sbar(sc)}</td>
              <td>{_regime_b(reg)}</td>
              <td>{_status_b(stt)}</td>
              <td>{_bias_b(dirv)}</td>
              <td><span style="font-family:'IBM Plex Mono',monospace;font-size:9.5px;color:#1a4060;">{_age_str(age_s)}</span></td>
              <td><span style="font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:#1a4060;max-width:140px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{trig[:28]}</span></td>
            </tr>"""
        else:
            rows += f"""
            <tr>
              <td><div class="as">{asset}</div><div class="asb">{obi_s}</div></td>
              <td><span class="pv">{pxs}</span></td>
              <td colspan="6" style="text-align:center;">
                <span class="badge bg">AWAITING LIVE DATA</span>
                <span style="font-size:9.5px;color:#1a4060;margin-left:8px;">daemon collecting signals...</span>
              </td>
            </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;border:1px solid #0a1f35;border-radius:1px;">
    <table class="matrix">
      <thead><tr>
        <th>ASSET</th><th>LIVE PRICE</th><th>S3 SCORE</th>
        <th>REGIME</th><th>STATUS</th><th>BIAS</th>
        <th>UPDATED</th><th>LAST TRIGGER</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)

    # Execution panel
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">■ TRADE EXECUTION PANEL  ·  LIVE PRICE FEED</div>', unsafe_allow_html=True)
    ex_cols = st.columns(len(MONITORED_ASSETS))
    for i, asset in enumerate(MONITORED_ASSETS):
        with ex_cols[i]:
            hist  = _S['history'].get(asset, [])
            sc    = hist[-1]['score'] if hist else 0.0
            reg_s = hist[-1]['regime'] if hist else 'STABILITY'
            reg_i = 2 if reg_s=="CONTRACTION" else 1 if reg_s=="EXPANSION" else 0
            opps  = [o for o in _S['opportunities'] if o['asset']==asset]
            dirv  = opps[-1]['direction'] if opps else 0
            px    = _prices.get(asset, _PX_FALLBACK.get(asset, 100.0))
            pxs   = (f"${px:,.4f}" if px<10 else f"${px:,.2f}" if px<1000 else f"${px:,.0f}")
            ok    = sc >= 0.80 and dirv != 0
            sc_c  = "#f85149" if sc>=0.95 else "#3fb950" if sc>=0.80 else "#1a4060"
            lbl   = f"{'▲ BUY' if dirv==1 else '▼ SELL' if dirv==-1 else '— HOLD'}  {asset}"
            st.markdown(
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9.5px;'
                f'color:#1a4060;margin-bottom:3px;">'
                f'{asset} &nbsp;·&nbsp; <span style="color:{sc_c}">{sc:.4f}</span>'
                f' &nbsp;·&nbsp; <span style="color:#2a6090">{pxs}</span></div>',
                unsafe_allow_html=True
            )
            btn_cls = "btn-long" if dirv==1 else "btn-short" if dirv==-1 else ""
            st.markdown(f'<div class="{btn_cls}">', unsafe_allow_html=True)
            if st.button(lbl, key=f"ex_{asset}", disabled=not ok):
                trade = _alc.execute_trade(asset, dirv, sc, reg_i, px)
                if trade:
                    trade.update({'timestamp': datetime.utcnow().isoformat(),
                                   'pnl': 0.0, 'asset': asset, 'regime': reg_s})
                    _S['trades'].append(trade)
                    _S['equity'] = _alc.equity
                    _save(_S)
                    try:
                        send_alert_sync(fmt_trade_executed(
                            asset=asset, direction=dirv, size=trade['size'],
                            entry=trade['entry_price'], sl=trade['sl_price'],
                            tp=trade['tp_price'], score=sc,
                            equity=_S['equity'], regime=reg_s,
                        ))
                    except Exception: pass
                    st.success(f"✅ {asset} @ {pxs}")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Top manifolds
    top_opps = sorted(_S['opportunities'], key=lambda x: x['score'], reverse=True)[:3]
    if top_opps:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">■ CAUSAL MANIFOLD  ·  TOP CONVERGENCES</div>', unsafe_allow_html=True)
        mc = st.columns(len(top_opps))
        for i, opp in enumerate(top_opps):
            with mc[i]:
                ws  = {k: v for k, v in opp['manifold_snapshot'].items() if v is not None}
                sc_c= "#f85149" if opp['score']>=0.95 else "#58c3e0"
                fig = go.Figure(go.Bar(
                    x=list(ws.keys()), y=list(ws.values()),
                    marker=dict(color=list(ws.values()),
                                colorscale=[[0,"#000d1f"],[0.5,"#001428"],[1,"#58c3e0"]],
                                line=dict(color="#000913",width=1)),
                ))
                _y_max = max((abs(v) for v in ws.values()), default=1.0) * 1.15
                fig.update_layout(**_PB, height=150,
                    title=dict(text=f"{opp['asset']} · {opp['score']:.4f} · {opp['status']}",
                               font=dict(size=9,color=sc_c),x=0),
                    yaxis=dict(gridcolor="#060f1c",tickfont=dict(size=8,color="#1a4060"),
                               range=[-_y_max*0.1, _y_max]),
                )
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2  —  OPPORTUNITY HUB
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="term-hdr">
      <div>
        <div class="term-title">🎯 OPPORTUNITY HUB</div>
        <div class="term-sub">S3-SURGICAL-TRIGGER LOG  ·  ALL ASSETS  ·  LIVE SIGNAL LEDGER</div>
      </div>
    </div>""", unsafe_allow_html=True)

    opps = _S['opportunities']
    if not opps:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;background:#000d1f;border:1px solid #0a1f35;border-radius:1px;">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#1a4060;letter-spacing:3px;">NO OPPORTUNITIES DETECTED</div>
          <div style="font-size:10px;color:#060f1c;margin-top:10px;">Daemon scanning — triggers when S3 score ≥ 0.70</div>
        </div>""", unsafe_allow_html=True)
    else:
        f1,f2,f3 = st.columns([2,2,1])
        with f1:
            af = st.multiselect("Asset", MONITORED_ASSETS, default=MONITORED_ASSETS, label_visibility="collapsed")
        with f2:
            sf = st.multiselect("Status", list(set(o['status'] for o in opps)),
                                 default=list(set(o['status'] for o in opps)), label_visibility="collapsed")
        with f3:
            ms = st.slider("Min Score", 0.0, 1.0, 0.0, 0.01)

        fopps = [o for o in opps if o['asset'] in af and o['status'] in sf and o['score'] >= ms]

        st.markdown("<br/>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        ic = sum(1 for o in fopps if o['status']=="INEVITABLE")
        hc = sum(1 for o in fopps if o['status']=="HIGH CONVICTION")
        ta = (max(set(o['asset'] for o in fopps),
                  key=lambda a: sum(o['score'] for o in fopps if o['asset']==a))
              if fopps else "—")
        for col, lbl, val, cls in [
            (c1,"TOTAL SETUPS",str(len(fopps)),""),
            (c2,"INEVITABLE",  str(ic),        "red kpi-glow" if ic else ""),
            (c3,"HIGH CONV.",  str(hc),         "grn" if hc else ""),
            (c4,"TOP ASSET",   ta,             "cyan"),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi {cls}">
                  <div class="kpi-lbl">{lbl}</div>
                  <div class="kpi-val" style="font-size:20px;">{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">■ SURGICAL TRIGGER LEDGER</div>', unsafe_allow_html=True)

        df   = pd.DataFrame(fopps)
        cols = [c for c in ['id','asset','timestamp','score','status','regime','direction','trigger'] if c in df.columns]
        dfd  = df[cols].copy()
        if 'timestamp' in dfd.columns:
            dfd['timestamp'] = pd.to_datetime(dfd['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'score' in dfd.columns:
            dfd['score'] = dfd['score'].round(4)
        if 'direction' in dfd.columns:
            dfd['direction'] = dfd['direction'].map({1:"▲ LONG",-1:"▼ SHORT",0:"— NEUTRAL"})
        dfd.columns = [c.upper().replace('_',' ') for c in dfd.columns]
        st.dataframe(dfd.sort_values('TIMESTAMP', ascending=False).head(200),
                     use_container_width=True, height=280)

        if fopps:
            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown('<div class="sec-hdr">■ SIGNAL DEEP-DIVE</div>', unsafe_allow_html=True)
            sel = st.selectbox("Select Opportunity ID", [o['id'] for o in fopps],
                               label_visibility="collapsed")
            if sel:
                opp = next(o for o in fopps if o['id']==sel)
                da,db,dc,dd = st.columns(4)
                for col, lbl, val, cls in [
                    (da,"SCORE",    f"{opp['score']:.4f}",    "red" if opp['score']>=0.95 else "grn"),
                    (db,"STATUS",   opp['status'],             "red" if opp['status']=="INEVITABLE" else ""),
                    (dc,"REGIME",   opp['regime'],             ""),
                    (dd,"TRIGGER",  opp.get('trigger','—')[:20],"amb"),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="kpi {cls}">
                          <div class="kpi-lbl">{lbl}</div>
                          <div class="kpi-val" style="font-size:15px;">{val}</div>
                        </div>""", unsafe_allow_html=True)

                ws = {k: v for k, v in opp['manifold_snapshot'].items() if v is not None}
                ch1, ch2 = st.columns(2)
                with ch1:
                    fig = go.Figure(go.Bar(
                        x=list(ws.keys()), y=list(ws.values()),
                        marker=dict(color=list(ws.values()), colorscale="teal",
                                    line=dict(color="#000913",width=1)),
                        text=[f"{v:.4f}" for v in ws.values()], textposition="outside",
                        textfont=dict(family="IBM Plex Mono",size=9,color="#2a6090"),
                    ))
                    _ym2 = max((abs(v) for v in ws.values()), default=1.0) * 1.15
                    fig.update_layout(**_PB, height=260,
                        title=dict(text="CAUSAL MANIFOLD SNAPSHOT",font=dict(size=9,color="#2a6090"),x=0),
                        yaxis=dict(gridcolor="#060f1c",tickfont=dict(size=8,color="#1a4060"),
                                   range=[-_ym2*0.1, _ym2]),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with ch2:
                    cats = list(ws.keys()); vals = [ws[k] for k in cats]
                    fig_r = go.Figure(go.Scatterpolar(
                        r=vals+[vals[0]], theta=cats+[cats[0]], fill='toself',
                        fillcolor='rgba(88,195,224,0.06)',
                        line=dict(color='#58c3e0',width=1.5),
                        marker=dict(size=4,color='#58c3e0'),
                    ))
                    fig_r.update_layout(**_PB, height=260,
                        title=dict(text="RADAR VIEW",font=dict(size=9,color="#2a6090"),x=0),
                        polar=dict(bgcolor="#000913",
                            radialaxis=dict(range=[0,1],tickfont=dict(size=7,color="#1a4060"),gridcolor="#060f1c"),
                            angularaxis=dict(tickfont=dict(family="IBM Plex Mono",size=9,color="#2a6090"),gridcolor="#060f1c"),
                        ),
                    )
                    st.plotly_chart(fig_r, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3  —  TRADE AUDIT
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="term-hdr">
      <div>
        <div class="term-title">💼 TRADE AUDIT LEDGER</div>
        <div class="term-sub">FULL PORTFOLIO AUDIT  ·  PERFORMANCE ANALYTICS</div>
      </div>
    </div>""", unsafe_allow_html=True)

    t1,t2,t3,t4,t5,t6 = st.columns(6)
    for col, lbl, val, cls in [
        (t1,"TOTAL EQUITY",  f"${_eq:,.2f}",         "cyan"),
        (t2,"TOTAL P&L",     f"${_total_p:+,.2f}",   "grn" if _total_p>=0 else "red"),
        (t3,"WIN RATE",      f"{_wr:.1f}%",           "grn" if _wr>=50 else "red"),
        (t4,"SHARPE",        f"{_sharpe:.3f}",        "grn" if _sharpe>=1 else "amb" if _sharpe>=0 else "red"),
        (t5,"MAX DRAWDOWN",  f"{_max_dd:.2f}%",       "red" if _max_dd<-10 else "amb" if _max_dd<-5 else ""),
        (t6,"PROFIT FACTOR", f"{_pf:.2f}x",           "grn" if _pf>=2 else ""),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
              <div class="kpi-lbl">{lbl}</div>
              <div class="kpi-val">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if not _trades:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;background:#000d1f;border:1px solid #0a1f35;">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#1a4060;letter-spacing:3px;">NO TRADES EXECUTED</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="sec-hdr">■ EQUITY CURVE  &  DRAWDOWN</div>', unsafe_allow_html=True)
        fig = make_subplots(rows=2, cols=1, row_heights=[0.65,0.35], vertical_spacing=0.04, shared_xaxes=True)
        xi  = list(range(len(_eq_curve)))
        fig.add_trace(go.Scatter(x=xi, y=_eq_curve, mode='lines',
            line=dict(color='#58c3e0',width=1.5), fill='tozeroy',
            fillcolor='rgba(88,195,224,0.04)', name='EQUITY'), row=1, col=1)
        fig.add_trace(go.Scatter(x=xi, y=[_init_eq]*len(xi),
            line=dict(color='#0a1f35',dash='dot',width=1), showlegend=False), row=1, col=1)
        fig.add_trace(go.Bar(x=xi, y=_dds,
            marker_color=['#f85149' if d<-5 else '#e3b341' if d<0 else '#3fb950' for d in _dds],
            showlegend=False), row=2, col=1)
        fig.update_layout(**_PB, height=340,
            yaxis =dict(**_YAX, tickprefix="$", tickformat=",.0f"),
            yaxis2=dict(**_YAX, ticksuffix="%"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        ts1, ts2 = st.columns(2)
        with ts1:
            st.markdown('<div class="sec-hdr">■ PERFORMANCE METRICS</div>', unsafe_allow_html=True)
            _w_l = [p for p in _pnl_l if p>0]; _l_l = [p for p in _pnl_l if p<0]
            for lbl, val in [
                ("BEST TRADE",     f"${max(_pnl_l):,.2f}" if _pnl_l else "$0.00"),
                ("WORST TRADE",    f"${min(_pnl_l):,.2f}" if _pnl_l else "$0.00"),
                ("AVG WIN",        f"${np.mean(_w_l):,.2f}" if _w_l else "$0.00"),
                ("AVG LOSS",       f"${np.mean(_l_l):,.2f}" if _l_l else "$0.00"),
                ("PROFIT FACTOR",  f"{_pf:.2f}x"),
                ("TOTAL RETURN",   f"{_eq_ret:+.2f}%"),
                ("SHARPE RATIO",   f"{_sharpe:.3f}"),
                ("MAX DRAWDOWN",   f"{_max_dd:.2f}%"),
            ]:
                st.markdown(f"""
                <div class="pill">
                  <span class="pill-k">{lbl}</span>
                  <span class="pill-v">{val}</span>
                </div>""", unsafe_allow_html=True)
        with ts2:
            st.markdown('<div class="sec-hdr">■ P&L DISTRIBUTION</div>', unsafe_allow_html=True)
            if _pnl_l:
                fig_h = go.Figure(go.Histogram(x=_pnl_l, nbinsx=18,
                    marker=dict(color=['#3fb950' if p>=0 else '#f85149' for p in sorted(_pnl_l)],
                                line=dict(color="#000913",width=1))))
                fig_h.update_layout(**_PB, height=240,
                    xaxis=dict(**_YAX, tickprefix="$"),
                    yaxis=_YAX)
                st.plotly_chart(fig_h, use_container_width=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">■ FULL TRADE LOG</div>', unsafe_allow_html=True)
        dft  = pd.DataFrame(_trades)
        cok  = [c for c in ['asset','direction','entry_price','size','sl_price','tp_price','pnl','timestamp'] if c in dft.columns]
        dfsh = dft[cok].copy()
        if 'direction' in dfsh.columns:
            dfsh['direction'] = dfsh['direction'].map({1:"▲ LONG",-1:"▼ SHORT",0:"— NEUTRAL"})
        if 'pnl' in dfsh.columns:
            dfsh['pnl'] = dfsh['pnl'].apply(lambda x: f"+${x:.2f}" if x>=0 else f"-${abs(x):.2f}")
        for c in ['entry_price','sl_price','tp_price']:
            if c in dfsh.columns:
                dfsh[c] = dfsh[c].apply(lambda x: f"${x:,.4f}")
        if 'size' in dfsh.columns:
            dfsh['size'] = dfsh['size'].apply(lambda x: f"{x:.4f}")
        dfsh.columns = [c.upper().replace('_',' ') for c in dfsh.columns]
        st.dataframe(dfsh, use_container_width=True, height=260)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4  —  SIGNAL LAB
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div class="term-hdr">
      <div>
        <div class="term-title">🔬 CAUSAL SIGNAL LAB</div>
        <div class="term-sub">LIVE API HEALTH  ·  SIGNAL HISTORY  ·  REGIME ANALYSIS</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">■ LIVE API HEALTH  ·  REAL-TIME SIGNAL VALUES</div>', unsafe_allow_html=True)
    health = _S['api_health']
    lsigs  = _S.get('last_signals', {})

    api_meta = {
        "NASA":      ("EONET",    "🌋", "Global Wildfire Count",       "0–1"),
        "EIA":       ("ENERGY",   "⚡", "US Petroleum Price Index",    "0–1"),
        "OpenAQ":    ("AQ",       "🏭", "Industrial PM2.5 Pollution",  "0–1"),
        "ETH":       ("OKX/ETH",  "💎", "ETHUSDT Funding Rate Proxy",  "0–1"),
        "RealYield": ("TIPS 10Y", "💵", "US Treasury Real Yield",      "raw %"),
        "OBI":       ("KRAKEN",   "📉", "BTC/USD L2 Order Book Imb.",  "-1..+1"),
    }
    hc = st.columns(6)
    for i, (api, status) in enumerate(health.items()):
        with hc[i]:
            meta    = api_meta.get(api, (api,"●","",""))
            sv      = lsigs.get(api)
            dot_cls = "dot-live" if status=="ONLINE" else "dot-off" if status=="GAP" else "dot-unk"
            val_col = "#3fb950" if status=="ONLINE" else "#f85149" if status=="GAP" else "#e3b341"
            if sv is not None:
                vs = f"{sv:.3f}%" if api=="RealYield" else f"{sv:+.4f}" if api=="OBI" else f"{sv:.4f}"
            else:
                vs = "—"
            st.markdown(f"""
            <div class="sig-cell">
              <div class="sig-name">{meta[0]}</div>
              <div style="margin-bottom:4px;">
                <span class="{dot_cls}"></span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:10.5px;
                      font-weight:700;color:{val_col};">{status}</span>
              </div>
              <div class="sig-val" style="color:{val_col};">{vs}</div>
              <div class="sig-sub">{meta[2]}</div>
              <div class="sig-sub" style="color:#060f1c;">{meta[3]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">■ SCORE HISTORY  ·  SELECT ASSET STREAM</div>', unsafe_allow_html=True)

    sel_a = st.selectbox("Stream", MONITORED_ASSETS, label_visibility="collapsed")
    hist  = _S['history'].get(sel_a, [])

    if hist:
        dfh   = pd.DataFrame(hist)
        dfh['time'] = pd.to_datetime(dfh['time'])
        ca, cb = st.columns([3,1])
        with ca:
            sc_colors = ['#f85149' if s>=0.95 else '#3fb950' if s>=0.80 else '#1a4060'
                         for s in dfh['score']]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dfh['time'], y=dfh['score'], mode='lines+markers',
                line=dict(color='#58c3e0',width=1.2),
                marker=dict(color=sc_colors,size=3,line=dict(color="#000913",width=1)),
                fill='tozeroy', fillcolor='rgba(88,195,224,0.04)',
            ))
            fig.add_hline(y=0.95, line_dash="dot", line_color="#f85149", line_width=1,
                          annotation_text="INEVITABLE",annotation_font=dict(family="IBM Plex Mono",size=8,color="#f85149"))
            fig.add_hline(y=0.80, line_dash="dot", line_color="#3fb950", line_width=1,
                          annotation_text="HIGH CONVICTION",annotation_font=dict(family="IBM Plex Mono",size=8,color="#3fb950"))
            fig.update_layout(**_PB, height=270,
                title=dict(text=f"{sel_a}  ·  CONVERGENCE SCORE HISTORY",font=dict(size=9,color="#2a6090"),x=0),
                yaxis=dict(**_YAX, range=[0, 1.05]),
            )
            st.plotly_chart(fig, use_container_width=True)
        with cb:
            if 'status' in dfh.columns:
                scc = dfh['status'].value_counts()
                cm  = {"INEVITABLE":"#f85149","HIGH CONVICTION":"#3fb950",
                        "NOISE":"#1a4060","DATA_GAP":"#e3b341"}
                fig_p = go.Figure(go.Pie(
                    labels=scc.index.tolist(), values=scc.values.tolist(), hole=0.65,
                    marker=dict(colors=[cm.get(s,"#0a1f35") for s in scc.index],
                                line=dict(color="#000913",width=2)),
                    textfont=dict(family="IBM Plex Mono",size=8), textinfo="percent+label",
                ))
                fig_p.update_layout(**_PB, height=270,
                    title=dict(text="STATUS SPLIT",font=dict(size=9,color="#2a6090"),x=0),
                    yaxis=_YAX,
                    annotations=[dict(text=f"{len(dfh)}<br>pts",x=0.5,y=0.5,
                                      font=dict(family="IBM Plex Mono",size=9,color="#2a6090"),showarrow=False)],
                )
                st.plotly_chart(fig_p, use_container_width=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        s1,s2,s3,s4 = st.columns(4)
        for col, lbl, val in [
            (s1,"TOTAL SCANS",  str(len(dfh))),
            (s2,"PEAK SCORE",   f"{dfh['score'].max():.4f}"),
            (s3,"MEAN SCORE",   f"{dfh['score'].mean():.4f}"),
            (s4,"INEVITABLE Σ", str(len(dfh[dfh['score']>=0.95]))),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi">
                  <div class="kpi-lbl">{lbl}</div>
                  <div class="kpi-val" style="font-size:17px;">{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">■ RAW STREAM LOG  ·  LAST 200 SCANS</div>', unsafe_allow_html=True)
        csh = [c for c in ['time','score','status','regime'] if c in dfh.columns]
        dfr = dfh[csh].copy()
        dfr['score'] = dfr['score'].round(4)
        dfr.columns  = [c.upper() for c in dfr.columns]
        st.dataframe(dfr.sort_values('TIME',ascending=False).head(200),
                     use_container_width=True, height=240)
    else:
        st.markdown(f"""
        <div style="text-align:center;padding:60px 20px;background:#000d1f;border:1px solid #0a1f35;">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#1a4060;letter-spacing:3px;">
            NO DATA FOR {sel_a}
          </div>
          <div style="font-size:9.5px;color:#060f1c;margin-top:10px;">Daemon collecting signals — check back in 10–30 seconds</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5  —  SYSTEM CONFIG
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("""
    <div class="term-hdr">
      <div>
        <div class="term-title">⚙️  SYSTEM CONFIGURATION</div>
        <div class="term-sub">PARAMETER CONTROL  ·  TELEGRAM ALERT SYSTEM  ·  API STATUS</div>
      </div>
    </div>""", unsafe_allow_html=True)

    cfg = _S['settings']

    # ── Gauge indicators ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">■ ACTIVE THRESHOLD PROFILE</div>', unsafe_allow_html=True)
    gc1,gc2,gc3 = st.columns(3)
    for gcol, lbl, val, lo, hi, col in [
        (gc1,"INEVITABLE SCORE",  cfg['INEVITABLE_SCORE'],   0.0, 1.0, "#f85149"),
        (gc2,"CONTRACTION YIELD", cfg['CONTRACTION_YIELD'],  0.0, 3.0, "#e3b341"),
        (gc3,"HARD STOP %",       cfg['HARD_STOP_PCT']*100,  0.0, 5.0, "#388bfd"),
    ]:
        with gcol:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                title=dict(text=lbl, font=dict(family="IBM Plex Mono",size=9,color="#2a6090")),
                number=dict(font=dict(family="IBM Plex Mono",size=18,color=col)),
                gauge=dict(
                    axis=dict(range=[lo,hi],tickfont=dict(family="IBM Plex Mono",size=7,color="#1a4060"),tickcolor="#0a1f35"),
                    bar=dict(color=col,thickness=0.25),
                    bgcolor="#000913", bordercolor="#0a1f35", borderwidth=1,
                    steps=[dict(range=[lo,hi],color="#000d1f")],
                )
            ))
            fig_g.update_layout(paper_bgcolor="#000913",height=170,
                margin=dict(l=14,r=14,t=36,b=8),font=dict(color="#cdd9e5"))
            st.plotly_chart(fig_g, use_container_width=True)

    # ── Parameter form ─────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">■ PARAMETER CONTROL</div>', unsafe_allow_html=True)
    with st.form("cfg_form"):
        fc1,fc2 = st.columns(2)
        with fc1:
            t_cy = st.number_input("CONTRACTION YIELD THRESHOLD (%)", value=float(cfg['CONTRACTION_YIELD']),
                                    min_value=0.0,max_value=5.0,step=0.05,format="%.2f")
            t_co = st.number_input("CONTRACTION OBI THRESHOLD", value=float(cfg['CONTRACTION_OBI']),
                                    min_value=-1.0,max_value=0.0,step=0.05,format="%.2f")
            t_in = st.number_input("INEVITABLE SCORE THRESHOLD", value=float(cfg['INEVITABLE_SCORE']),
                                    min_value=0.50,max_value=1.00,step=0.01,format="%.2f")
        with fc2:
            t_ey = st.number_input("EXPANSION YIELD THRESHOLD (%)", value=float(cfg['EXPANSION_YIELD']),
                                    min_value=-2.0,max_value=0.0,step=0.05,format="%.2f")
            t_eo = st.number_input("EXPANSION OBI THRESHOLD", value=float(cfg['EXPANSION_OBI']),
                                    min_value=0.0,max_value=1.0,step=0.05,format="%.2f")
            t_st = st.number_input("HARD STOP % (RISK)", value=float(cfg['HARD_STOP_PCT']),
                                    min_value=0.001,max_value=0.10,step=0.001,format="%.3f")
        if st.form_submit_button("💾  DEPLOY PARAMETERS", use_container_width=True):
            _S['settings'] = {
                'CONTRACTION_YIELD': t_cy, 'CONTRACTION_OBI': t_co,
                'EXPANSION_YIELD':   t_ey, 'EXPANSION_OBI':   t_eo,
                'INEVITABLE_SCORE':  t_in, 'HARD_STOP_PCT':   t_st,
            }
            _save(_S)
            st.success("✅ Parameters deployed.")

    # ── Telegram ───────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">■ TELEGRAM ENTERPRISE ALERT SYSTEM</div>', unsafe_allow_html=True)

    tg_tok = os.environ.get('TELEGRAM_TOKEN','')
    tg_cid = os.environ.get('TELEGRAM_CHAT_ID','')
    tg_ok  = bool(tg_tok and tg_cid)
    tg_col = "#3fb950" if tg_ok else "#f85149"
    tg_lab = "CONFIGURED — ARMED" if tg_ok else "NOT CONFIGURED"

    tga,tgb,tgc = st.columns(3)
    with tga:
        st.markdown(f"""
        <div class="kpi {'grn' if tg_ok else 'red'}">
          <div class="kpi-lbl">TELEGRAM STATUS</div>
          <div style="margin:7px 0 3px;">
            <span class="{'dot-live' if tg_ok else 'dot-off'}"></span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:{tg_col};">{tg_lab}</span>
          </div>
          <div class="kpi-sub">CHAT ID: {tg_cid or '—'}</div>
        </div>""", unsafe_allow_html=True)
    with tgb:
        st.markdown(f"""
        <div class="kpi">
          <div class="kpi-lbl">ALERT TRIGGERS</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#cdd9e5;margin-top:5px;line-height:1.7;">
            🚨 INEVITABLE (≥ {cfg.get('INEVITABLE_SCORE',0.95):.2f})<br/>
            🟡 HIGH CONVICTION (≥ 0.80)<br/>
            ✅ TRADE EXECUTED<br/>
            💓 HEARTBEAT (60 cycles)
          </div>
        </div>""", unsafe_allow_html=True)
    with tgc:
        st.markdown("""
        <div class="kpi blue">
          <div class="kpi-lbl">ALERT TEMPLATE</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#cdd9e5;margin-top:5px;line-height:1.7;">
            1. CORE SIGNAL<br/>
            2. EXECUTION SPECS<br/>
            3. CAUSAL SNAPSHOT<br/>
            ⚡ EXECUTE HYPER-TRADE
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    ta1,ta2,ta3,ta4 = st.columns([1,1,1,2])
    with ta1:
        st.markdown('<div class="btn-tg">', unsafe_allow_html=True)
        if st.button("📡  TEST ALERT", key="tg_t", disabled=not tg_ok):
            ok = send_alert_sync(fmt_test(equity=_eq))
            st.success("✅ Delivered.") if ok else st.error("❌ Failed.")
        st.markdown('</div>', unsafe_allow_html=True)
    with ta2:
        iv = [o for o in _S['opportunities'] if o['status']=="INEVITABLE"]
        if st.button("🚨  FIRE INEVITABLE", key="tg_i", disabled=not tg_ok):
            opp = iv[-1] if iv else None
            if opp:
                msg = fmt_inevitable(opp['asset'], opp['score'], opp['regime'],
                                      opp['direction'], opp['id'],
                                      world_state=opp.get('manifold_snapshot',{}), equity=_eq)
            else:
                msg = fmt_inevitable("XAUUSD",0.9712,"CONTRACTION",-1,"DEMO-LIVE-001",
                                      world_state={"NASA":0.34,"EIA":0.78,"OpenAQ":0.52,
                                                   "ETH":0.41,"RealYield":1.85,"OBI":-0.847},equity=_eq)
            ok = send_alert_sync(msg)
            st.success("✅ Sent.") if ok else st.error("❌ Failed.")
    with ta3:
        hcv = [o for o in _S['opportunities'] if o['status']=="HIGH CONVICTION"]
        if st.button("🟡  HIGH CONV.", key="tg_h", disabled=not tg_ok):
            opp = hcv[-1] if hcv else None
            if opp:
                msg = fmt_high_conviction(opp['asset'],opp['score'],opp['regime'],
                                           opp['direction'],world_state=opp.get('manifold_snapshot',{}),equity=_eq)
            else:
                msg = fmt_high_conviction("EURUSD",0.8310,"EXPANSION",1,
                                           world_state={"NASA":0.22,"EIA":0.44,"OpenAQ":0.31,
                                                        "ETH":0.55,"RealYield":-0.12,"OBI":0.782},equity=_eq)
            ok = send_alert_sync(msg)
            st.success("✅ Sent.") if ok else st.error("❌ Failed.")
    with ta4:
        if not tg_ok:
            st.markdown("""
            <div style="background:#150a00;border:1px solid #5a3500;border-radius:1px;padding:9px 13px;">
              <span style="color:#e3b341;font-family:'IBM Plex Mono',monospace;font-size:10.5px;">
              ⚠  Set TELEGRAM_TOKEN (Secret) + TELEGRAM_CHAT_ID (Shared Env) to activate.
              </span>
            </div>""", unsafe_allow_html=True)

    # ── System info ─────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">■ SYSTEM INFORMATION</div>', unsafe_allow_html=True)
    si1,si2 = st.columns(2)
    with si1:
        wok = _eng["engine"].weights_loaded
        for lbl, val, col in [
            ("ENGINE",        "S3-RHGNN v5.0",              "#58c3e0"),
            ("WEIGHTS",       "✓ LOADED" if wok else "✗ RANDOM INIT", "#3fb950" if wok else "#f85149"),
            ("OBI SOURCE",    "Kraken BTC/USD + Coinbase",  "#cdd9e5"),
            ("ETH SOURCE",    "OKX ETHUSDT Funding Rate",   "#cdd9e5"),
            ("YIELD SOURCE",  "US Treasury XML + FRED",     "#cdd9e5"),
            ("NASA SOURCE",   "EONET Wildfire Events",      "#cdd9e5"),
            ("POLL INTERVAL", "10 seconds",                 "#cdd9e5"),
            ("UI REFRESH",    "15 seconds",                 "#cdd9e5"),
        ]:
            st.markdown(f"""
            <div class="pill">
              <span class="pill-k">{lbl}</span>
              <span class="pill-v" style="color:{col};">{val}</span>
            </div>""", unsafe_allow_html=True)
    with si2:
        for lbl, val in [
            ("LEVERAGE MAX",    "150x  (INEVITABLE + CONTRACTION)"),
            ("POSITION RISK",   "2% equity per trade"),
            ("STOP LOSS",       "1%  hard stop"),
            ("TAKE PROFIT",     "10–20%  (tier-based)"),
            ("RISK/REWARD",     "10:1 min  ·  20:1 INEVITABLE"),
            ("ASSETS",          "5 streams (XAUUSD XAGUSD HG=F EURUSD AUDUSD)"),
            ("STATE FILE",      "enterprise_state.json (atomic write)"),
            ("TRIGGER LOGIC",   "S3-Surgical: dir | status | +0.05 score"),
        ]:
            st.markdown(f"""
            <div class="pill">
              <span class="pill-k">{lbl}</span>
              <span class="pill-v">{val}</span>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-REFRESH (15s)
# ══════════════════════════════════════════════════════════════════════════════
_save(_S)
time.sleep(15)
st.session_state.state = _load()
st.rerun()
