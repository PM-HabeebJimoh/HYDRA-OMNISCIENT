import sys,json,math,random,datetime
sys.path.insert(0,'scripts')
from agba_metta_live import load_daily,bt_live,mr,A,direction
from intraday_engine import load_1h,resample_4h

p1h=load_1h(); p4h=resample_4h(p1h); D=load_daily()

def month_keys(panel,y,m):
    ks=[]
    for ts in sorted(panel):
        d=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc)
        if d.year==y and d.month==m: ks.append(ts)
    return ks

def keys_with_prev(panel,y,m):
    """all keys sorted; month filter applied to ENTRY candle inside bt_live via start/end
       -> for intraday we pass the full sorted key list and filter by entry ts."""
    return sorted(panel)

def bt_intraday(panel,y,m,**kw):
    ks=sorted(panel)
    lo=datetime.datetime(y,m,1,tzinfo=datetime.timezone.utc).timestamp()
    hi=(datetime.datetime(y+(m==12),(m%12)+1,1,tzinfo=datetime.timezone.utc)).timestamp()
    # replicate bt_live but on intraday panel with entry-ts month filter
    eq=kw.get('eq0',1e5); lev=kw['lev']; cap=kw.get('cap'); risk=.20; stop=.01
    peak=eq; rows=[]; ns=0; rets=[]
    for i in range(len(ks)-1):
        sk,ek=ks[i],ks[i+1]
        if not(lo<=ek<hi): continue
        s,e_=panel[sk],panel[ek]
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        up=all(s[a]['close']>s[a]['open'] for a in A)
        if dn: side=-1
        elif up: side=1
        else: continue
        pnl=0; legrets=[]
        for a in A:
            b=e_[a]; entry=b['open']
            if side<0:
                st=entry*(1+stop); hit=b['high']>=st; ex=st if hit else b['close']; r=(entry-ex)/entry
            else:
                st=entry*(1-stop); hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-entry)/entry
            if hit: ns+=1
            pnl+=r*(eq*risk/3*lev); legrets.append(r)
        rets.append(sum(legrets)/3*100)
        if cap is not None and pnl<-cap*eq: pnl=-cap*eq
        eq+=pnl
        if eq<=0:
            return dict(ret=-100.,dd=-100.,n=len(rows)+1,eq=0.,wr=0.,stops=ns,dead=True,S=0,L=0),rets
        peak=max(peak,eq); rows.append((pnl,side,(eq-peak)/peak*100))
    if not rows: return dict(ret=0.,dd=0.,n=0,eq=eq,wr=0.,stops=0,dead=False,S=0,L=0),rets
    return dict(ret=(eq/1e5-1)*100,dd=min(r[2] for r in rows),n=len(rows),eq=eq,
                wr=sum(1 for r in rows if r[0]>0)/len(rows)*100,stops=ns,dead=False,
                S=sum(1 for r in rows if r[1]<0),L=sum(1 for r in rows if r[1]>0)),rets

def tstat(x):
    n=len(x)
    if n<2: return 0.,0.
    m=sum(x)/n; v=sum((q-m)**2 for q in x)/(n-1)
    sd=math.sqrt(v) if v>0 else 0.
    return m,(m/(sd/math.sqrt(n)) if sd>0 else 0.)

def daily_edge(y,m):
    ks=sorted(D)
    s,e=mr(y,m); rets=[]
    for i in range(len(ks)-1):
        sk,ek=ks[i],ks[i+1]
        if not(s<=ek<=e): continue
        S,E=D[sk],D[ek]
        if not all(a in S for a in A) or not all(a in E for a in A): continue
        dirs=[direction(S[a]) for a in A]
        if all(d=='DOWN' for d in dirs): side=-1
        elif all(d=='UP' for d in dirs): side=1
        else: continue
        tot=0
        for a in A:
            b=E[a]; en=b['open']
            if side<0:
                st=en*1.01; ex=st if b['high']>=st else b['close']; r=(en-ex)/en
            else:
                st=en*0.99; ex=st if b['low']<=st else b['close']; r=(ex-en)/en
            tot+=r
        rets.append(tot/3*100)
    return rets

def run_month(y,m,label):
    ks=sorted(D); s,e=mr(y,m)
    out={}
    n1=len([t for t in p1h if lo_hi(t,y,m)]); n4=len([t for t in p4h if lo_hi(t,y,m)])
    nd=len([k for k in D if s<=k<=e])
    out['coverage']={'1H_bars':n1,'4H_bars':n4,'daily_sessions':nd}
    d1=bt_live(D,ks,lev=500,start=s,end=e)
    d3=bt_live(D,ks,lev=400,cap=.02,start=s,end=e)
    de=daily_edge(y,m); mn,tt=tstat(de)
    out['DAILY']={'V1_500x':{k:d1[k] for k in ('ret','dd','n','eq','wr','stops','S','L','dead')},
                  'V3_400x_cap2':{k:d3[k] for k in ('ret','dd','n','eq','wr','stops','S','L','dead')},
                  'raw_edge_1x':{'n':len(de),'wr':(sum(1 for x in de if x>0)/len(de)*100 if de else 0),'mean':mn,'t':tt}}
    for tag,panel in (('4H',p4h),('1H',p1h)):
        v1,rets=bt_intraday(panel,y,m,lev=500)
        v3,_=bt_intraday(panel,y,m,lev=400,cap=.02)
        mn,tt=tstat(rets)
        out[tag]={'V1_500x':v1,'V3_400x_cap2':v3,
                  'raw_edge_1x':{'n':len(rets),'wr':(sum(1 for x in rets if x>0)/len(rets)*100 if rets else 0),'mean':mn,'t':tt}}
    return out

def lo_hi(ts,y,m):
    d=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc)
    return d.year==y and d.month==m

if __name__=='__main__':
    for (y,m,lab) in [(2026,2,'FEBRUARY2026'),(2026,3,'MARCH2026')]:
        r=run_month(y,m,lab)
        print(f"\n{lab}  1H={r['coverage']['1H_bars']} 4H={r['coverage']['4H_bars']} daily={r['coverage']['daily_sessions']}")
        for tf in ('DAILY','4H','1H'):
            b=r[tf]
            print(f"  {tf:5s} V1 n={b['V1_500x']['n']:4d} wr={b['V1_500x']['wr']:5.1f}% ret={b['V1_500x']['ret']:16.2f}% dd={b['V1_500x']['dd']:9.2f}% st={b['V1_500x']['stops']}")
            print(f"  {tf:5s} V3 n={b['V3_400x_cap2']['n']:4d} wr={b['V3_400x_cap2']['wr']:5.1f}% ret={b['V3_400x_cap2']['ret']:16.2f}% dd={b['V3_400x_cap2']['dd']:9.2f}%")
            print(f"        raw n={b['raw_edge_1x']['n']} wr={b['raw_edge_1x']['wr']:.1f}% mean={b['raw_edge_1x']['mean']:+.4f}% t={b['raw_edge_1x']['t']:+.2f}")
