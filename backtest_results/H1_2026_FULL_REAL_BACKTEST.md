# HYDRA-S3-MAX — Full Real Backtest, January → June 2026

**Branch:** `hydra-s3-max-actual-system`
**System:** the actual configuration from `config.py` / `live_engine.py` — 1% hard stop, all-3 alignment filter, 20% of equity per trade day, 500x leverage, $100,000 start.
**Data:** real market data only. No simulated, synthesised or hand-typed prices.
**Execution:** every entry is priced off the real OHLC of its own entry candle, and the hard stop is checked against that candle's intraday high before the close is used.

---

## Headline

| | As published (July method) | Point-in-time (causally honest) |
|---|---|---|
| Final equity from $100,000 | **$1,174,855** | **$155.62** |
| Total return | **+1,074.86%** | **−99.84%** |
| Day win rate | 80.00% (16W/4L) | 30.00% (6W/14L) |
| Asset win rate | 91.67% (55/60) | 35.00% (21/60) |
| Stop-loss hits | 5 of 60 | 14 of 60 |
| Profit factor | 2.05 | 0.02 |
| Max drawdown | −53.65% | −99.84% |
| Sharpe | 3.04 | −4.52 |

Both columns run the **same system, same config, same real data, same 20 trade days**. The only difference is *when the entry decision is allowed to look at the market*. That single change moves the result from +1,075% to −99.8%.

---

## Why the two columns differ — the finding that matters

The July script on this branch decides whether to trade using this test:

```python
gold_down = gold["close"] < gold["open"]     # today's close
eur_down  = eur["close"]  < eur["open"]
aud_down  = aud["close"]  < aud["open"]
aligned   = gold_down and eur_down and aud_down
```

…and then enters that **same** candle at its open and exits at that **same** close.

The filter therefore requires `close < open`, and the trade is `SHORT` from `open` to `close`. Its return is `(open − close) / open`, which is **positive whenever the filter passes**. The trade cannot lose unless the 1% stop is touched intraday.

This is not a strategy result — it is an identity. Verified against the run itself:

- every one of the 55 non-stopped trades was profitable (100%, by construction)
- every single losing trade in that mode was a stop-out — there is no other loss path

The published July figure (+1,026.41%, 12/12 wins, 0 stop hits) is a direct consequence. **My engine reproduces that number to the cent — $1,126,407.83 — when replayed on the July script's own inputs**, which confirms the two runs differ only in data and timing, not in mechanics.

`point_in_time` fixes only the timing: the alignment signal is read from the **last completed session**, the regime from the **last real-yield print available before the open**, and the trade is entered at the **next** session's open. Nothing after the decision informs the decision. Everything else — the 1% stop, the leverage, the position sizing, the OHLC handling — is unchanged.

---

## Monthly breakdown — point-in-time (the real result)

| Month | Sessions | Trade days | Trades | Day wins | Stop-outs | Equity start | Equity end | Return | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 2026-01 | 18 | 2 | 6 | 0 | 1 | $100,000.00 | $57,984.09 | −42.02% | −42.02% |
| 2026-02 | 19 | 6 | 18 | 0 | 7 | $57,984.09 | $1,679.36 | **−97.10%** | −97.10% |
| 2026-03 | 21 | 5 | 15 | 3 | 3 | $1,679.36 | $490.91 | −70.77% | −70.77% |
| 2026-04 | 21 | 3 | 9 | 1 | 2 | $490.91 | $225.22 | −54.12% | −54.12% |
| 2026-05 | 20 | 3 | 9 | 2 | 0 | $225.22 | $233.15 | +3.52% | −4.39% |
| 2026-06 | 20 | 1 | 3 | 0 | 1 | $233.15 | $155.62 | −33.25% | −33.25% |

The account is effectively destroyed in February. Everything after that is a rounding artefact on a sub-$2,000 balance — the May "+3.52%" is $7.93.

## Monthly breakdown — as published (lookahead retained, for continuity)

| Month | Sessions | Trade days | Trades | Day wins | Stop-outs | Equity start | Equity end | Return | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 2026-01 | 18 | 3 | 9 | 2 | 1 | $100,000.00 | $94,294.19 | −5.71% | −31.93% |
| 2026-02 | 19 | 5 | 15 | 4 | 1 | $94,294.19 | $331,703.34 | +251.77% | −31.91% |
| 2026-03 | 21 | 5 | 15 | 5 | 1 | $331,703.34 | $842,866.29 | +154.10% | 0.00% |
| 2026-04 | 21 | 3 | 9 | 2 | 1 | $842,866.29 | $942,963.23 | +11.88% | −31.34% |
| 2026-05 | 20 | 3 | 9 | 3 | 0 | $942,963.23 | $1,676,159.99 | +77.75% | 0.00% |
| 2026-06 | 20 | 1 | 3 | 0 | 1 | $1,676,159.99 | $1,174,855.05 | −29.91% | −29.91% |

Even *with* the lookahead, H1 draws down 53.65% and loses 29.91% in June — the July run's "0.00% DD" does not survive a six-month window.

---

## The position sizing is the mechanical cause of ruin

From the real config: `20% risk × 500x leverage ÷ 3 assets`

- notional per asset = **33.3× account equity**
- total notional = **100× account equity**
- **one** asset hitting its 1% stop = **−33.3% of the entire account**
- all three stopping out = **−100%: total wipeout in a single session**

A 1% adverse move against the basket is a full account loss. On 2026-02-03 gold gapped from an open of 4,680.00 to a high of 4,984.60 (+6.5%) — the stop was blown through and the day cost 66.5% of remaining equity.

Gold is structurally incompatible with a 1% stop here: its median daily high-low range in H1 2026 was **1.48%**, and in **31.1%** of sessions the high alone exceeded the open by ≥1%. The stop sits *inside* the instrument's normal daily noise, so it is hit by routine volatility rather than by being wrong. Gold accounted for **11 of the 14** point-in-time stop-outs.

---

## Is it the leverage, or the signal?

The signal itself, before any leverage or stop is applied:

| Measure | Result |
|---|---|
| Point-in-time mean return per trade, **no stop**, open→close | **−0.2522%** |
| Same, with the 1% hard stop | **−0.2275%** |
| Lookahead version (for contrast) | +0.1830% |

The expectancy is **negative before leverage is involved**. Leverage only sets the speed of ruin. Notably, the stop slightly *improves* the result — the entries are simply on the wrong side.

A parameter sweep across stop (1/2/5%), risk (1/5/20%) and leverage (10/100/500x) produced **no profitable combination** — the best case, the most conservative setting tested (1% risk, 10x), still ends at $99,546. You cannot size your way out of a negative edge.

Direction check: gold did fall over H1 (−7.5% open-to-close), so an unconditional daily short in gold averaged **+0.19%/day**. The strategy's *timed* gold entries averaged **−0.76%**. The filter selected materially worse-than-random entry days.

---

## Data provenance

| Series | Source | Detail |
|---|---|---|
| XAUUSD | Yahoo Finance v8 chart API, `GC=F` | COMEX gold futures, daily OHLC, America/New_York sessions |
| EURUSD | Yahoo Finance v8 chart API, `EURUSD=X` | spot, daily OHLC |
| AUDUSD | Yahoo Finance v8 chart API, `AUDUSD=X` | spot, daily OHLC |
| Real yield | FRED `DFII10` | 10-year TIPS constant maturity, 127 real observations, 1.72%–2.29% |

Raw API payloads are archived verbatim in `data/raw/`; `build_market_data.py` normalises them into `data/ohlc_daily_2026H1.csv`.

**119 sessions** in Jan–Jun 2026 have a real bar for all three assets and are evaluated. Sessions where any asset lacked a real bar (US market holidays, the 2026-01-01 FX holiday) are skipped rather than filled — no gap-filling, no carry-forward, no invented prices.

Handling notes, disclosed in full:
- 4 flat/stale zero-range vendor bars dropped.
- 12 bars had a vendor close a fraction of a pip outside the vendor high/low (different vendor cut-offs for close vs. intraday aggregation). Their envelope was widened to contain the already-observed open/close. This is logged per bar by `build_market_data.py`. It is conservative for stop testing — it can only make a stop *more* likely to register, never less.
- Yahoo stamps daily bars at exchange-local midnight, so session dates are resolved with the real tz database (America/New_York for GC=F, Europe/London for the FX crosses). Using a fixed UTC offset mis-dates every bar once DST begins, which silently misaligns the three feeds.
- Where a candle both breaches the stop and closes profitably, the stop is assumed to trigger first — daily bars do not reveal the intraday path, so the conservative assumption is used.

The whole regime window is CONTRACTION (DFII10 stayed between 1.72% and 2.29%, far above the 0.7% threshold), so the regime filter never gated a single day in H1. All selectivity came from the alignment filter: 20 of 119 sessions.

---

## Verification performed

1. **Engine fidelity** — replaying this engine's logic on the July script's own hardcoded inputs reproduces its published result exactly: $1,126,407.83 / +1,026.41% / 4 trade days / 12 wins / 0 stop hits.
2. **Trade-level arithmetic** — hand-recomputed against raw OHLC. Example, 2026-01-05 XAUUSD: open 4,386.70, stop 4,386.70×1.01 = 4,430.567, session high 4,443.50 ≥ stop → filled at stop, −1.0000%. Engine agrees to 1e-9.
3. **Equity math** — 2026-01-05: notional/asset = 100,000×0.20×500/3 = $3,333,333; the three legs sum to −$32,427.34; equity $100,000 → $67,572.66. Matches the engine.
4. **Lookahead proof** — in `as_published`, all 55 non-stopped trades are winners and every loss is a stop-out, confirming profit-by-construction.
5. **No weekend bars**, no duplicate (date, asset) rows, no high < low after repair.

### Note on the July run's input data

The gold prices hardcoded in `backtest_actual_system_july2026.py` do not reconcile with the real `GC=F` feed for the days it traded. For example, on 2026-07-16 the script uses O 4,064.37 / C 3,976.28 (a −2.2% down candle that passes its filter), while the real session was O 4,030.50 / C 3,985.60. On 2026-07-07 the script has a down candle (4,166.99 → 4,107.32) where the real session was **up** (4,126.50 → 4,145.30) and would not have qualified at all. Those hardcoded values are labelled "Investing.com" in the file, but they do not match the COMEX record pulled here, so the July result rests on inputs I could not verify against a live source.

---

## Conclusion

Re-run in full across all six months on real data, with every entry candle's OHLC and the hard stop honoured:

- **The +1,000%-class result is an artefact of lookahead bias.** The filter reads the candle it trades, which makes profit arithmetically unavoidable. Removing only that — changing nothing else — turns +1,074.86% into −99.84%.
- **The system as configured is not survivable.** 33.3× equity of notional per asset means one 1% stop costs a third of the account and three cost all of it. February 2026 alone takes it down 97.10%.
- **The entry signal has negative expectancy** (−0.25%/trade unlevered), and no stop/risk/leverage combination tested makes it profitable. The problem is the signal, not the sizing.

The honest H1 2026 answer for this system on real data is a **−99.84% loss**, not a gain. I did not tune parameters to reach a target, because doing so on a negative-expectancy signal would only reproduce the original error in a new form.
