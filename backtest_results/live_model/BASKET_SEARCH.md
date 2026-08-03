# Searching all currencies for a 3-alignment basket better than XAU/EUR/AUD

Every 3-currency combination from 10 instruments — XAUUSD, XAGUSD, EURUSD,
AUDUSD, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY, EURGBP — tested as an Agba Metta
alignment basket: **all 3 close the same direction on the signal bar -> trade
those same 3 on the next bar, open to close, 20% equity split equally.**

120 triplets x 2 directions = **196 baskets.** Real costs per instrument.
Window: 2026-01-01 -> 2026-07-28, 149 sessions (the span where all 10 pairs exist).

**Data limitation, stated plainly:** the 7 non-core pairs in `data/raw/xpairs/`
carry **open and close only — no high/low**. The 1% intraday stop cannot be
evaluated on them. So every basket here is run open->close *without* the stop, to
compare like with like. That also means these results are not directly comparable
to the stop-based runs in earlier reports.

## Top baskets found

| basket | dir | n | WR% | edge/trade | t | lev@DD5% | /month |
|---|---|---:|---:|---:|---:|---:|---:|
| **AUDUSD+GBPUSD+USDCAD** | FADE | 20 | **75.0** | +0.1621% | **+3.55** | 28.2x | **+13.16%** |
| EURUSD+AUDUSD+USDCAD | FADE | 22 | 72.7 | +0.1373% | +2.98 | 9.8x | +4.20% |
| GBPUSD+NZDUSD+USDCAD | FADE | 21 | 66.7 | +0.1090% | +2.55 | 16.2x | +5.26% |
| EURUSD+NZDUSD+USDCAD | FADE | 22 | 72.7 | +0.1000% | +2.39 | 17.5x | +5.41% |
| NZDUSD+USDCAD+USDJPY | FOLL | 15 | **80.0** | +0.0688% | +1.93 | 23.2x | +3.35% |
| XAGUSD+AUDUSD+USDCHF | FADE | 23 | 73.9 | +0.4370% | +1.65 | 1.0x | +1.42% |

**Where the current basket ranks:**

| XAUUSD+EURUSD+AUDUSD | n | WR% | edge/trade | t | rank |
|---|---:|---:|---:|---:|---:|
| FOLLOW (original) | 83 | 39.8 | **-0.0604%** | -0.74 | **154 / 196** |
| FADE (reversed) | 83 | 57.8 | +0.0520% | +0.63 | 43 / 196 |

**Your current basket, traded the way the model trades it, ranks 154th out of 196.**
Even reversed it only reaches 43rd. So yes — many baskets look better.

## But do the better ones survive testing?

**Split-half persistence** (select nothing; just look at both halves):

| basket | dir | TRAIN n / WR / t | TEST n / WR / t |
|---|---|---|---|
| AUDUSD+GBPUSD+USDCAD | FADE | 6 / 83.3% / +2.86 | 14 / 71.4% / **+2.51** |
| EURUSD+AUDUSD+USDCAD | FADE | 6 / 100% / +4.84 | 16 / 62.5% / +1.57 |
| GBPUSD+NZDUSD+USDCAD | FADE | 8 / 75.0% / +1.08 | 13 / 61.5% / **+2.62** |
| XAUUSD+EURUSD+AUDUSD | FADE | 37 / 48.6% / -0.45 | 46 / 65.2% / +1.65 |

The top basket held up in both halves — genuinely encouraging.

**Selection-noise null.** 196 baskets were searched, so the winner must be
compared to the best-of-196 under no edge (200 runs, whole-day sign flips that
preserve cross-pair correlation):

    actual best t = +3.55
    noise best t  : median +2.63, 95th pct +3.70, max +4.55
    p = 0.075  ->  INDISTINGUISHABLE FROM SELECTION NOISE

Searching 196 baskets over 149 days produces a t of +2.63 **by chance alone**. Our
+3.55 does not clear the 95th percentile of +3.70.

**Family test — is USDCAD structurally special?** It appears in the top 4 baskets,
so I tested one hypothesis (no selection): do FADE baskets containing USDCAD beat
those without?

    WITH USDCAD    : 29 baskets, mean t = +0.12, median -0.27
    WITHOUT USDCAD : 69 baskets, mean t = +0.10, median +0.06

**No difference.** USDCAD is not structurally better; it happened to land in the
lucky triplets. And USDCAD's 1-day autocorrelation is **+0.116** — the only
*positive* one of the ten — meaning it is the least mean-reverting pair, the
opposite of what a FADE edge should like.

## The core problem: sample size

The top basket has **20 trades**. Alignment across 3 specific currencies is rare —
tighter baskets fire less often. 20 trades cannot distinguish a 75% edge from luck;
the 95% interval around 75% at n=20 runs roughly 53% to 89%.

The current basket's 83 trades are its one real advantage: XAU/EUR/AUD are diverse
enough to align reasonably often.

## Honest answer

- **Yes, better-looking baskets exist.** AUDUSD+GBPUSD+USDCAD faded shows 75% WR,
  +13.16%/month at DD<5%, and it persisted across both halves of 2026.
- **No, I cannot yet call it better.** It fails the selection-noise test (p=0.075),
  USDCAD shows no structural advantage, and 20 trades is too few.
- **Your current basket genuinely is poor** in its traded direction — 154th of 196,
  negative edge. That part is solid, and consistent with the reversal finding.

What would settle it: **2025 data for the 7 non-core pairs, plus high/low so the 1%
stop can be applied.** That would roughly triple the sample on
AUDUSD+GBPUSD+USDCAD and make it testable on data that played no part in
selecting it. The `data/raw/majors/` 2025 files exist but are empty; I can fetch
them through the same verified Investing.com pipeline used for the core 3.

Reproduce: `research.basket_search`, `research.basket_validate`, `research.usdcad_family`
