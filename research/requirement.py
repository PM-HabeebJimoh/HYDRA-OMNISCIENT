"""Monte-Carlo the exact statistical quality a strategy must have to hit
   +700%/month with intramonth MaxDD < 5%. No model, pure requirement math."""
import numpy as np, math
rng=np.random.default_rng(0)
TARGET=math.log(8.0)   # +700%
DDCAP=math.log(1/0.95) # 5.13% log drawdown

def mdd_log(x):
    c=np.cumsum(x,axis=1); peak=np.maximum.accumulate(c,axis=1)
    return (peak-c).max(axis=1)

print(f"{'N/mo':>5} {'mu/trade':>10} {'max sigma':>10} {'per-tr SR':>10} {'ann SR':>8} {'P(DD<5%)':>9}")
for N in (10,20,40,100,200,400):
    mu=TARGET/N
    lo,hi=1e-5,0.5
    for _ in range(40):
        s=(lo+hi)/2
        x=rng.normal(mu,s,size=(4000,N))
        p=(mdd_log(x)<DDCAP).mean()
        if p<0.95: hi=s
        else: lo=s
    s=lo
    sr=mu/s
    print(f"{N:5d} {mu*100:9.3f}% {s*100:9.3f}% {sr:10.3f} {sr*math.sqrt(N*12):8.2f} {'95%':>9}")
print()
print("Interpretation: the goal is a SHARPE problem, not a leverage problem.")
print("Leverage scales mu and sigma TOGETHER -> per-trade Sharpe is leverage-invariant.")
print("No amount of leverage, capping, or position sizing changes the required Sharpe.")
print("The ONLY lever is signal quality (hit rate x payoff) and trade count.")
