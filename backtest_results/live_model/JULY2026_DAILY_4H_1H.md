# AGBA METTA MODEL — JULY 2026 — DAILY / 4H / 1H

## The timing fix

You were right: entering on the signal day is impossible in live trading. The
original engine records `entry_date == exit_date` — it reads day D's **close** to
confirm alignment, then enters at day D's **open**, a price that already passed.

Corrected timing used here:

```
bar i CLOSES  ->  alignment tested on bar i (close vs open)
              ->  ENTER at bar i+1 OPEN
              ->  1% hard stop from the ACTUAL entry price, checked on bar i+1 high/low
              ->  EXIT at bar i+1 CLOSE unless stopped
```

Both are shown side by side so the difference is measurable, not asserted.

## Results — July 2026

Universe XAUUSD / EURUSD / AUDUSD. Risk 20%, leverage 500x, hard stop 1%,
capital $100,000.

| TF | timing | bars | bar_WR | trade_days | asset_WR | stops | return | maxDD | final equity |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DAILY | SIGNAL-DAY | 4 | 100.0% | 4 | 100.0% | 0 | **+953.78%** | 0.00% | $1,053,775 |
| DAILY | **LIVE next-bar** | 4 | 25.0% | 4 | 33.3% | 2 | **-81.78%** | -82.82% | $18,220 |
| 4H | SIGNAL-DAY | 30 | 100.0% | 15 | 100.0% | 0 | **+82,144.71%** | 0.00% | $82,244,707 |
| 4H | **LIVE next-bar** | 31 | 61.3% | 16 | 55.9% | 1 | **+29.96%** | -68.36% | $129,963 |
| 1H | SIGNAL-DAY | 94 | 100.0% | 16 | 100.0% | 0 | **+5,128,203.35%** | 0.00% | $5,128,303,354 |
| 1H | **LIVE next-bar** | 95 | 60.0% | 16 | 56.8% | 2 | **-35.29%** | -79.03% | $64,714 |

## What the fix costs

| TF | signal-day | live next-bar | difference |
|---|---:|---:|---:|
| DAILY | +953.78% | -81.78% | **-1,035 points** |
| 4H | +82,144.71% | +29.96% | **-82,114 points** |
| 1H | +5,128,203.35% | -35.29% | **-5,128,238 points** |

The 5.1-million-percent 1H figure is entirely the timing error. Note also:

- **Win rate collapses from 100% to 25-61%.** Under signal-day entry the model
  only ever enters bars it has already seen close in its favour, so it cannot
  lose. That is why every signal-day run shows 100% WR and 0.00% drawdown.
- **Stops start firing.** Signal-day: 0 stops across all timeframes. Live: 2 on
  daily, 1 on 4H, 2 on 1H. Real entries get hit.
- **Drawdown appears.** 0.00% becomes -68% to -83%.

Example, daily, 2026-07-13 -> 07-14: XAUUSD entered at 4001.24, stopped at
4041.25 for -1.000% (-$35,345); AUDUSD entered 0.69200, stopped 0.69892, also
-1.000% (-$35,345). Both legs stopped on the same bar. Under signal-day entry
that day was recorded as a winner.

## Only 4H survives, and barely

4H live is the single positive result: **+29.96%**, bar win rate 61.3%. But
maxDD is **-68.36%**, far outside any usable risk limit. Daily and 1H both lose
money live.

## Answering the 4H / 1H question for the swap baskets

I could not run 4H or 1H for AUDUSD+GBPUSD+USDCAD, EURUSD+AUDUSD+USDCAD,
GBPUSD+NZDUSD+USDCAD or NZDUSD+USDCAD+USDJPY.

`data/raw/intraday/` contains **only XAUUSD, EURUSD and AUDUSD**. There are no
1H or 4H bars for GBPUSD, NZDUSD, USDCAD, USDJPY, USDCHF, XAGUSD or EURGBP
anywhere in this repo — those pairs exist only as daily open/close in
`data/raw/xpairs/`, with no high/low. Intraday backtests of the swap baskets are
not possible without fetching that data first.

## Data note

July 1H coverage per symbol: XAUUSD runs to 07-30, but EURUSD and AUDUSD stop at
07-27 (provider gap, previously documented). The intraday panel keeps only
timestamps where all three assets exist, so July 1H/4H effectively ends 07-27.
Daily is unaffected.

## Bottom line

With live-correct timing, in July 2026 the Agba Metta model returns **-81.78%
daily, +29.96% on 4H, -35.29% on 1H** — against +953.78% / +82,144.71% /
+5,128,203.35% under the original same-bar entry. The published performance is a
timing artifact, not an edge.

Full trade logs: `backtest_results/live_model/july2026_daily_4h_1h.json`
Reproduce: `python3 -m research.july2026_live_tf`
