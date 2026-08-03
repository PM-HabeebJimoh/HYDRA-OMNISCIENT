import sys,datetime,math,random,json
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
from agba_metta_live import load_daily, A
from agba_metta_v3 import run_v3
p1=load_1h(); p4=resample_4h(p1); D=load_daily()
dkeys=[k for k in sorted(D) if all(a in D[k] for a in A)]
dpanel={k:D[k] for k in dkeys}
def dyield(sk):
    i=dkeys.index(sk)
    return i>=1 and dpanel[sk].get('real_yield',0)>=dpanel[dkeys[i-1]].get('real_yield',0)
def tstat(x):
    n=len(x)
    if n<2: return 0.,0.
    mu=sum(x)/n; v=sum((q-mu)**2 for q in x)/(n-1); sd=math.sqrt(v) if v>0 else 0
    return mu,(mu/(sd/math.sqrt(n)) if sd>0 else 0.)
def betacf(a,b,x):
    M,E,F=200,3e-16,1e-300; qab,qap,qam=a+b,a+1.,a-1.; c=1.; d=1.-qab*x/qap
    d=F if abs(d)<F else d; d=1./d; h=d
    for m in range(1,M+1):
        m2=2*m; aa=m*(b-m)*x/((qam+m2)*(a+m2)); d=1.+aa*d
        d=F if abs(d)<F else d; c=1.+aa/c; c=F if abs(c)<F else c; d=1./d; h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2)); d=1.+aa*d
        d=F if abs(d)<F else d; c=1.+aa/c; c=F if abs(c)<F else c; d=1./d; de=d*c; h*=de
        if abs(de-1.)<E: break
    return h
def betai(a,b,x):
    if x<=0: return 0.
    if x>=1: return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log(1-x))
    return bt*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1.-bt*betacf(b,a,1-x)/b
def pv(t,df): return betai(df/2.,.5,df/(df+t*t)) if df>0 else 1.

MON=[(2025,12,'Dec'),(2026,1,'Jan'),(2026,2,'Feb'),(2026,3,'Mar'),(2026,4,'Apr'),(2026,5,'May'),(2026,6,'Jun')]
import calendar
def bnd(y,m,isd):
    if isd: return f"{y}-{m:02d}-01", f"{y}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}\uffff"
    lo=datetime.datetime(y,m,1,tzinfo=datetime.timezone.utc).timestamp()
    hi=datetime.datetime(y+(m==12),(m%12)+1,1,tzinfo=datetime.timezone.utc).timestamp()
    return lo,hi
TFS=[('DAILY',dkeys,dpanel,True,dyield),('4H',sorted(p4),p4,False,None),('1H',sorted(p1),p1,False,None)]

# POOLED: continuous equity across all 7 months
print("POOLED Dec2025->Jun2026, V3 PROPER (7 enhancements, 400x, -2% cap)")
print(f"{'TF':6s} {'n':>5s} {'WR':>7s} {'return':>16s} {'maxDD':>9s} {'raw t':>7s} {'caps':>5s} {'filtered':>9s}")
pooled={}
for tf,keys,pan,isd,yf in TFS:
    lo=bnd(2025,12,isd)[0]; hi=bnd(2026,6,isd)[1]
    r=run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="capped")
    mu,t=tstat(r['rets']); pooled[tf]=(r,t)
    print(f"{tf:6s} {r['n']:5d} {r['wr']:6.1f}% {r['ret']:15,.2f}% {r['dd']:8.2f}% {t:+7.2f} {r['caps']:5d} {r['filtered']:9d}")

# 21-test Bonferroni on V3 selection
print("\n21-test Bonferroni on V3's OWN trade selection (raw 1x edge)")
ts={};ps={}
for y,m,sh in MON:
    for tf,keys,pan,isd,yf in TFS:
        lo,hi=bnd(y,m,isd)
        r=run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="capped")
        mu,t=tstat(r['rets']); lb=f"{sh} {'Daily' if tf=='DAILY' else tf}"
        ts[lb]=round(t,2); ps[lb]=pv(t,len(r['rets'])-1)
k=len(ts);al=.05/k;best=min(ps,key=lambda x:ps[x]);obs=sum(1 for v in ps.values() if v<.05)
for a in ts: print(f"  {a:10s} t={ts[a]:+.2f} p={ps[a]:.4f}{' *' if ps[a]<.05 else ''}")
print(f"\nalpha={al:.6f}  smallest={best} p={ps[best]:.4f} survives={ps[best]<al}  expected={0.05*k:.2f} observed={obs}")

# control: coin-flip direction on V3's OWN selected bars, keeping all enhancements
print("\nRANDOM-DIRECTION CONTROL on V3 proper (200 runs, seed 7)")
def ctl(keys,pan,lo,hi,yf,runs=200,seed=7):
    import copy
    base=run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="capped")
    act=base['ret']
    # flip by inverting the panel's close/open relationship is invasive; instead
    # re-run with randomized side by monkeypatching direction via wrapper
    rng=random.Random(seed); outs=[]
    for _ in range(runs):
        eq=1e5; cool=False; ms=eq
        # replicate run_v3 loop with random side
        from agba_metta_v3 import atr_pct, grade, MIN_BASKET_STRENGTH, ATR_HIGH, ATR_LOW, W_HIGH, W_NORM, W_LOW, WICK_DANGER, COOLDOWN_MULT, PROFIT_LOCK_TRIGGER, PROFIT_LOCK_RISK
        for i in range(len(keys)-1):
            sk,ek=keys[i],keys[i+1]
            if not(lo<=ek<hi): continue
            s,e_=pan[sk],pan[ek]
            dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
            if not(dn or up): continue
            strength=sum(abs(s[a]['close']-s[a]['open'])/s[a]['open'] for a in A)/3
            if strength<MIN_BASKET_STRENGTH: continue
            side=rng.choice((-1,1))
            xa=atr_pct(keys,pan,i,'gold')
            w=dict(W_HIGH) if (xa is None or xa>=ATR_HIGH) else (dict(W_LOW) if xa<=ATR_LOW else dict(W_NORM))
            g0=s['gold']
            wick=((g0['high']-max(g0['open'],g0['close']))/g0['open']) if side<0 else ((min(g0['open'],g0['close'])-g0['low'])/g0['open'])
            if wick>WICK_DANGER:
                fr=w['gold']*.5; w['gold']-=fr; w['eur']+=fr/2; w['aud']+=fr/2
            yr=yf(sk) if yf else False
            g,lev=grade(strength,xa,yr,"capped")
            if cool: lev*=COOLDOWN_MULT
            risk=PROFIT_LOCK_RISK if (eq/ms-1)>=PROFIT_LOCK_TRIGGER else 0.20
            pnl=0.;st_=False
            for a in A:
                b=e_[a];en=b['open'];nt=eq*risk*w[a]*lev
                if side<0:
                    sp=en*1.01;hit=b['high']>=sp;ex=sp if hit else b['close'];r=(en-ex)/en
                else:
                    sp=en*0.99;hit=b['low']<=sp;ex=sp if hit else b['close'];r=(ex-en)/en
                if hit: st_=True
                pnl+=r*nt
            if pnl<-0.02*eq: pnl=-0.02*eq
            eq+=pnl; cool=st_
            if eq<=0: eq=0; break
        outs.append((eq/1e5-1)*100)
    outs.sort()
    return act,outs[runs//2],sum(1 for o in outs if o>act)
for tf,keys,pan,isd,yf in TFS:
    lo=bnd(2025,12,isd)[0]; hi=bnd(2026,6,isd)[1]
    a_,md,beat=ctl(keys,pan,lo,hi,yf)
    print(f"  POOLED {tf:5s} actual {a_:14,.2f}%   coinflip median {md:14,.2f}%   flip beats {beat}/200")
