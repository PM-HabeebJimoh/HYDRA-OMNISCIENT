# The Real Agba Metta Model

Corrected. My previous write-up described the **author's code**, not the model.
The code enters on the signal candle. **The model does not** — the signal candle
and the entry candle are two different candles.

## The four steps

```
STEP 1  REGIME     real yield (FRED DFII10)
                     > 0.7%  ->  CONTRACTION  ->  SHORT
                     < -0.1% ->  EXPANSION    ->  LONG
                     between ->  STABILITY    ->  no trade

STEP 2  SIGNAL     candle i CLOSES
                   all 3 of XAUUSD / EURUSD / AUDUSD closed in the regime
                   direction  ->  SIGNAL CONFIRMED
                   mixed      ->  no signal

STEP 3  ENTRY      candle i+1 OPEN          <-- NEXT CANDLE
                   1% hard stop from the ACTUAL entry price

STEP 4  EXIT       candle i+1 CLOSE, unless the stop hits intraday
```

Sizing: 20% of equity per signal, split equally across the 3 assets, 500x.

**The signal candle is never traded.** You cannot act on a close until it has
happened, and by then that candle is gone. You trade the candle *after* it.

## Why this is the whole model

The author's `trades_agba_metta.csv` has `entry_date == exit_date` on 12 of 12
trades — it reads the close of day D and buys the open of day D. That is the
implementation, and it is what produces +1026.41% with 12/12 wins, 0 stops and
0.00% drawdown. **A model that only enters candles it has already seen close
in its favour cannot lose.**

With the correct next-candle timing, on the same real July 2026 bars:

| TF | timing | signals | asset WR | stops | return | maxDD |
|---|---|---:|---:|---:|---:|---:|
| DAILY | same candle (code) | 4 | 100.0% | 0 | **+953.78%** | 0.00% |
| DAILY | **NEXT candle (model)** | 4 | 33.3% | 2 | **−81.78%** | −82.82% |
| 4H | same candle (code) | 30 | 100.0% | 0 | **+82,144.71%** | 0.00% |
| 4H | **NEXT candle (model)** | 31 | 55.9% | 1 | **+29.96%** | −68.36% |
| 1H | same candle (code) | 94 | 100.0% | 0 | **+5,128,203.35%** | 0.00% |
| 1H | **NEXT candle (model)** | 95 | 56.8% | 2 | **−35.29%** | −79.03% |

## Every trade, July 2026 daily, correct timing

| asset | signal candle | entry candle | entry | exit | move | exit |
|---|---|---|---:|---:|---:|---|
| XAUUSD | 07-07 | **07-08** | 4098.58 | 4076.04 | +0.550% | CLOSE |
| EURUSD | 07-07 | **07-08** | 1.14020 | 1.14210 | −0.167% | CLOSE |
| AUDUSD | 07-07 | **07-08** | 0.69220 | 0.69360 | −0.202% | CLOSE |
| XAUUSD | 07-13 | **07-14** | 4001.24 | 4041.25 | −1.000% | **STOP** |
| EURUSD | 07-13 | **07-14** | 1.13840 | 1.14210 | −0.325% | CLOSE |
| AUDUSD | 07-13 | **07-14** | 0.69200 | 0.69892 | −1.000% | **STOP** |
| XAUUSD | 07-16 | **07-17** | 3986.48 | 4017.23 | −0.771% | CLOSE |
| EURUSD | 07-16 | **07-17** | 1.14460 | 1.14380 | +0.070% | CLOSE |
| AUDUSD | 07-16 | **07-17** | 0.70000 | 0.69810 | +0.271% | CLOSE |
| XAUUSD | 07-23 | **07-24** | 4047.32 | 4052.98 | −0.140% | CLOSE |
| EURUSD | 07-23 | **07-24** | 1.13760 | 1.13710 | +0.044% | CLOSE |
| AUDUSD | 07-23 | **07-24** | 0.69670 | 0.69830 | −0.230% | CLOSE |

4 signals → 12 asset trades, 2 stopped. Final $18,219.68, **−81.78%**.

Note the signal/entry columns are always one candle apart. That single column is
the difference between +953.78% and −81.78%.

## The regime gate has never fired LONG

Real yield ran **1.67 to 2.34** across all of 2025–2026 — always above 0.7. So
CONTRACTION is permanent and the model is **SHORT-only, 100% of the time**. The
EXPANSION branch has never executed a single trade.

## Summary

**Real yield sets the direction → wait for a candle to close with all three
assets confirming it → enter the NEXT candle's open at 20% equity and 500x →
exit that candle's close or a 1% stop.**

Source: `cebb21c:config/model_config.yaml`, `cebb21c:src/engine.py`,
`cebb21c:backtest_results/trades_agba_metta.csv`
Reproduce: `python3 -m research.real_model`
