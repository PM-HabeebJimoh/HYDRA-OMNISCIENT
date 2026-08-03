import sys,json,math,random,datetime
sys.path.insert(0,'scripts'); sys.path.insert(0,'/tmp')
from run_feb import run_month,lo_hi,tstat,bt_intraday
from agba_metta_live import load_daily,bt_live,mr,A,direction
from intraday_engine import load_1h,resample_4h
p1h=load_1h(); p4h=resample_4h(p1h); D=load_daily()

def ctl(panel,y,m,lev,cap,runs=200,seed=7):
    """random-direction control: same bars where alignment fires, coin-flip side."""
    ks=sorted(panel)
    lo=datetime.datetime(y,m,1,tzinfo=datetime.timezone.utc).timestamp()
    hi=datetime.datetime(y+(m==12),(m%12)+1,1,tzinfo=datetime.timezone.utc).timestamp()
    ev=[]
    for i in range(len(ks)-1):
        sk,ek=ks[i],ks[i+1]
        if not(lo<=ek<hi): continue
        s=panel[sk]
        dn=all(s[a]['close']<s[a]['open'] for a in A)
        up=all(s[a]['close']>s[a]['open'] for a in A)
        if dn or up: ev.append((ek,-1 if dn else 1))
    def sim(sides):
        eq=1e5
        for (ek,_),side in zip(ev,sides):
            e_=panel[ek]; pnl=0
            for a in A:
                b=e_[a]; en=b['open']
                if side<0:
                    st=en*1.01; ex=st if b['high']>=st else b['close']; r=(en-ex)/en
                else:
                    st=en*0.99; ex=st if b['low']<=st else b['close']; r=(ex-en)/en
                pnl+=r*(eq*.20/3*lev)
            if cap is not None and pnl<-cap*eq: pnl=-cap*eq
            eq+=pnl
            if eq<=0: return -100.
        return (eq/1e5-1)*100
    act=sim([s for _,s in ev])
    rng=random.Random(seed); outs=[]
    for _ in range(runs): outs.append(sim([rng.choice((-1,1)) for _ in ev]))
    outs.sort()
    return dict(n=len(ev),actual_ret=act,random_beats=sum(1 for o in outs if o>act),
                runs=runs,random_median=outs[runs//2])

MON=[(2026,2,'FEBRUARY2026'),(2026,3,'MARCH2026'),(2026,4,'APRIL2026'),(2026,5,'MAY2026'),(2026,6,'JUNE2026')]
res={}
for y,m,lab in MON:
    r=run_month(y,m,lab)
    r['random_direction_control']={
      '1H_V1_500x':ctl(p1h,y,m,500,None),'1H_V3_400x_cap2':ctl(p1h,y,m,400,.02),
      '4H_V1_500x':ctl(p4h,y,m,500,None),'4H_V3_400x_cap2':ctl(p4h,y,m,400,.02)}
    res[lab]=r

# pooled Feb->Jun
def pooled(panel,tag):
    ks=sorted(panel); lo=datetime.datetime(2026,2,1,tzinfo=datetime.timezone.utc).timestamp()
    hi=datetime.datetime(2026,7,1,tzinfo=datetime.timezone.utc).timestamp()
    eq1=1e5; eq3=1e5; peak1=eq1; peak3=eq3; dd1=0.; dd3=0.; rets=[]; ns=0; w=0; n=0
    for i in range(len(ks)-1):
        sk,ek=ks[i],ks[i+1]
        if not(lo<=ek<hi): continue
        s,e_=panel[sk],panel[ek]
        dn=all(s[a]['close']<s[a]['open'] for a in A); up=all(s[a]['close']>s[a]['open'] for a in A)
        if dn: side=-1
        elif up: side=1
        else: continue
        n+=1; p1=0.;p3=0.;tot=0.
        for a in A:
            b=e_[a]; en=b['open']
            if side<0:
                st=en*1.01; hit=b['high']>=st; ex=st if hit else b['close']; r=(en-ex)/en
            else:
                st=en*0.99; hit=b['low']<=st; ex=st if hit else b['close']; r=(ex-en)/en
            if hit: ns+=1
            p1+=r*(eq1*.20/3*500); p3+=r*(eq3*.20/3*400); tot+=r
        rets.append(tot/3*100)
        if p1>0: w+=1
        if p3<-.02*eq3: p3=-.02*eq3
        eq1=max(eq1+p1,0.); eq3+=p3
        peak1=max(peak1,eq1); peak3=max(peak3,eq3)
        if peak1>0: dd1=min(dd1,(eq1-peak1)/peak1*100)
        dd3=min(dd3,(eq3-peak3)/peak3*100)
    mn,tt=tstat(rets)
    return {'raw_edge_1x':{'n':n,'wr':w/n*100 if n else 0,'mean':mn,'t':tt},
            'V1_500x':{'ret':(eq1/1e5-1)*100,'dd':dd1,'n':n,'wr':w/n*100 if n else 0,'stops':ns},
            'V3_400x_cap2':{'ret':(eq3/1e5-1)*100,'dd':dd3,'n':n,'wr':w/n*100 if n else 0,'stops':ns}}
res['POOLED_FEB_TO_JUNE']={'4H':pooled(p4h,'4H'),'1H':pooled(p1h,'1H')}

# Bonferroni over 15 tests
def betacf(a,b,x):
    MAXIT,EPS,FPMIN=200,3e-16,1e-300
    qab,qap,qam=a+b,a+1.,a-1.; c=1.; dd=1.-qab*x/qap
    if abs(dd)<FPMIN: dd=FPMIN
    dd=1./dd; h=dd
    for mm in range(1,MAXIT+1):
        m2=2*mm
        aa=mm*(b-mm)*x/((qam+m2)*(a+m2)); dd=1.+aa*dd
        if abs(dd)<FPMIN: dd=FPMIN
        c=1.+aa/c
        if abs(c)<FPMIN: c=FPMIN
        dd=1./dd; h*=dd*c
        aa=-(a+mm)*(qab+mm)*x/((a+m2)*(qap+m2)); dd=1.+aa*dd
        if abs(dd)<FPMIN: dd=FPMIN
        c=1.+aa/c
        if abs(c)<FPMIN: c=FPMIN
        dd=1./dd; de=dd*c; h*=de
        if abs(de-1.)<EPS: break
    return h
def betai(a,b,x):
    if x<=0: return 0.
    if x>=1: return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log(1-x))
    return bt*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1.-bt*betacf(b,a,1-x)/b
def pv(t,df): return betai(df/2.,.5,df/(df+t*t)) if df>0 else 1.

short={'FEBRUARY2026':'Feb','MARCH2026':'Mar','APRIL2026':'Apr','MAY2026':'May','JUNE2026':'Jun'}
ts={};ps={}
for _,_,lab in MON:
    for tf in ('DAILY','4H','1H'):
        r=res[lab][tf]['raw_edge_1x']; L=f"{short[lab]} {'Daily' if tf=='DAILY' else tf}"
        ts[L]=round(r['t'],2); ps[L]=pv(r['t'],r['n']-1)
k=len(ts); alpha=.05/k; best=min(ps,key=lambda x:ps[x]); obs=sum(1 for v in ps.values() if v<.05)
res['multiple_testing']={'tests':k,'bonferroni_alpha':alpha,'t_stats':ts,
  'p_values':{a:round(b,6) for a,b in ps.items()},
  'smallest_p':{'test':best,'p':ps[best],'survives_bonferroni':ps[best]<alpha},
  'expected_p05_under_noise':round(.05*k,2),'observed_p05':obs,
  'note':('One p<0.05 out of 15 tests is what pure noise produces (expected 0.75). '
    'May 4H fails Bonferroni at alpha=0.003333 and does not persist: 4H t by month is '
    'Feb -0.56 -> Mar -0.47 -> Apr +0.33 -> May +2.13 -> Jun -1.02.')}
res['method']={
 'timing':'signal candle closes -> enter NEXT candle open -> 1% stop from actual entry -> exit that candle close unless stopped',
 'V1':'500x no cap','V3':'400x with -2% per-bar basket loss cap','risk':'20% equity split /3 per asset',
 'data':'100% Investing.com tvc4 endpoint; ALL February windows envelope_fixes=0; 4H resampled from real 1H (00/04/08/12/16/20 UTC)',
 'controls':'random-direction control: keep exact bars where 3-asset alignment fires, coin-flip side, 200 runs, seed 7',
 'validation':'engine re-verified by exactly reproducing the previously published March 2026 figures'}
json.dump(res,open('backtest_results/live_model/feb_to_june_2026_live_all_tf.json','w'),indent=1)

f=res['FEBRUARY2026']
print("FEB coverage",f['coverage'])
for tf in ('DAILY','4H','1H'):
    b=f[tf]; print(f"  {tf:5s} V1 {b['V1_500x']['ret']:14.2f}% dd {b['V1_500x']['dd']:8.2f}% | V3 {b['V3_400x_cap2']['ret']:14.2f}% dd {b['V3_400x_cap2']['dd']:7.2f}% | t={b['raw_edge_1x']['t']:+.2f}")
print("\nCONTROLS FEB:")
for kk,v in f['random_direction_control'].items(): print(f"  {kk:18s} act={v['actual_ret']:14.2f}% med={v['random_median']:14.2f}% beat={v['random_beats']}/200")
P=res['POOLED_FEB_TO_JUNE']
for tf in ('4H','1H'):
    r=P[tf]; print(f"\nPOOLED {tf}: n={r['raw_edge_1x']['n']} t={r['raw_edge_1x']['t']:+.2f} mean={r['raw_edge_1x']['mean']:+.4f}% | V1 {r['V1_500x']['ret']:.2f}% dd {r['V1_500x']['dd']:.2f}%")
mt=res['multiple_testing']
print(f"\n{k} tests alpha={alpha:.6f} smallest={best} p={ps[best]:.4f} survives={ps[best]<alpha} expected={.05*k:.2f} observed={obs}")
for a in ts: print(f"  {a:11s} t={ts[a]:+.2f} p={ps[a]:.4f}{' *' if ps[a]<.05 else ''}")
