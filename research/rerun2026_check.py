"""Is the 2026 reversal real, or 42 lucky trades? Check against 2025 (unseen by this choice)."""
import json,math
import numpy as np
D={}
for f in ('data/market_data_spot2025.json','data/market_data_spot.json'):
    for dt,row in json.load(open(f)).items(): D.setdefault(dt,{}).update(row)
A=('gold','eur','aud')
def trades(yr):
    ds=sorted(d for d in D if d.startswith(yr) and all(a in D[d] for a in A) and 'real_yield' in D[d])
    out=[]
    for i in range(len(ds)-1):
        d,nd=ds[i],ds[i+1]
        if D[d]['real_yield']<=0.7: continue
        if not all(D[d][a]['close']<D[d][a]['open'] for a in A): continue
        legs=[(D[nd][a]['close']-D[nd][a]['open'])/D[nd][a]['open'] for a in A]  # LONG (reversed)
        out.append(np.mean(legs))
    return np.array(out)
t26=trades('2026'); t25=trades('2025')
for lab,t in (('2025',t25),('2026',t26),('BOTH',np.concatenate([t25,t26]))):
    wr=(t>0).mean()*100; mu=t.mean()*100
    tstat=t.mean()/(t.std()/np.sqrt(len(t)))
    p=2*(1-0.5*(1+math.erf(abs(tstat)/math.sqrt(2))))
    print(f"{lab}: n={len(t):3d}  reversed WR={wr:5.1f}%  mean={mu:+.4f}%/trade  t={tstat:+.2f}  p={p:.4f}")
print()
t=np.concatenate([t25,t26])
print("The reversal was DISCOVERED on 2025+2026 combined, so 2026 alone is not out-of-sample.")
print("2025 and 2026 agree in sign and magnitude, which is supportive but not independent proof.")
print()
# binomial CI on combined
k=(t>0).sum(); n=len(t); p_=k/n; z=1.96; den=1+z*z/n
c=(p_+z*z/(2*n))/den; h=z*math.sqrt(p_*(1-p_)/n+z*z/(4*n*n))/den
print(f"Combined reversed win rate {p_*100:.1f}%  95% CI [{(c-h)*100:.1f}, {(c+h)*100:.1f}]")
# payoff
w=t[t>0]; l=t[t<0]
print(f"avg win {w.mean()*100:+.4f}%   avg loss {l.mean()*100:+.4f}%   ratio {abs(w.mean()/l.mean()):.2f}")
be=abs(l.mean())/(w.mean()+abs(l.mean()))
print(f"break-even WR needed {be*100:.1f}%  vs actual {p_*100:.1f}%  -> margin {p_*100-be*100:+.1f} pts")
