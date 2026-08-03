import sys,datetime,json,math
sys.path.insert(0,'scripts')
from intraday_engine import load_1h, resample_4h
from agba_metta_live import load_daily, A
from agba_metta_v3 import run_v3

p1=load_1h(); p4=resample_4h(p1); D=load_daily()
# daily panel -> same dict-of-dict shape, keys sortable strings
dkeys=sorted(D)
dpanel={k:D[k] for k in dkeys if all(a in D[k] for a in A)}
dkeys=[k for k in dkeys if k in dpanel]
def dyield(sk):
    i=dkeys.index(sk)
    if i<1: return False
    return dpanel[sk].get('real_yield',0) >= dpanel[dkeys[i-1]].get('real_yield',0)

MON=[(2025,12,'Dec25'),(2026,1,'Jan26'),(2026,2,'Feb26'),(2026,3,'Mar26'),
     (2026,4,'Apr26'),(2026,5,'May26'),(2026,6,'Jun26')]
def bounds(y,m):
    lo=datetime.datetime(y,m,1,tzinfo=datetime.timezone.utc).timestamp()
    hi=datetime.datetime(y+(m==12),(m%12)+1,1,tzinfo=datetime.timezone.utc).timestamp()
    return lo,hi
def dbounds(y,m):
    import calendar
    return f"{y}-{m:02d}-01", f"{y}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}\uffff"

def tstat(x):
    n=len(x)
    if n<2: return 0.,0.
    mu=sum(x)/n; v=sum((q-mu)**2 for q in x)/(n-1); sd=math.sqrt(v) if v>0 else 0
    return mu,(mu/(sd/math.sqrt(n)) if sd>0 else 0.)

print("="*104)
print("V3 PROPER (7 enhancements, 400x base, -2% cap)   vs   V3 STUB (400x + cap only)")
print("="*104)
print(f"{'month':7s} {'TF':5s} {'STUB ret':>16s} {'V3 capped':>16s} {'V3 scaled':>16s} {'n stub':>7s} {'n V3':>6s} {'filt':>5s} {'caps':>5s} {'V3 dd':>9s}")
store={}
for y,m,lab in MON:
    for tf,keys,pan,isd in (('DAILY',dkeys,dpanel,True),('4H',sorted(p4),p4,False),('1H',sorted(p1),p1,False)):
        lo,hi = dbounds(y,m) if isd else bounds(y,m)
        yf = dyield if isd else None
        stub = run_v3(keys,pan,lo,hi,yields=yf,enh=False)
        vc   = run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="capped")
        vs   = run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="scaled")
        store[(lab,tf)]=(stub,vc,vs)
        print(f"{lab:7s} {tf:5s} {stub['ret']:15,.2f}% {vc['ret']:15,.2f}% {vs['ret']:15,.2f}% "
              f"{stub['n']:7d} {vc['n']:6d} {vc['filtered']:5d} {vc['caps']:5d} {vc['dd']:8.2f}%")
json.dump({f"{k[0]}_{k[1]}":{'stub':v[0]['ret'],'capped':v[1]['ret'],'scaled':v[2]['ret'],
           'n_stub':v[0]['n'],'n_v3':v[1]['n'],'filtered':v[1]['filtered'],'caps':v[1]['caps'],
           'dd':v[1]['dd'],'wr':v[1]['wr']} for k,v in store.items()},
          open('/tmp/v3res.json','w'),indent=1)

print()
print("RAW EDGE of the V3 TRADE SELECTION (1x, no leverage, no cap) — does filtering find better trades?")
print(f"{'month':7s} {'TF':5s} {'stub n':>7s} {'stub t':>8s} {'V3 n':>6s} {'V3 t':>8s}")
for y,m,lab in MON:
    for tf,keys,pan,isd in (('DAILY',dkeys,dpanel,True),('4H',sorted(p4),p4,False),('1H',sorted(p1),p1,False)):
        lo,hi = dbounds(y,m) if isd else bounds(y,m)
        yf = dyield if isd else None
        stub=run_v3(keys,pan,lo,hi,yields=yf,enh=False)
        vc  =run_v3(keys,pan,lo,hi,yields=yf,enh=True,ladder="capped")
        _,t0=tstat(stub['rets']); _,t1=tstat(vc['rets'])
        print(f"{lab:7s} {tf:5s} {len(stub['rets']):7d} {t0:+8.2f} {len(vc['rets']):6d} {t1:+8.2f}")
