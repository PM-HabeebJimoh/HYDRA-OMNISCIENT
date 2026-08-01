# The Real Agba Metta Model

Read directly from the author's committed code at `cebb21c` — not my variants,
not V3, not Omega. This is what the model actually is.

## The universe — fixed, 3 assets

```
XAUUSD  (Gold,   contract 100)
EURUSD  (Euro,   contract 100,000)
AUDUSD  (Aussie, contract 100,000)
```

## The logic — three gates in strict order

**GATE 1 — REGIME (from FRED DFII10, 10Y TIPS real yield)**

```
real yield >  0.7%  ->  CONTRACTION  ->  SHORT
real yield < -0.1%  ->  EXPANSION    ->  LONG
in between          ->  STABILITY    ->  NO TRADE
```

**GATE 2 — ALIGNMENT (the "Agba" logic)**

```
CONTRACTION: ALL THREE must close < open   -> confirm SHORT
EXPANSION:   ALL THREE must close > open   -> confirm LONG
mixed                                      -> NO TRADE that day
```

**GATE 3 — SIZING (the "Metta" logic)**

```
risk_per_trade_pct  0.20     20% of equity per trade day
leverage            500x
equal_weight        true     split equally across the 3 assets
max_assets          3
```

**EXECUTION**

```
entry        day's OPEN
exit         day's CLOSE
hard stop    1% from entry, checked intraday on high/low
re-entry     not allowed after a stop
```

**RISK LIMITS (declared in config, but the engine never halts on them)**

```
max_drawdown_pct   0.20
max_daily_loss_pct 0.10
```
`src/engine.py` records these as `risk_events` for reporting only. Comment in the
code: *"The Agba Metta daily loop has no halt step: every aligned day is traded."*

## The author's own recorded result

```
period            2026-07-01 to 2026-07-24
initial capital   $100,000
final equity      $1,126,407.83
total return      +1026.41%
trade days        4
day win rate      100.00%  (4/4)
asset win rate    100.00%  (12/12)
profit factor     inf
max drawdown      0.00%
Sharpe            8.41
goals_met         True
```

## Why it returns 1026% — proven from the author's own trade file

The equity comes from **compounding 20% of a growing balance at 500x**:

| trade day | position size per asset |
|---|---:|
| 2026-07-07 | $6,666.67 |
| 2026-07-13 | $11,442.34 |
| 2026-07-16 | $23,485.23 |
| 2026-07-23 | $43,083.53 |

**6.46× growth in position size across 4 trade days.** 20% × 500x = **100× equity
notional per asset**, so a 1.4% gold move returns 143% of the trade's stake.

## The one thing you should know about it

From the author's own `trades_agba_metta.csv`:

```
trades where entry_date == exit_date : 12 of 12
stops hit                            : 0 of 12
losing trades                        : 0 of 12
```

**Every trade opens and closes on the same day.** Alignment is tested on that
day's **close**; entry is that same day's **open**.

Example, the first trade:

```
XAUUSD-2026-07-07-CLOSE
  entry 4166.99 at the OPEN  of 2026-07-07
  exit  4107.32 at the CLOSE of 2026-07-07
```

The close that authorises the trade is the same close it exits at. **The model
enters at a price that has already passed by the time its own signal exists.**

That is why 12 of 12 trades win, 0 of 12 stops are hit, and max drawdown is
exactly 0.00%. It only ever enters days it has already seen close in its favour.

This is not a criticism of the idea — it is a property of the code as written,
and it is the single reason the +1026.41% cannot be reproduced live. When I move
entry to the next bar's open and change nothing else, July 2026 goes from
**+1026%** to **−72.32%**, 3 stops fire, and drawdown becomes −84.36%.

## Summary in one line

**Agba Metta = real-yield regime picks the direction → all three of gold/EUR/AUD
must confirm it with same-direction candles → trade all three at 20% equity and
500x with a 1% stop, open to close.**

The regime gate has never once fired LONG: real yield ran 1.67–2.34 across
2025–2026, always above 0.7, so the live model is **short-only, 100% of the time**.

Source: `cebb21c:config/model_config.yaml`, `cebb21c:src/engine.py`,
`cebb21c:backtest_results/{summary,trades}_agba_metta.{json,csv}`
