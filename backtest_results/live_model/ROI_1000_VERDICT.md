# Correction: the +1,456.66% is not an edge

I reported EURUSD 1H fade at **+1,456.66%**, passing a selection-noise null
(p=0.042), and framed it as real-but-cost-sensitive. I then interrogated it
properly. **It is a microstructure artifact.** I am withdrawing it.

## What tipped me off

Break-even cost came out at **0.417 pips** and the measured edge was **0.417
pips** — identical to three decimals. An edge that exactly equals the spread is
usually *made of* the spread.

## Test 1 — does the edge persist beyond one bar?

| entry | mean | t |
|---|---:|---:|
| bar i+1 open → close (the trade) | **+0.4208 pips** | +2.36 |
| bar i+2 open → close | +0.1957 pips | +1.14 |
| bar i+3 open → close | +0.1378 pips | +0.74 |

Decays to nothing within two bars. Genuine reversion after a 3-asset capitulation
would persist; a one-bar bounce would not.

## Test 2 — the decisive one: edge vs size of the triggering move

| triggering move | n | gross | t |
|---|---:|---:|---:|
| **smallest 25%** | 459 | **+0.6667 pips** | +2.25 |
| 25–50% | 459 | +0.8308 pips | +2.34 |
| 50–75% | 459 | +0.2208 pips | +0.64 |
| **largest 25%** | 459 | **−0.0546 pips** | −0.13 |

**This is backwards.** Real mean-reversion after a capitulation gets *stronger*
when the move is bigger. Here the entire effect sits in the **smallest** moves
and is **zero or negative** in the largest. That is the textbook signature of
**bid-ask bounce** — price ticking between bid and offer on quiet bars — not of
tradeable reversion.

## Test 3 — apply cost where the edge actually lives

At 0.2 pip round trip (tight ECN):

| bucket | net pips | t(net) |
|---|---:|---:|
| smallest 25% | +0.4667 | +1.57 |
| 25–50% | +0.6308 | +1.78 |
| 50–75% | +0.0208 | +0.06 |
| largest 25% | −0.2546 | −0.62 |
| **ALL** | **+0.2159** | **+1.21** |

Net t = **+1.21**. Not significant. The +2.34 gross t-stat was measuring the
bounce, and cost removes it.

## Why the noise null passed anyway

My sign-flip null preserved each bar's magnitude and only randomised direction.
Bid-ask bounce is a property of *magnitudes on quiet bars*, so it survived the
flip and inflated the null's own baseline. **The test was blind to this failure
mode.** A p-value only rules out the specific alternative the null encodes.

## Scale check

Mean absolute EURUSD 1H move: **5.19 pips**. Extracted "edge": **0.421 pips** —
sub-pip residue on a 5-pip bar, the same order as the tick grid and the spread.
It cannot be separated from execution noise on hourly OHLC data.

## Corrected verdict on ROI > 1000%

| claim | status |
|---|---|
| Basket, 864 configs | 0 above 1000% — stands |
| Basket, 259,200 configs | 0 above 1000%, best +897.24% — stands |
| Compounding ceiling is arithmetic | stands |
| **EURUSD 1H +1,456.66%** | **withdrawn — bid-ask bounce** |

**ROI > 1000% has not been achieved on this data under live-correct timing with
realistic execution.** The one config that cleared it was measuring spread, not
a market edge.

## What I should have done first

Before reporting any high-frequency result I should have checked whether the edge
scales with move size. It costs one query and it is the difference between a real
signal and a bounce. I ran it only after the break-even/edge coincidence forced
the question — that ordering was the mistake.

Reproduce: `research.microstructure`, `research.bounce_verdict`
