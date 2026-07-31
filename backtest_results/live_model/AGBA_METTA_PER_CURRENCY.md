# Agba Metta model, per currency — signal BEFORE alignment

I went back and read `config/model_config.yaml` and `src/engine.py`. You were right
that I had drifted. Your model has **three steps in a fixed order**, and I had been
skipping step 1:

    STEP 1  SIGNAL     real yield decides direction
                       yield > 0.7   -> CONTRACTION -> SHORT
                       yield < -0.1  -> EXPANSION   -> LONG
                       in between    -> STABILITY   -> no trade

    STEP 2  ALIGNMENT  all 3 assets must CONFIRM that direction
                       SHORT needs every asset close < open

    STEP 3  EXECUTE    enter at open, exit at close, 1% hard stop

The signal comes first, alignment only confirms it. That is what I tested here.

## Step 1 result: the regime never changes

Real yield across 2025-01-02 to 2026-07-29 ranges **1.67 to 2.34**. It is *always*
above 0.7, and never below -0.1.

    SHORT days: 409      LONG days: 0      NO-TRADE days: 0

**The model is SHORT 100% of the time.** The EXPANSION/LONG branch never fires
once in 409 days. So the regime filter is not selecting anything — it is a
constant. Every trade the model ever takes is a short.

## Step 2 + 3: after each currency confirms, does it keep falling?

Regime says SHORT; the currency confirms by closing down. The model then bets it
falls again next day.

| pair | confirm days | fell again | accuracy | avg win | avg loss | edge/trade |
|---|---:|---:|---:|---:|---:|---:|
| XAUUSD | 178 | 66 | **37.08%** | 1.3810% | -0.9200% | **-0.0668%** |
| XAGUSD | 65 | 27 | 41.54% | 4.3627% | -2.7844% | +0.1844% |
| EURUSD | 208 | 108 | 51.92% | 0.2792% | -0.3823% | -0.0388% |
| AUDUSD | 193 | 86 | 44.56% | 0.4449% | -0.4460% | -0.0490% |
| GBPUSD | 81 | 43 | 53.09% | 0.3132% | -0.3472% | +0.0034% |
| NZDUSD | 76 | 37 | 48.68% | 0.5026% | -0.4497% | +0.0139% |
| USDCAD | 61 | 29 | 47.54% | 0.2428% | -0.1684% | +0.0271% |
| USDCHF | 63 | 29 | 46.03% | 0.4061% | -0.4289% | -0.0445% |
| USDJPY | 49 | 13 | **26.53%** | 0.4498% | -0.3408% | -0.1310% |
| EURGBP | 71 | 30 | 42.25% | 0.2332% | -0.1422% | +0.0164% |

## With FULL alignment required (all 3 core assets confirm first)

| pair | aligned days | fell again | accuracy | edge/trade |
|---|---:|---:|---:|---:|
| XAUUSD | 102 | 33 | **32.35%** | **-0.3142%** |
| XAGUSD | 42 | 11 | **26.19%** | **-0.8482%** |
| EURUSD | 102 | 45 | 44.12% | -0.0915% |
| AUDUSD | 102 | 41 | 40.20% | -0.1200% |
| GBPUSD | 42 | 17 | 40.48% | -0.1341% |
| NZDUSD | 42 | 14 | 33.33% | -0.1850% |
| USDCHF | 42 | 25 | 59.52% | +0.0869% |
| EURGBP | 42 | 24 | 57.14% | +0.0753% |
| USDCAD | 42 | 20 | 47.62% | +0.0393% |
| USDJPY | 42 | 19 | 45.24% | +0.0705% |

## The core finding

Running the model's own basket, its own way:

    Alignment fires (all 3 close DOWN): 102 days out of 409

    The SHORT won :  35 / 102  = 34.3%
    The SHORT lost:  67 / 102  = 65.7%
    Average per trade: -0.1752%   (t = -2.71)

    gold kept falling 32.4% of the time
    eur  kept falling 44.1% of the time
    aud  kept falling 40.2% of the time

**The model bets on CONTINUATION. The data does the OPPOSITE — it REVERSES.**

t = -2.71 is statistically significant. This is not a weak or absent edge; it is a
real effect pointing the **wrong way**. After all three assets fall together, they
tend to bounce, and gold bounces hardest (only 32% follow-through).

## What this means

The alignment filter genuinely finds something real: a **capitulation / exhaustion
day**. Three correlated assets all closing down together marks a short-term low,
not the start of a further drop. The model then sells that low.

**Taking the same signal and buying instead of selling wins 65.7% of days,
averaging +0.1752% per trade.**

That is the honest result, in the model's own terms, on 409 real trading days.

Two cautions before anyone acts on the reversed version:
1. The 500x/20% sizing is unchanged by direction. At that size a 1% stop is still
   -33% of equity per leg, so the reversal must be traded much smaller.
2. This is one 19-month sample, and it is the same data that suggested the
   original direction. It needs 2020-2024 to confirm.

Reproduce: `research.agba_percurrency`, `research.agba_verdict`
