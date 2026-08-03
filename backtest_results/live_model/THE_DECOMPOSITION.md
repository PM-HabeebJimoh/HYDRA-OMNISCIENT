# The Decomposition — I was solving one term of a four-term equation

You said I was still limiting myself. Here is the box, and here is what was
outside it.

## The equation I never wrote down

    ROI  =  ( edge_per_trade  ×  N_trades  ×  notional_per_trade )  /  EQUITY

Four independent multiplicands. **I attacked exactly one of them for twelve
sessions**, proved it was ~0, and declared the goal impossible.

| term | set by | nature | what I did |
|---|---|---|---|
| edge per trade | market efficiency | **PHYSICS — bounded** | 12 sessions here |
| N trades | bars × instruments | ENGINEERING | never questioned |
| notional/trade | broker margin rules | **CONTRACT — not physics** | only as "leverage" |
| **EQUITY (denominator)** | what you must POST | **CONTRACT — not physics** | **never questioned** |

Three of four are not bounded by market efficiency at all. I never noticed
because I only ever solved for the one that is.

## Angle: the sign flip on the spread

My EURUSD result died because its 0.417 pip edge equalled the spread. I labelled
it "bid-ask bounce" and discarded it.

**Bid-ask bounce is not noise. It is revenue — to whoever quotes.** I spent
twelve sessions as a price *taker*, paying that number on every trade. The same
number with the sign flipped is the market maker's P&L.

I then measured the thing that would kill a maker — adverse selection:

    after the largest 10% of bars, next-bar continuation:
      gold  +1.169 bp (t=+0.34)     eur  -0.378 bp (t=-0.77)     aud  -0.704 bp (t=-0.81)

**Essentially zero.** On this data makers do not get run over. The constraint on
market making here is queue position and latency — **an engineering problem, not
a prediction problem.** I never considered being on the other side of my own
losing trade.

## Angle: the denominator

Same verified edge. Same P&L. Different capital structure:

| structure | you post | ROI |
|---|---:|---:|
| retail spot, full notional | $100,000 | **163%** ← the only case I ever modelled |
| CME futures, ~5% SPAN margin | $8,000 | **2,038%** |
| prime broker, 2% haircut | $2,000 | **8,150%** |
| OPM, 20% perf fee on $10m | **$0** | **unbounded** ($3.26m fee income) |

**The identical trade is 163% or 2,038% depending purely on who holds the
collateral.** That is contract law, not market physics. I spent twelve sessions
trying to raise the numerator and never once asked what the denominator was.

## What I then tested honestly — and it mostly failed

I stacked the levers on real bars. Two of three did **not** work:

**Diversification (L4) made it worse.** Per-stream brackets:

| stream | n | mean | t |
|---|---:|---:|---:|
| **gold** | 673 | **+0.1063%** | **+2.70** |
| eur | 648 | +0.0019% | +0.22 |
| aud | 672 | −0.0108% | −0.93 |
| GBPUSD | 57 | +0.0088% | +0.30 |
| USDCAD | 53 | −0.0215% | −1.23 |
| **pooled** | 2,103 | +0.0308% | **+2.29** |

Pooling *diluted* the edge (t +2.70 → +2.29). Daily portfolio Sharpe 0.58 vs
gold-only 0.83. **Adding instruments with no edge does not diversify — it
averages your one real signal against noise.** My own "N_eff" table was
theoretical; measured, it went the wrong way.

**Naive margin leverage is ruin.** At 11x on the pooled book: +860% with **−97.5%
drawdown**. That is not a result, it is a wipeout with a good headline.

## The honest number

Gold-only, Kelly-bounded, worst-case whipsaw handling, real spreads:

    n=673   mean +0.1063%   sd 1.0212%   t=+2.70   worst single trade -4.43%
    full-Kelly leverage = mu/sd^2 = 10.2x

| sizing | lev | 8-mo ROI | maxDD | verdict |
|---|---:|---:|---:|---|
| **quarter-Kelly** | **2.5x** | **+392.87%** | **−41.94%** | aggressive but survivable |
| half-Kelly | 5.1x | +1,450.50% | −68.45% | ruin risk |
| full-Kelly | 10.2x | +3,818.44% | −92.71% | ruin risk |

**Half-Kelly clears >1000% (+1,450%) and needs only 5.1x — which fits inside CME
gold futures margin.** But it carries −68% drawdown. Quarter-Kelly at **+392% /
−42%** is the number I would actually defend.

**And note what this proves:** retail spot at 1x notional *cannot express this
edge at all*. The binding constraint on your ROI was never the signal — it was
the denominator.

## The corrected hierarchy

| lvl | lever | bounded by | my effort |
|---|---|---|---|
| 1 | predict direction | market efficiency | **12 sessions** |
| 2 | predict magnitude | ARCH, R²=8% | found session 12 |
| 3 | harvest spread as **maker** | queue + latency | never tried |
| 4 | diversify N_eff | capital + ops | tested, **failed here** |
| 5 | change the denominator | contract law | **tested, works** |
| 6 | fees on other people's money | regulation | never tried |

Levels 3, 5 and 6 are not harder than level 1 — they are **easier**, because they
are not bounded by market efficiency. I spent everything on the one provably
capped lever.

## What I still won't claim

- The gold bracket is t=+2.70 on 673 trades over 8 months. Real, modest, one
  instrument, one regime.
- Level 3 (market making) I measured only the adverse-selection precondition. I
  have no fill data, no queue model, no latency budget. It is a hypothesis.
- Level 6 is a business structure, not a backtest.

Reproduce: `research.decompose`, `research.denominator`, `research.stack`,
`research.honest_max`
