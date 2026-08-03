"""
AUDIT R2: short-straddle / range-selling. WR 83-85%, t up to +9.72.

This is the ninth candidate. Eight died. The specific ways this one could
be fake, each tested:

  A. WR IS FREE. Selling options-like payoffs wins often and loses big.
     80%+ WR with negative expectancy is the classic signature. Must check
     the LOSS TAIL, not the win rate.
  B. My stop logic may be optimistic. If both stops are hit I charge
     -2*stop, but within a 4H bar I cannot know the order. Test a strictly
     worse assumption.
  C. Tail risk: what does the worst single bar do to a levered account?
  D. Is it just short-vol beta, i.e. does it die when vol rises?
  E. Does it survive out-of-sample in time, and a sign-flip null?
  F. Does the MODEL add anything over selling range on EVERY bar?
"""
import json, sys, glob, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'research'))
from intraday_engine import load_1h, resample_4h, A
from calendar_edge import build_events, tstat, signflip_null
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def say(*a): print(*a, flush=True)

p1h = load_1h(); p4 = resample_4h(p1h); b4 = sorted(p4); N = len(b4)
MAC = {}
for f in glob.glob(str(ROOT / 'data/raw/macro/*.json')):
    d = json.load(open(f))
    MAC[Path(f).stem] = {dt.date.fromisoformat(x): v
                         for x, v in zip(d['dates'], d['v']) if v is not None}
MKEYS = ('VIX','DXY','HYSPREAD','CURVE','GVZ','VIX3M')
MSORT = {k: sorted(MAC.get(k, {})) for k in MKEYS}
EV = build_events()
sched4 = collections.Counter(e['ts']-(e['ts']%14400) for e in EV)
SPREAD = {'gold':0.00012,'eur':0.000045,'aud':0.000075}

def macro_at(k,d,lag=1):
    cut,best = d-dt.timedelta(days=lag),None
    for x in MSORT[k]:
        if x<=cut: best=MAC[k][x]
        else: break
    return best

def series(a):
    out,pc=[],None
    for t in b4:
        x=p4[t][a]
        out.append((t,x['open'],x['high'],x['low'],x['close'],pc if pc else x['open']))
        pc=x['close']
    return out
S={a:series(a) for a in A}

def feats(a,i):
    q=S[a]; _,o,h,l,c,pc=q[i]; rng=max(h-l,1e-12)
    r=[(q[j][4]-q[j][1])/q[j][1] for j in range(i-20,i+1)]
    rr=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
    return [(c-o)/o,(c-l)/rng,(h-max(o,c))/rng,(min(o,c)-l)/rng,abs(c-o)/rng,
            (o-q[i-1][4])/q[i-1][4],rng/o,np.mean(r[-3:]),np.mean(r[-10:]),
            np.std(r[-10:]),np.mean(rr[-3:]),np.mean(rr[-5:]),np.mean(rr[-20:]),
            np.std(rr[-10:]),np.mean(rr[-3:])/(np.mean(rr[-20:])+1e-12),
            float(np.sum(np.sign(r[-5:]))),np.mean(np.abs(r[-5:]))]

def ctx(i):
    t=b4[i]; d=dt.datetime.utcfromtimestamp(t).date(); f=[]
    for k in MKEYS:
        v=macro_at(k,d); f.append(v if v is not None else 0.0)
    f+=[float(sched4.get(t,0)),float(sched4.get(t+14400,0)),
        float(dt.datetime.utcfromtimestamp(t).hour),
        float(dt.datetime.utcfromtimestamp(t).weekday())]
    return f

def fade(a, i, w_mult=1.0, stop_mult=2.0, pessimistic=False):
    """Sell range: fade the band, stop out beyond stop_mult."""
    q=S[a]
    hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
    w=float(np.mean(hist))*w_mult; stop=stop_mult*w
    _,o,h,l,c,_=q[i+1]; hs=SPREAD[a]
    up,dn=o*(1+w),o*(1-w); su,sd=o*(1+stop),o*(1-stop)
    hu,hd=h>=up,l<=dn; su_,sd_=h>=su,l<=sd
    if su_ and sd_:  return -2*stop-2*hs
    if su_ or sd_:
        # pessimistic: assume we also got faded on the other side first
        return (-stop-hs) if not pessimistic else (-stop-w-2*hs)
    if hu and hd:    return 2*w-2*hs
    if hu:           return (up-c)/o-hs
    if hd:           return (c-dn)/o-hs
    return 0.0

# build model predictions once
PRED={}
for a in A:
    X,Y=[],[]
    q=S[a]
    for i in range(60,N-1):
        X.append(feats(a,i)+ctx(i))
        nx=q[i+1]; hist=[(q[j][2]-q[j][3])/q[j][1] for j in range(i-20,i+1)]
        Y.append(int((nx[2]-nx[3])/nx[1] < float(np.median(hist))))
    X=np.array(X,float); Y=np.array(Y)
    pr,tr,idx=[],[],[]
    mdl=sc=None
    for k in range(150,len(X)):
        if (k-150)%10==0:
            if len(np.unique(Y[:k]))<2: continue
            sc=StandardScaler().fit(X[:k])
            mdl=RandomForestClassifier(n_estimators=100,max_depth=5,
                min_samples_leaf=20,random_state=0,n_jobs=-1).fit(sc.transform(X[:k]),Y[:k])
        if mdl is None: continue
        pr.append(float(mdl.predict_proba(sc.transform(X[k:k+1]))[0,1]))
        tr.append(Y[k]); idx.append(60+k)
    PRED[a]=(np.array(pr),np.array(tr),np.array(idx))

say("="*78); say("A. THE LOSS TAIL -- is the 84% WR paid for by the losses?"); say("="*78)
for a in A:
    pr,tr,idx=PRED[a]
    pnl=np.array([fade(a,i) for i in idx])
    w=pnl[pnl>0]; L=pnl[pnl<=0]
    m,t,n=tstat(list(pnl))
    say(f"  {a:5s} n={n} WR {len(w)/n*100:.1f}%  mean {m*100:+.4f}%  t={t:+.2f}")
    say(f"        avg win {w.mean()*100:+.4f}%   avg loss {L.mean()*100:+.4f}%   "
        f"ratio {abs(w.mean()/L.mean()):.3f}")
    say(f"        worst {pnl.min()*100:+.3f}%   5 worst "
        f"{', '.join(f'{x*100:+.2f}' for x in np.sort(pnl)[:5])}")
    say(f"        sum wins {w.sum()*100:+.2f}%  sum losses {L.sum()*100:+.2f}%  "
        f"net {pnl.sum()*100:+.2f}%")

say(); say("="*78); say("B. PESSIMISTIC STOP ACCOUNTING"); say("="*78)
for a in A:
    pr,tr,idx=PRED[a]
    for lab,pes in [('standard',False),('pessimistic',True)]:
        pnl=[fade(a,i,pessimistic=pes) for i in idx]
        m,t,n=tstat(pnl)
        say(f"  {a:5s} {lab:12s} mean {m*100:+.4f}%  t={t:+6.2f}  "
            f"WR {np.mean([x>0 for x in pnl])*100:.1f}%")

say(); say("="*78); say("C. STOP WIDTH SENSITIVITY (is 2x cherry-picked?)"); say("="*78)
for a in A:
    row=f"  {a:5s} "
    for sm in (1.5,2.0,3.0,5.0,99.0):
        pnl=[fade(a,i,stop_mult=sm) for i in PRED[a][2]]
        m,t,n=tstat(pnl)
        row+=f" stop{sm:>4.1f}:t={t:+5.2f}"
    say(row)

say(); say("="*78); say("D. IS IT JUST SHORT VOL? split by VIX regime"); say("="*78)
for a in A:
    pr,tr,idx=PRED[a]
    vix=[]
    for i in idx:
        d=dt.datetime.utcfromtimestamp(b4[i]).date()
        v=macro_at('VIX',d); vix.append(v if v else np.nan)
    vix=np.array(vix,float); pnl=np.array([fade(a,i) for i in idx])
    ok=~np.isnan(vix); med=np.nanmedian(vix)
    for lab,m_ in [('low VIX',ok&(vix<=med)),('high VIX',ok&(vix>med))]:
        mm,tt,nn=tstat(list(pnl[m_]))
        say(f"  {a:5s} {lab:9s} n={nn:4d} mean {mm*100:+.4f}%  t={tt:+5.2f}")

say(); say("="*78); say("E. SPLIT-HALF, MONTHLY, SIGN-FLIP NULL"); say("="*78)
for a in A:
    pr,tr,idx=PRED[a]
    pnl=np.array([fade(a,i) for i in idx]); h=len(pnl)//2
    m1,t1,_=tstat(list(pnl[:h])); m2,t2,_=tstat(list(pnl[h:]))
    say(f"  {a:5s} 1st half t={t1:+5.2f}  2nd half t={t2:+5.2f}  "
        f"sign-flip p={signflip_null(list(pnl)):.4f}")
    bym=collections.defaultdict(list)
    for k,i in enumerate(idx):
        bym[dt.datetime.utcfromtimestamp(b4[i]).strftime('%Y-%m')].append(pnl[k])
    pos=sum(1 for v in bym.values() if np.mean(v)>0)
    say(f"        months positive: {pos}/{len(bym)}  " +
        " ".join(f"{k[-2:]}:{np.mean(v)*100:+.3f}" for k,v in sorted(bym.items())))

say(); say("="*78); say("F. DOES THE MODEL ADD ANYTHING OVER FADING EVERY BAR?"); say("="*78)
for a in A:
    pr,tr,idx=PRED[a]
    pnl=np.array([fade(a,i) for i in idx])
    m_all,t_all,_=tstat(list(pnl))
    top=pr>=np.quantile(pr,.8)
    m_t,t_t,n_t=tstat(list(pnl[top]))
    say(f"  {a:5s} every bar: mean {m_all*100:+.4f}% t={t_all:+5.2f} n={len(pnl)}   "
        f"model top20%: mean {m_t*100:+.4f}% t={t_t:+5.2f} n={n_t}")

say(); say("="*78); say("G. MONEY: compounding, leverage, drawdown"); say("="*78)
byt=collections.defaultdict(list)
for a in A:
    for i in PRED[a][2]: byt[b4[i]].append(fade(a,i))
times=sorted(byt)
say(f"{'lev':>5s} {'WR%':>6s} {'median mo%':>11s} {'worst mo%':>10s} {'maxDD%':>8s} {'8mo%':>10s}")
for lev in (1,2,4,8,15):
    eq=1.0; peak=1.0; dd=0.0; curve={}; wins=0; tot=0
    for t in times:
        rs=byt[t]; eq*=(1+lev*np.mean(rs))
        wins+=sum(1 for r in rs if r>0); tot+=len(rs)
        peak=max(peak,eq); dd=max(dd,1-eq/peak)
        curve[dt.datetime.utcfromtimestamp(t).strftime('%Y-%m')]=eq
        if eq<=0: break
    mk=sorted(curve); mr=[]; prev=1.0
    for k in mk: mr.append(curve[k]/prev-1); prev=curve[k]
    say(f"{lev:5d} {wins/tot*100:6.1f} {np.median(mr)*100:+11.2f} "
        f"{min(mr)*100:+10.2f} {dd*100:8.2f} {(eq-1)*100:+10.2f}")
