"""THE REAL AGBA METTA STRUCTURE, applied to each currency.

Your model has THREE steps, in this order:
  STEP 1  SIGNAL       : real yield decides the regime -> the DIRECTION
                         yield > 0.7  = CONTRACTION -> SHORT
                         yield < -0.1 = EXPANSION   -> LONG
                         in between   = STABILITY   -> NO TRADE
  STEP 2  ALIGNMENT    : all assets must CONFIRM that direction
                         SHORT needs every asset close < open
                         LONG  needs every asset close > open
                         if they disagree -> NO TRADE
  STEP 3  EXECUTE      : enter at open, exit at close, 1% hard stop intraday

This asks: for each currency, when the regime says SHORT and that currency
CONFIRMS by closing down, does it keep going down the next bar?
"""
import json
import numpy as np

D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items():
        D.setdefault(dt,{}).update(row)
for f in __import__('glob').glob('data/raw/xpairs/*.json'):
    j=json.load(open(f))
    for i,dt in enumerate(j['dates']):
        D.setdefault(dt,{})[j['symbol']]={'open':j['o'][i],'close':j['c'][i]}

NAME={'gold':'XAUUSD','eur':'EURUSD','aud':'AUDUSD'}
for dt in D:
    for k,v in list(D[dt].items()):
        if k in NAME: D[dt][NAME[k]]=v

SYMS=['XAUUSD','XAGUSD','EURUSD','AUDUSD','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY','EURGBP']
CORE=('XAUUSD','EURUSD','AUDUSD')
dates=sorted(d for d in D if 'real_yield' in D[d] and all(s in D[d] for s in CORE))
print(f"dates with real yield + core 3: {len(dates)}  {dates[0]} -> {dates[-1]}")

# STEP 1 - regime from real yield
def regime(y):
    if y>0.7: return -1,'CONTRACTION(SHORT)'
    if y<-0.1: return +1,'EXPANSION(LONG)'
    return 0,'STABILITY(NO TRADE)'
regs=[regime(D[d]['real_yield'])[0] for d in dates]
import collections
cnt=collections.Counter(regs)
print(f"STEP 1 regime counts: SHORT={cnt[-1]}  LONG={cnt[1]}  NO-TRADE={cnt[0]}")
ys=[D[d]['real_yield'] for d in dates]
print(f"  real yield range {min(ys):.2f} .. {max(ys):.2f}  -> never below -0.1, so the model is ALWAYS SHORT\n")

def updown(d,s):
    b=D[d][s]; return np.sign(b['close']-b['open'])

print("="*94)
print("STEP 2+3: regime says SHORT. Currency CONFIRMS (closes down). Does it fall again NEXT day?")
print("="*94)
print(f"{'pair':>8} {'bars':>5} | {'CONFIRM days':>12} {'next-day DOWN':>14} {'accuracy':>9} | {'avg win':>8} {'avg loss':>9} {'edge/trade':>11}")
rows=[]
for s in SYMS:
    ok=[d for d in dates if s in D[d]]
    if len(ok)<40: continue
    idx={d:i for i,d in enumerate(ok)}
    conf=0; win=0; wins=[]; loss=[]
    for i in range(len(ok)-1):
        d,nd=ok[i],ok[i+1]
        if regime(D[d]['real_yield'])[0]!=-1: continue
        # STEP 2: this currency confirms the SHORT by closing DOWN
        if updown(d,s)>=0: continue
        conf+=1
        b=D[nd][s]; ret=(b['open']-b['close'])/b['open']   # SHORT next day open->close
        if ret>0: win+=1; wins.append(ret)
        else: loss.append(ret)
    if conf<20: continue
    acc=win/conf
    aw=np.mean(wins)*100 if wins else 0; al=np.mean(loss)*100 if loss else 0
    edge=(np.sum(wins)+np.sum(loss))/conf*100
    rows.append((s,len(ok),conf,win,acc,aw,al,edge))
    print(f"{s:>8} {len(ok):5d} | {conf:12d} {win:14d} {acc*100:8.2f}% | {aw:7.4f}% {al:8.4f}% {edge:+10.4f}%")

print("\n" + "="*94)
print("SAME, but requiring FULL AGBA ALIGNMENT (all 3 core assets confirm) before trading each pair")
print("="*94)
print(f"{'pair':>8} | {'aligned days':>12} {'next-day DOWN':>14} {'accuracy':>9} | {'avg win':>8} {'avg loss':>9} {'edge/trade':>11}")
for s in SYMS:
    ok=[d for d in dates if s in D[d]]
    if len(ok)<40: continue
    conf=0; win=0; wins=[]; loss=[]
    for i in range(len(ok)-1):
        d,nd=ok[i],ok[i+1]
        if regime(D[d]['real_yield'])[0]!=-1: continue
        if not all(updown(d,x)<0 for x in CORE): continue     # STEP 2 full alignment
        conf+=1
        b=D[nd][s]; ret=(b['open']-b['close'])/b['open']
        if ret>0: win+=1; wins.append(ret)
        else: loss.append(ret)
    if conf<20: continue
    acc=win/conf
    aw=np.mean(wins)*100 if wins else 0; al=np.mean(loss)*100 if loss else 0
    edge=(np.sum(wins)+np.sum(loss))/conf*100
    print(f"{s:>8} | {conf:12d} {win:14d} {acc*100:8.2f}% | {aw:7.4f}% {al:8.4f}% {edge:+10.4f}%")
