# HYDRA-S3-MAX — Full Real Backtest, July 2026

**Branch:** `hydra-s3-max-actual-system`
**Period:** 2026-07-01 → 2026-07-27 (last completed session; today is 2026-07-28 and its session is still forming, so it is excluded)
**System:** actual config from `config.py` / `live_engine.py` — 1% hard stop, all-3 alignment filter, 20% of equity per trade day, 500x leverage, $100,000 start
**Data:** real market data only — no simulated, synthesised or hand-typed prices
**Execution:** every entry is priced off the real OHLC of its own entry candle, and the 1% hard stop is tested against that candle's intraday high before the close is used

---

## Headline

| | As published (July method) | Point-in-time (causally honest) |
|---|---|---|
| Final equity from $100,000 | **$280,545.86** | **$94,206.84** |
| Total return | **+180.55%** | **−5.79%** |
| Trade days | 4 of 18 sessions | 3 of 18 sessions |
| Day win rate | 100.00% (4W/0L) | 66.67% (2W/1L) |
| Asset win rate | 100.00% (12/12) | 66.67% (6/9) |
| Stop-loss hits | 0 of 12 | 1 of 9 |
| Profit factor | ∞ | 0.875 |
| Max drawdown | 0.00% | **−32.21%** |
| Sharpe | 6.21 | 0.48 |

Same system, same config, same real July data. The only difference is **when the entry decision is allowed to look at the market**.

---

## Weekly breakdown — point-in-time (the real result)

| Week | Dates | Sessions | Trade days | Trades | Stop-outs | Equity start | Equity end | Return | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| W27 | 07-01..07-02 | 2 | 0 | 0 | 0 | $100,000.00 | $100,000.00 | 0.00% | 0.00% |
| W28 | 07-06..07-10 | 5 | 0 | 0 | 0 | $100,000.00 | $100,000.00 | 0.00% | 0.00% |
| W29 | 07-13..07-17 | 5 | 2 | 6 | 1 | $100,000.00 | $94,024.85 | −5.98% | −32.21% |
| W30 | 07-20..07-24 | 5 | 1 | 3 | 0 | $94,024.85 | $94,206.84 | +0.19% | 0.00% |
| W31 | 07-27..07-27 | 1 | 0 | 0 | 0 | $94,206.84 | $94,206.84 | 0.00% | 0.00% |

### Equity walk

| Date | Equity open | Equity close | Day P&L |
|---|---|---|---|
| 2026-07-16 | $100,000.00 | $138,698.56 | **+$38,698.56** |
| 2026-07-17 | $138,698.56 | $94,024.85 | **−$44,673.70** |
| 2026-07-24 | $94,024.85 | $94,206.84 | +$181.99 |

July's whole outcome is two consecutive days. The month gains 38.7% on 07-16 and gives back more than all of it on 07-17.

## Weekly breakdown — as published (lookahead retained, for continuity)

| Week | Dates | Trade days | Trades | Stop-outs | Equity start | Equity end | Return | Max DD |
|---|---|---|---|---|---|---|---|---|
| W27 | 07-01..07-02 | 0 | 0 | 0 | $100,000.00 | $100,000.00 | 0.00% | 0.00% |
| W28 | 07-06..07-10 | 0 | 0 | 0 | $100,000.00 | $100,000.00 | 0.00% | 0.00% |
| W29 | 07-13..07-17 | 2 | 6 | 0 | $100,000.00 | $145,238.41 | +45.24% | 0.00% |
| W30 | 07-20..07-24 | 1 | 3 | 0 | $145,238.41 | $243,899.35 | +67.93% | 0.00% |
| W31 | 07-27..07-27 | 1 | 3 | 0 | $243,899.35 | $280,545.86 | +15.03% | 0.00% |

---

## The single trade that defines the month

**2026-07-17 XAUUSD** — real GC=F session: open 3,975.50, high 4,017.20, low 3,964.20, close 4,012.70

- stop = 3,975.50 × 1.01 = **4,015.255**
- session high 4,017.20 **≥** stop → filled at the stop, **−1.0000%**
- had it survived to the close it would have been −0.936%

At 33.3× equity notional, that single 1% stop cost **−33.3% of the account** — $46,232.85. The gold high exceeded the stop by **$1.95**, less than a tenth of a percent. That is the entire difference between July finishing up and finishing down.

This is why the `as_published` mode reports 0 stop hits and a 0.00% drawdown: on its lookahead entry dates the stop never happened to be touched. Move the entries to where they can honestly be taken and the very first week produces a −32.21% drawdown.

---

## Why the two modes pick different days

The published filter tests `close < open` on the **same candle** it enters at that candle's open and exits at that close. The return is then `(open − close)/open`, which is **positive whenever the filter passes**. All 12 trades win and profit is an identity, not a forecast.

Concretely, **2026-07-15**:

| Session | XAUUSD | EURUSD | AUDUSD |
|---|---|---|---|
| 07-14 (the signal day) | UP | UP | DOWN |
| 07-15 (the traded day) | DOWN | DOWN | DOWN |

`as_published` trades 07-15 because 07-15's *own* candle came out all-down — information not available at 07-15's open. Point-in-time reads 07-14, sees it was not aligned, and correctly stands aside.

Point-in-time also picks up **07-17**, which the lookahead mode skips: 07-16 was all-down so the signal was live, but 07-17 itself turned up and hit the stop. That is exactly the losing case the lookahead filter is structurally incapable of selecting.

---

## The branch's published July figures do not reconcile with the real feed

`backtest_actual_system_july2026.py` reports **+1,026.41%** ($1,126,407.83) from 4 trade days, 12/12 wins, 0 stop hits. Its hardcoded gold prices are labelled "Investing.com", but they do not match the COMEX `GC=F` record:

| Date | Script O/C | Real GC=F O/C | Direction |
|---|---|---|---|
| 2026-07-06 | 4165.17 / 4165.17 | 4175.40 / 4155.10 | UP vs **DOWN** |
| 2026-07-07 | 4166.99 / 4107.32 | 4126.50 / 4145.30 | DOWN vs **UP** |
| 2026-07-15 | 4051.70 / 4059.93 | 4049.10 / 4044.00 | UP vs **DOWN** |
| 2026-07-03 | 4175.70 / 4175.70 | *no session — US Independence Day holiday* | — |

Mean absolute close difference: **$13.54**. Several rows are flat (`open == close`), which no real session produces.

Checking the four days the script actually traded against real data:

| Script trade day | All three really down? |
|---|---|
| 2026-07-07 | **No** — gold UP, AUD UP |
| 2026-07-13 | **No** — EUR UP |
| 2026-07-16 | Yes |
| 2026-07-23 | Yes |

**Two of its four trade days did not qualify on real market data.** The published figure rests on inputs I could not verify against any live source.

Comparison:

| | Published on branch | As published, real data | Point-in-time, real data |
|---|---|---|---|
| Final equity | $1,126,408 | $280,546 | $94,207 |
| Total return | +1,026.41% | +180.55% | **−5.79%** |
| Stop hits | 0 | 0 | 1 |
| Max drawdown | 0.00% | 0.00% | **−32.21%** |

---

## Position sizing

From the real config: `20% risk × 500x leverage ÷ 3 assets`

- notional per asset = **33.3× account equity**
- total notional = **100× account equity**
- one asset hitting its 1% stop = **−33.3% of the entire account**
- all three stopping out = **−100%: total wipeout in a single session**

July never saw all three stop together. One did, and it erased a 38.7% gain in a day. Gold's median daily range in 2026 is **1.48%** and its high clears the open by ≥1% in **31.1%** of sessions, so the 1% stop sits *inside* gold's ordinary daily noise.

---

## Data provenance

| Series | Source | Detail |
|---|---|---|
| XAUUSD | Yahoo Finance v8 chart API, `GC=F` | COMEX gold futures, daily OHLC, America/New_York sessions |
| EURUSD | Yahoo Finance v8 chart API, `EURUSD=X` | spot, daily OHLC, Europe/London sessions |
| AUDUSD | Yahoo Finance v8 chart API, `AUDUSD=X` | spot, daily OHLC, Europe/London sessions |
| Real yield | FRED `DFII10` | 10y TIPS constant maturity; July range 2.24%–2.43% |

Raw payloads archived verbatim in `data/raw/*_2026-07.json`; `build_market_data.py` normalises them.

**18 sessions** in July have a real bar for all three assets and are evaluated. Handling notes:

- **2026-07-28 is excluded** — the FX feed returns a null close for it plus a partial intraday bar (stamped 16:49 BST), i.e. the session is still forming. Only completed sessions are used.
- **2026-07-03** has no gold session (US Independence Day observed). Not filled, not carried forward — skipped.
- Overlapping bars between the H1 and July pulls are de-duplicated, and the builder **fails loudly** if two independent pulls disagree on the same session. They did not.
- 2 July bars (07-15, 07-24 AUDUSD) had a vendor close a fraction of a pip outside the vendor high/low; the envelope was widened to contain the observed open/close. This is conservative for stop testing — it can only make a stop *more* likely to register.
- Where a candle both breaches the stop and closes profitably, the stop is assumed to trigger first.

DFII10 held 2.24%–2.43% all month, far above the 0.7% threshold, so **every July session was CONTRACTION** and the regime filter never gated a day. All selectivity came from the alignment filter.

---

## Verification performed

1. **Engine fidelity** — this engine reproduces the branch script's published result to the cent ($1,126,407.83 / +1,026.41% / 4 trade days / 12 wins / 0 stops) when replayed on that script's own hardcoded inputs, isolating the difference to data and timing rather than mechanics.
2. **Decisive trade re-derived by hand** — 07-17 XAUUSD: 3,975.50 × 1.01 = 4,015.255; high 4,017.20 ≥ stop → −1.0000%. Matches the engine.
3. **H1 regression** — the Jan–Jun run is byte-identical after the shared-engine refactor ($1,174,855.05 / $155.62), confirming the July work changed no existing result.
4. **Cross-source consistency** — de-duplication check passes: the H1 and July pulls agree exactly on every overlapping session.

---

## Conclusion

Re-run in full for July 2026 on real data, with every entry candle's OHLC and the hard stop honoured:

- **The +1,026% July claim does not survive real data.** Two of its four trade days do not qualify against the actual COMEX and FX record, and its hardcoded prices differ from the real feed by $13.54 on average with flat and non-existent sessions among them.
- **Removing only the lookahead turns +180.55% into −5.79%.** The filter reads the candle it trades, which makes profit arithmetically unavoidable; it can never select a day like 07-17 that opens aligned and then reverses.
- **The "0.00% drawdown" is an artefact of that same bias.** Point-in-time, July draws down **32.21%** in its first trading week.
- **One stop-out defines the month.** Gold's high exceeded the stop by $1.95, which at 33.3× notional cost a third of the account and wiped out a 38.7% gain in a single session.

The honest July 2026 result for this system on real data is **−5.79%**, with a −32.21% intra-month drawdown — not +1,026% with zero drawdown.
