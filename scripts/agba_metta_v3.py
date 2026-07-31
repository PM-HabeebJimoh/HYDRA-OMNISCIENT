#!/usr/bin/env python3
"""
Agba Metta V3 = v2's SEVEN risk enhancements, applied at 400x with the basket
loss limit tightened to -2%, run NATIVELY per-bar on Daily / 4H / 1H.

Timing is live-correct throughout (user spec):
  signal bar closes -> all 3 same direction -> ENTER NEXT BAR OPEN
  -> 1% stop from actual entry -> exit that bar's close unless stopped.

Enhancements (from scripts/agba_metta_v2.py header, applied per-bar):
  1 min basket strength   mean move on the SIGNAL bar >= 0.30%
  2 vol-adjusted weights  gold shrinks when its ATR-14 is elevated
  3 dynamic leverage      grade A+/A/B  (ladder variant selectable)
  4 basket loss limit     -2% of equity per bar   <-- V3 tightening of v2's -10%
  5 post-stop cooldown    x0.50 leverage on the next signal
  6 profit lock           risk 20% -> 10% once the month clears +1000%
  7 XAU danger filter     halve gold weight after a large adverse wick

NO LOOK-AHEAD: every enhancement is computed from the signal bar and earlier.
(v2 computed `strength` from the trade day's own close while entering at that
day's open - that is look-ahead. Here strength comes from the completed
signal bar, which is the live-correct equivalent.)

Direction handling: the intraday panels have no DFII10, and alignment fires
both ways, so V3 trades LONG and SHORT (same signal universe as V1) rather
than v2's regime-forced SHORT-only. Enhancement 7 is made direction-aware:
upper wick for SHORT, lower wick for LONG.
"""
import json, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
A = ("gold", "eur", "aud")

MIN_BASKET_STRENGTH = 0.0030
ATR_LOOKBACK = 14
ATR_HIGH, ATR_LOW = 0.0180, 0.0110
W_HIGH = {"gold":0.150,"eur":0.425,"aud":0.425}
W_NORM = {"gold":0.250,"eur":0.375,"aud":0.375}
W_LOW  = {"gold":1/3,  "eur":1/3,  "aud":1/3}
BASKET_MAX_LOSS = 0.02          # V3
COOLDOWN_MULT   = 0.50
PROFIT_LOCK_TRIGGER = 10.0
PROFIT_LOCK_RISK    = 0.10
WICK_DANGER = 0.0060

LADDER = {"capped": (400,300,150), "scaled": (400,240,120)}

def atr_pct(keys, panel, i, asset, n=ATR_LOOKBACK):
    """ATR% over the n bars ENDING AT the signal bar i (no look-ahead)."""
    if i < 1: return None
    trs=[]
    for j in range(max(1,i-n+1), i+1):
        cur, prev = panel[keys[j]][asset], panel[keys[j-1]][asset]
        tr = max(cur["high"]-cur["low"], abs(cur["high"]-prev["close"]), abs(cur["low"]-prev["close"]))
        trs.append(tr/cur["open"])
    return sum(trs)/len(trs) if trs else None

def grade(strength, xa, yield_rising, ladder):
    LA, LB, LC = LADDER[ladder]
    score = (strength>=0.0060) + (xa is not None and xa<ATR_HIGH) + bool(yield_rising)
    if score>=3: return "A+", LA
    if score==2: return "A",  LB
    return "B", LC

def run_v3(keys, panel, lo, hi, yields=None, ladder="capped",
           base_risk=0.20, eq0=1e5, enh=True, lev_flat=400, cap=BASKET_MAX_LOSS):
    """enh=False reproduces the old two-parameter V3 stub (400x + cap only)."""
    eq=eq0; peak=eq; cooldown=False; month_start=eq
    rows=[]; rets=[]; nstop=0; ncap=0; nfilt=0
    for i in range(len(keys)-1):
        sk, ek = keys[i], keys[i+1]
        if not (lo <= ek < hi): continue
        s, e_ = panel[sk], panel[ek]
        dn = all(s[a]["close"]<s[a]["open"] for a in A)
        up = all(s[a]["close"]>s[a]["open"] for a in A)
        if dn: side=-1
        elif up: side=1
        else: continue

        strength = sum(abs(s[a]["close"]-s[a]["open"])/s[a]["open"] for a in A)/3

        if enh:
            if strength < MIN_BASKET_STRENGTH:          # 1
                nfilt+=1; continue
            xa = atr_pct(keys, panel, i, "gold")        # 2
            if xa is None or xa>=ATR_HIGH: w=dict(W_HIGH)
            elif xa<=ATR_LOW:              w=dict(W_LOW)
            else:                          w=dict(W_NORM)
            g_prev = panel[sk]["gold"]                  # 7 (direction-aware)
            if side<0: wick=(g_prev["high"]-max(g_prev["open"],g_prev["close"]))/g_prev["open"]
            else:      wick=(min(g_prev["open"],g_prev["close"])-g_prev["low"])/g_prev["open"]
            if wick>WICK_DANGER:
                freed=w["gold"]*0.5; w["gold"]-=freed; w["eur"]+=freed/2; w["aud"]+=freed/2
            yr = yields(sk) if yields else False        # 3
            g, lev = grade(strength, xa, yr, ladder)
            if cooldown: lev*=COOLDOWN_MULT             # 5
            risk = PROFIT_LOCK_RISK if (eq/month_start-1)>=PROFIT_LOCK_TRIGGER else base_risk  # 6
        else:
            w={a:1/3 for a in A}; lev=lev_flat; risk=base_risk; g="-"

        pnl=0.0; stopped=False; legrets=[]
        for a in A:
            b=e_[a]; en=b["open"]; notional=eq*risk*w[a]*lev
            if side<0:
                st=en*1.01; hit=b["high"]>=st; ex=st if hit else b["close"]; r=(en-ex)/en
            else:
                st=en*0.99; hit=b["low"]<=st;  ex=st if hit else b["close"]; r=(ex-en)/en
            if hit: nstop+=1; stopped=True
            pnl += r*notional; legrets.append(r)
        rets.append(sum(legrets)/3*100)

        if cap is not None and pnl < -cap*eq:           # 4
            pnl = -cap*eq; ncap+=1
        eq += pnl; cooldown = stopped
        if eq<=0:
            return dict(ret=-100.,dd=-100.,n=len(rows)+1,eq=0.,wr=0.,stops=nstop,
                        caps=ncap,filtered=nfilt,dead=True,rets=rets)
        peak=max(peak,eq); rows.append((pnl,(eq-peak)/peak*100))
    if not rows:
        return dict(ret=0.,dd=0.,n=0,eq=eq0,wr=0.,stops=0,caps=0,filtered=nfilt,dead=False,rets=[])
    return dict(ret=(eq/eq0-1)*100, dd=min(r[1] for r in rows), n=len(rows), eq=eq,
                wr=sum(1 for r in rows if r[0]>0)/len(rows)*100,
                stops=nstop, caps=ncap, filtered=nfilt, dead=False, rets=rets)
