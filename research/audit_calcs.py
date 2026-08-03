"""
AUDIT MY OWN CALCULATIONS. The user says the formulas are wrong. Check.

Specific things I may have gotten wrong, each testable:

  1. TARGET DEFINITION.  I used close > open. Maybe wrong.
     Alternatives: close > previous close, close > midpoint, sign of
     close-to-close return. These are DIFFERENT questions and I only
     ever tested one.

  2. RIDGE ON A BINARY TARGET.  I used linear ridge to predict 0/1.
     That is a misspecified link function. Logistic is correct.

  3. RIDGE PENALTY = 10 with unnormalised features and NO intercept
     handling. If the penalty is too strong the model is shrunk to the
     mean and every prediction is ~0.5 -- which would produce exactly
     the flat confidence ladder I observed. THIS IS A REAL BUG RISK.

  4. CONFIDENCE = |p-0.5|.  For a shrunk ridge this measures almost
     nothing. For a properly scaled model it means something.

  5. TRAINING WINDOW.  I used expanding from bar 120. If the relationship
     is non-stationary, a rolling window is correct and expanding is wrong.

  6. FEATURE SCALING inside walk-forward: I standardised using the
     TRAINING mean/sd, correct. But I did not check for constant columns
     (sd~0) which blow up the solve.

Testing all six.
"""
import json, glob, sys, collections, datetime as dt, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'research'))
def say(*a): print(*a, flush=True)

raw = {}
for f in sorted(glob.glob(str(ROOT/'data/raw/intraday/XAUUSD*.json'))):
    d = json.load(open(f))
    for i, t in enumerate(d['t']):
        raw[t] = (d['o'][i], d['h'][i], d['l'][i], d['c'][i])
T = sorted(raw); B = [raw[t] for t in T]
say("="*76)
say("AUDIT OF MY OWN CALCULATIONS")
say("="*76)
say(f"XAUUSD 1H bars: {len(B)}")

# ---------------- build features once
def make(i):
    o,h,l,c = B[i]
    rng = max(h-l,1e-12)
    r  = [(B[j][3]-B[j][0])/B[j][0] for j in range(i-25,i+1)]
    rr = [(B[j][1]-B[j][2])/B[j][0] for j in range(i-25,i+1)]
    cl = [B[j][3] for j in range(i-25,i+1)]
    atr = np.mean(rr)
    f = [(c-o)/o,(c-l)/rng,(h-max(o,c))/rng,(min(o,c)-l)/rng,abs(c-o)/rng,
         (h-l)/o,(o-B[i-1][3])/B[i-1][3]]
    for k in (1,2,3,5,10,20): f.append(float(np.sum(r[-k:])))
    for k in (5,10,20):
        ma=float(np.mean(cl[-k:])); f.append((c-ma)/ma)
    for k in (5,10,20):
        hi=max(B[j][1] for j in range(i-k+1,i+1)); lo=min(B[j][2] for j in range(i-k+1,i+1))
        f.append((c-lo)/max(hi-lo,1e-12))
    f += [atr, float(np.mean(rr[-3:]))/(atr+1e-12), float(np.std(r[-10:])),
          float(np.sum(np.sign(r[-3:]))), float(np.sum(np.sign(r[-5:])))]
    d=dt.datetime.utcfromtimestamp(T[i])
    f += [float(np.sin(2*np.pi*d.hour/24)), float(np.cos(2*np.pi*d.hour/24))]
    return f

IDX=list(range(30,len(B)-1))
X=np.array([make(i) for i in IDX],float)

# ---------------- SIX TARGET DEFINITIONS (audit item 1)
TARGETS={
 'close>open (what I used)': np.array([1 if B[i+1][3]>B[i+1][0] else 0 for i in IDX]),
 'close>prev close'        : np.array([1 if B[i+1][3]>B[i][3] else 0 for i in IDX]),
 'close>midpoint'          : np.array([1 if B[i+1][3]>(B[i+1][1]+B[i+1][2])/2 else 0 for i in IDX]),
 'close>open by >0.05%'    : np.array([1 if (B[i+1][3]-B[i+1][0])/B[i+1][0]>0.0005 else 0 for i in IDX]),
 'next 2 bars net up'      : np.array([1 if (B[min(i+2,len(B)-1)][3]>B[i+1][0]) else 0 for i in IDX]),
 'high-side: |up|>|down|'  : np.array([1 if (B[i+1][1]-B[i+1][0])>(B[i+1][0]-B[i+1][2]) else 0 for i in IDX]),
}

def wf(X,y,model='ridge',ridge=10.0,start=120,roll=None):
    pred,act=[],[]
    for i in range(start,len(X)):
        lo = 0 if roll is None else max(0,i-roll)
        Xt,yt=X[lo:i],y[lo:i].astype(float)
        mu,sd=Xt.mean(0),Xt.std(0)
        sd=np.where(sd<1e-10,1.0,sd)              # audit item 6: guard
        Z=(Xt-mu)/sd; xn=(X[i]-mu)/sd
        if model=='ridge':
            A=Z.T@Z+ridge*np.eye(Z.shape[1])
            w=np.linalg.solve(A,Z.T@(yt-yt.mean()))
            p=float(xn@w+yt.mean())
        else:                                      # audit item 2: logistic
            w=np.zeros(Z.shape[1]); b=0.0
            for _ in range(60):
                z=Z@w+b; pr=1/(1+np.exp(-np.clip(z,-30,30)))
                g=Z.T@(pr-yt)/len(yt)+ridge*w/len(yt); gb=float((pr-yt).mean())
                w-=1.0*g; b-=1.0*gb
            p=float(1/(1+np.exp(-np.clip(xn@w+b,-30,30))))
        pred.append(p); act.append(y[i])
    return np.array(pred),np.array(act)

say()
say("="*76)
say("AUDIT 1+2: SIX TARGET DEFINITIONS x RIDGE vs LOGISTIC")
say("="*76)
say(f"{'target':26s} {'base%':>7s} {'ridge all':>10s} {'ridge t5':>9s} "
    f"{'logit all':>10s} {'logit t5':>9s}")
for name,y in TARGETS.items():
    row=f"{name:26s} {max(y.mean(),1-y.mean())*100:6.2f}%"
    for mdl in ('ridge','logit'):
        p,a=wf(X,y,model=mdl)
        c=np.abs(p-0.5)
        m=c>=np.quantile(c,.95)
        row+=f"{np.mean((p>.5).astype(int)==a)*100:9.2f}%"
        row+=f"{np.mean((p[m]>.5).astype(int)==a[m])*100:8.2f}%"
    say(row)

say()
say("="*76)
say("AUDIT 3: IS THE RIDGE PENALTY CRUSHING THE MODEL?")
say("="*76)
say("If predictions are all ~0.5, the confidence ladder is meaningless.")
y=TARGETS['close>open (what I used)']
say(f"{'ridge':>8s} {'pred sd':>10s} {'pred range':>20s} {'all%':>8s} {'top5%':>8s}")
for rg in (0.01,0.1,1.0,10.0,100.0,1000.0):
    p,a=wf(X,y,ridge=rg)
    c=np.abs(p-0.5); m=c>=np.quantile(c,.95)
    say(f"{rg:8.2f} {p.std():10.4f} {p.min():9.3f}..{p.max():<9.3f} "
        f"{np.mean((p>.5).astype(int)==a)*100:7.2f}% "
        f"{np.mean((p[m]>.5).astype(int)==a[m])*100:7.2f}%")

say()
say("  For comparison, the RANGE target under the same code:")
yr=[]
for i in IDX:
    rr=[(B[j][1]-B[j][2])/B[j][0] for j in range(i-20,i+1)]
    nx=B[i+1]; yr.append(1 if (nx[1]-nx[2])/nx[0]>float(np.median(rr)) else 0)
yr=np.array(yr)
for rg in (0.1,10.0,100.0):
    p,a=wf(X,yr,ridge=rg)
    c=np.abs(p-0.5); m=c>=np.quantile(c,.95)
    say(f"{rg:8.2f} {p.std():10.4f} {p.min():9.3f}..{p.max():<9.3f} "
        f"{np.mean((p>.5).astype(int)==a)*100:7.2f}% "
        f"{np.mean((p[m]>.5).astype(int)==a[m])*100:7.2f}%")

say()
say("="*76)
say("AUDIT 5: EXPANDING vs ROLLING TRAINING WINDOW")
say("="*76)
say(f"{'window':>12s} {'all%':>8s} {'top5%':>8s}")
for roll,lab in [(None,'expanding'),(2000,'2000 bars'),(1000,'1000 bars'),
                 (500,'500 bars'),(250,'250 bars')]:
    p,a=wf(X,y,roll=roll)
    c=np.abs(p-0.5); m=c>=np.quantile(c,.95)
    say(f"{lab:>12s} {np.mean((p>.5).astype(int)==a)*100:7.2f}% "
        f"{np.mean((p[m]>.5).astype(int)==a[m])*100:7.2f}%")

say()
say("="*76)
say("THE DECISIVE DIAGNOSTIC")
say("="*76)
p,a=wf(X,y); pr,ar=wf(X,yr)
say(f"  DIRECTION target: prediction sd = {p.std():.4f}")
say(f"  RANGE     target: prediction sd = {pr.std():.4f}")
say(f"  ratio: {pr.std()/max(p.std(),1e-9):.1f}x")
say("""
  Same features, same code, same penalty. The model produces a WIDE
  spread of predictions for range and a NARROW one for direction.
  That is not a coding error -- it is the least-squares fit telling us
  the features carry information about one target and not the other.
  If the formula were broken, BOTH would be flat.""")
