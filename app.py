import streamlit as st
import asyncio
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os
import time
import logging

# Core Imports
from core.collector import S3CausalCollector
from core.convergence import S3ConvergenceEngine
from core.allocator import S3AntiFragileAllocator
from config import MONITORED_ASSETS, REGIMES, THRESHOLDS, SYMBOL_MAP

# --- LOGGING & STATE ---
STATE_FILE = "enterprise_state.json"

def load_enterprise_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "equity": 100000.0,
        "initial_capital": 100000.0,
        "trades": [],
        "opportunities": [],
        "history": {asset: [] for asset in MONITORED_ASSETS},
        "settings": THRESHOLDS,
        "api_health": {k: "Unknown" for k in ["NASA", "EIA", "OpenAQ", "ETH", "RealYield", "OBI"]}
    }

def save_enterprise_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

# --- STREAMLIT CONFIG ---
st.set_page_config(
    page_title="HYDRA-S3 | ENTERPRISE QUANT TERMINAL",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Grade A Professional CSS (Bloomberg/Reuters Terminal Style)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }
    
    .main { background-color: #05070a; color: #c9d1d9; }
    
    div[data-testid="stMetricValue"] {
        color: #00ffcc !important;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stMetric { 
        background-color: #0d1117; 
        border: 1px solid #30363d; 
        padding: 15px; 
        border-radius: 4px; 
    }
    
    .s-alert-banner {
        background-color: #ff0033;
        color: #ffffff;
        padding: 15px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        border: 2px solid #ffffff;
        animation: pulse-red 1s infinite;
        margin-bottom: 20px;
    }
    
    @keyframes pulse-red {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .enterprise-card {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    
    .matrix-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
    }
    .matrix-table th {
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #30363d;
        color: #8b949e;
    }
    .matrix-table td {
        padding: 12px;
        border-bottom: 1px solid #21262d;
    }
    .status-inevitable { color: #ff0033; font-weight: bold; text-shadow: 0 0 5px #ff0033; }
    .status-noise { color: #8b949e; }
    .status-high { color: #00ffcc; font-weight: bold; }
    
    .sidebar .sidebar-content { background-color: #05070a; border-right: 1px solid #30363d; }
    .stButton>button { width: 100%; background-color: #1f6feb; color: white; font-weight: bold; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# Global State
if 'enterprise_state' not in st.session_state:
    st.session_state.enterprise_state = load_enterprise_state()

@st.cache_resource
def init_engines():
    return {
        "engine": S3ConvergenceEngine(),
        "allocator": S3AntiFragileAllocator(initial_capital=load_enterprise_state()['equity'])
    }

sys_engines = init_engines()
engine = sys_engines["engine"]
allocator = sys_engines["allocator"]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🔱 HYDRA-S3</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.8em; color: #8b949e;'>Enterprise Quant OS v4.0</p>", unsafe_allow_html=True)
    st.divider()
    
    nav = st.radio(
        "SYSTEM MODULES", 
        ["Matrix Dashboard", "Opportunity Hub", "Trade Audit Ledger", "Surgical Causal Lab", "System Configuration"],
        index=0
    )
    
    st.divider()
    st.markdown("### ⚡ DAEMON STATUS")
    try:
        mtime = os.path.getmtime(STATE_FILE)
        if (time.time() - mtime) < 60:
            st.markdown("<span style='color: #3fb950;'>🟢 DAEMON ACTIVE (24/7)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #f85149;'>🔴 DAEMON OFFLINE</span>", unsafe_allow_html=True)
    except:
        st.markdown("<span style='color: #f85149;'>🔴 DAEMON OFFLINE</span>", unsafe_allow_html=True)
    
    st.markdown(f"**Engine**: `S3-RHGNN v4.0` ✅")
    st.markdown(f"**Mode**: `QUANT-AUTOMATION` 🤖")

# --- MODULE 1: MATRIX DASHBOARD ---
if nav == "Matrix Dashboard":
    st.title("📊 QUANT MATRIX DASHBOARD")
    
    state = st.session_state.enterprise_state
    
    # Top KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    trades = state['trades']
    win_rate = (sum(1 for t in trades if t.get('pnl', 0) > 0) / max(1, len(trades)) * 100) if trades else 0.0
    
    kpi1.metric("S3 TOTAL EQUITY", f"${state['equity']:,.2f}")
    kpi2.metric("REALIZED WIN RATE", f"{win_rate:.2f}%")
    kpi3.metric("S3 TOTAL OPPORTUNITIES", len(state['opportunities']))
    kpi4.metric("ACTIVE POSITIONS", len(allocator.open_positions))

    st.divider()

    # GLOBAL S-ALERT BANNER
    inevitable_assets = [o['asset'] for o in state['opportunities'] if o['status'] == "INEVITABLE" and 
                         (datetime.utcnow().timestamp() - datetime.fromisoformat(o['timestamp']).timestamp() < 3600)]
    
    if inevitable_assets:
        st.markdown(f'<div class="s-alert-banner">🚨 S-ALERT: CONVERGENCE INEVITABLE DETECTED FOR: {", ".join(set(inevitable_assets))} 🚨</div>', unsafe_allow_html=True)

    # THE MATRIX VIEW (No switching)
    st.markdown("### 🌐 Multi-Asset Convergence Matrix")
    
    # Create the matrix data
    matrix_html = '<table class="matrix-table"><thead><tr>'
    matrix_html += '<th>ASSET</th><th>SCORE</th><th>REGIME</th><th>STATUS</th><th>BIAS</th><th>ACTION</th></tr></thead><tbody>'
    
    for asset in MONITORED_ASSETS:
        asset_history = state['history'].get(asset, [])
        if asset_history:
            latest = asset_history[-1]
            score = latest['score']
            regime = latest['regime']
            status = latest['status']
            
            # Find bias from latest opportunity
            asset_opps = [o for o in state['opportunities'] if o['asset'] == asset]
            bias = "NEUTRAL"
            if asset_opps:
                b_val = asset_opps[-1]['direction']
                bias = "LONG" if b_val == 1 else "SHORT" if b_val == -1 else "NEUTRAL"
            
            status_class = "status-inevitable" if status == "INEVITABLE" else "status-high" if status == "HIGH CONVICTION" else "status-noise"
            
            matrix_html += f'<tr>'
            matrix_html += f'<td><b>{asset}</b></td>'
            matrix_html += f'<td class="mono">{score:.4f}</td>'
            matrix_html += f'<td>{regime}</td>'
            matrix_html += f'<td class="{status_class}">{status}</td>'
            matrix_html += f'<td>{bias}</td>'
            matrix_html += f'<td><button style="cursor:pointer; background:#1f6feb; color:white; border:none; border-radius:4px; padding:4px 8px;">EXECUTE</button></td>'
            matrix_html += f'</tr>'
        else:
            matrix_html += f'<tr><td><b>{asset}</b></td><td colspan="5" style="text-align:center; color:#484f58;">AWAITING DAEMON DATA...</td></tr>'
            
    matrix_html += '</tbody></table>'
    st.markdown(matrix_html, unsafe_allow_html=True)

    # Lower Section: Real-time Manifolds for Top Opportunities
    st.divider()
    st.markdown("### 📉 Live Causal Flows (Top Convergences)")
    
    top_opps = sorted(state['opportunities'], key=lambda x: x['score'], reverse=True)[:3]
    if top_opps:
        cols = st.columns(len(top_opps))
        for i, opp in enumerate(top_opps):
            with cols[i]:
                st.markdown(f"**{opp['asset']}** | Score: {opp['score']:.4f}")
                ws = opp['manifold_snapshot']
                valid_cols = [k for k, v in ws.items() if v is not None]
                vals = [ws[k] for k in valid_cols]
                fig = go.Figure(go.Bar(x=valid_cols, y=vals, marker_color='#00ffcc'))
                fig.update_layout(template="plotly_dark", height=200, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No high-conviction manifolds to project yet.")

# --- MODULE 2: OPPORTUNITY HUB ---
elif nav == "Opportunity Hub":
    st.title("🎯 OPPORTUNITY HUB")
    
    state = st.session_state.enterprise_state
    if not state['opportunities']:
        st.info("No significant opportunities detected yet.")
    else:
        df_opps = pd.DataFrame(state['opportunities'])
        display_df = df_opps[['id', 'asset', 'timestamp', 'score', 'regime', 'status', 'direction']].copy()
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.markdown("### 📋 All-Asset Setup Ledger")
        st.dataframe(display_df, use_container_width=True)
        
        selected_opp_id = st.selectbox("Deep-Dive Analysis", display_df['id'].tolist())
        if selected_opp_id:
            opp = next(o for o in state['opportunities'] if o['id'] == selected_opp_id)
            st.divider()
            st.markdown(f"### 🔍 Surgical Analysis: {selected_opp_id} ({opp['asset']})")
            d1, d2, d3 = st.columns(3)
            d1.markdown(f"**Convergence Score**\n# {opp['score']:.4f}")
            d2.markdown(f"**Causal Regime**\n# {opp['regime']}")
            d3.markdown(f"**S3 Status**\n# {opp['status']}")
            
            ws = opp['manifold_snapshot']
            valid_cols = [k for k, v in ws.items() if v is not None]
            vals = [ws[k] for k in valid_cols]
            fig = go.Figure(go.Bar(x=valid_cols, y=vals, marker_color='#00ffcc'))
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: TRADE AUDIT LEDGER ---
elif nav == "Trade Audit Ledger":
    st.title("💼 TRADE AUDIT LEDGER")
    state = st.session_state.enterprise_state
    if not state['trades']:
        st.info("No trades executed yet.")
    else:
        st.markdown("### 📈 Portfolio Equity Curve")
        equities = [state['initial_capital']]
        current = state['initial_capital']
        for t in state['trades']:
            current += t.get('pnl', 0)
            equities.append(current)
        fig = px.line(y=equities, template="plotly_dark", color_discrete_sequence=['#00ffcc'])
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pd.DataFrame(state['trades']), use_container_width=True)

# --- MODULE 4: SURGICAL CAUSAL LAB ---
elif nav == "Surgical Causal Lab":
    st.title("🔬 SURGICAL CAUSAL LAB")
    state = st.session_state.enterprise_state
    selected_asset = st.selectbox("SELECT ASSET STREAM", MONITORED_ASSETS)
    if selected_asset in state['history'] and state['history'][selected_asset]:
        df_hist = pd.DataFrame(state['history'][selected_asset])
        df_hist['time'] = pd.to_datetime(df_hist['time'])
        fig = px.line(df_hist, x='time', y='score', template="plotly_dark", color_discrete_sequence=['#00ffcc'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 🌐 API Health Matrix")
        health = state['api_health']
        cols = st.columns(len(health))
        for i, (api, status) in enumerate(health.items()):
            color = "#3fb950" if status == "ONLINE" else "#f85149"
            cols[i].markdown(f'<div class="enterprise-card" style="text-align: center;"><small>{api}</small><br><span style="color: {color}; font-weight: bold;">{status}</span></div>', unsafe_allow_html=True)
    else:
        st.info("No data stream available.")

# --- MODULE 5: SYSTEM CONFIGURATION ---
elif nav == "System Configuration":
    st.title("⚙️ SYSTEM CONFIGURATION")
    state = st.session_state.enterprise_state
    with st.form("config_form"):
        c1, c2 = st.columns(2)
        with c1:
            t_con_yield = st.number_input("Contraction Yield", value=state['settings']['CONTRACTION_YIELD'])
            t_con_obi = st.number_input("Contraction OBI", value=state['settings']['CONTRACTION_OBI'])
            t_inev = st.number_input("Inevitable Score", value=state['settings']['INEVITABLE_SCORE'])
        with c2:
            t_exp_yield = st.number_input("Expansion Yield", value=state['settings']['EXPANSION_YIELD'])
            t_exp_obi = st.number_input("Expansion OBI", value=state['settings']['EXPANSION_OBI'])
            t_stop = st.number_input("Hard Stop %", value=state['settings']['HARD_STOP_PCT'], format="%.4f")
        if st.form_submit_button("💾 APPLY SYSTEM PARAMETERS"):
            state['settings'] = {'CONTRACTION_YIELD': t_con_yield, 'CONTRACTION_OBI': t_con_obi, 'EXPANSION_YIELD': t_exp_yield, 'EXPANSION_OBI': t_exp_obi, 'INEVITABLE_SCORE': t_inev, 'HARD_STOP_PCT': t_stop}
            save_enterprise_state(state)
            st.success("Parameters deployed.")

# --- AUTO-SAVE ---
save_enterprise_state(st.session_state.enterprise_state)
