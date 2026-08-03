# AGBA METTA MODEL — July 2026 — all baskets, real OHLC, stop active

## Data gathered

The four swap pairs previously had **open/close only**, so the model's 1% hard
stop could not be evaluated. I fetched real daily OHLC from Investing.com
(`tvc4` endpoint, `resolution=D`) for all four:

| pair | pair_id | bars | range | envelope_fixes |
|---|---:|---:|---|---:|
| GBPUSD | 2 | 30 | 2026-06-22 → 2026-07-31 | **0** |
| NZDUSD | 8 | 30 | 2026-06-22 → 2026-07-31 | **0** |
| USDCAD | 7 | 30 | 2026-06-22 → 2026-07-31 | **0** |
| USDJPY | 3 | 30 | 2026-06-22 → 2026-07-31 | **0** |

Cross-checked open/close against the existing `xpairs` feed: **107 of 108
overlapping values match exactly.** The one difference is NZDUSD 2026-07-28
close (0.5787 new vs 0.5781 old, 0.1%). Saved to `data/raw/xpairs_ohlc/`.

**Still not available: 1H/4H for these pairs.** The intraday endpoint returns
hourly bars, but building verified 1H panels for 4 pairs requires the
window-by-window transcription pipeline used for the core 3 (~40 fetches per
pair-month). Not done here. Intraday remains XAU/EUR/AUD only.

## Results — July 2026, all five baskets

| universe | timing | days | asset_WR | stops | return | maxDD | final equity |
|---|---|---:|---:|---:|---:|---:|---:|
| XAUUSD+EURUSD+AUDUSD | SIGNAL-DAY | 5 | 100.0% | 0 | **+1,415.07%** | 0.00% | $1,515,075 |
| XAUUSD+EURUSD+AUDUSD | **LIVE** | 5 | 40.0% | 3 | **−72.32%** | −84.36% | $27,682 |
| AUDUSD+GBPUSD+USDCAD | SIGNAL-DAY | 4 | 100.0% | 0 | +131.81% | 0.00% | $231,809 |
| AUDUSD+GBPUSD+USDCAD | **LIVE** | 4 | 25.0% | 1 | **−46.73%** | −46.73% | $53,267 |
| EURUSD+AUDUSD+USDCAD | SIGNAL-DAY | 4 | 100.0% | 0 | +108.59% | 0.00% | $208,594 |
| EURUSD+AUDUSD+USDCAD | **LIVE** | 4 | 33.3% | 1 | **−38.54%** | −41.03% | $61,461 |
| GBPUSD+NZDUSD+USDCAD | SIGNAL-DAY | 3 | 100.0% | 0 | +104.70% | 0.00% | $204,704 |
| GBPUSD+NZDUSD+USDCAD | **LIVE** | 3 | 22.2% | 1 | **−43.56%** | −43.56% | $56,438 |
| NZDUSD+USDCAD+USDJPY | SIGNAL-DAY | 1 | 100.0% | 0 | +15.05% | 0.00% | $115,048 |
| NZDUSD+USDCAD+USDJPY | **LIVE** | 1 | 66.7% | 0 | **+14.06%** | 0.00% | $114,058 |

## What the real data changed

Adding true high/low **activated stops that were previously invisible**:

- AUDUSD+GBPUSD+USDCAD: 1 stop. AUDUSD 07-14 entered 0.69180, stopped 0.69872,
  −1.000%, **−$32,467**.
- GBPUSD+NZDUSD+USDCAD: 1 stop. NZDUSD 07-14 entered 0.57560, stopped 0.58136,
  −1.000%, **−$28,519**.
- EURUSD+AUDUSD+USDCAD: 1 stop, AUDUSD 07-14, **−$34,740**.

The earlier open→close run reported these baskets at +157.75% / +104.70% /
+108.59% with **zero stops and 0.00% drawdown**. With real high/low they lose
**−46.73% / −43.56% / −38.54%**. The missing high/low was hiding every stop-out.

## Every basket fails live

**Four of five lose money** under live-correct timing. Only
NZDUSD+USDCAD+USDJPY is positive at **+14.06%** — on a **single trade day**,
which is not evidence of anything.

The original XAU/EUR/AUD basket is the **worst** performer live (−72.32%,
maxDD −84.36%) precisely because gold's large range that made
signal-day returns look spectacular (+1,415.07%) cuts equally hard in the real
direction. Three of its nine legs stopped out.

## The pattern across all five

| basket | signal-day | live | swing |
|---|---:|---:|---:|
| XAUUSD+EURUSD+AUDUSD | +1,415.07% | −72.32% | −1,487 pts |
| AUDUSD+GBPUSD+USDCAD | +131.81% | −46.73% | −179 pts |
| EURUSD+AUDUSD+USDCAD | +108.59% | −38.54% | −147 pts |
| GBPUSD+NZDUSD+USDCAD | +104.70% | −43.56% | −148 pts |
| NZDUSD+USDCAD+USDJPY | +15.05% | +14.06% | −1 pt |

Every signal-day column shows **100% asset win rate, 0 stops, 0.00% drawdown** —
the signature of entering bars already known to have closed favourably. No
basket substitution fixes this, because it is a timing property, not a
universe property.

Full trade logs: `backtest_results/live_model/july2026_swap_ohlc.json`
Data: `data/raw/xpairs_ohlc/{GBPUSD,NZDUSD,USDCAD,USDJPY}_2026jul.json`
Reproduce: `python3 -m research.july2026_swap_ohlc`
