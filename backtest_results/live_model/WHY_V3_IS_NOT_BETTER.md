# "These are worse than AGBA-METTA" — here is the test that settles it

You are right that my numbers are smaller. The question is whether V3's bigger
numbers are **money** or **bookkeeping**. One experiment answers it.

I ran **your V3 exactly as written** — all 7 enhancements, 400x, the graded
leverage ladder, every filter — and then ran **the identical code with one line
changed**: book the loss the market actually delivered instead of -2%.

Nothing else differs. Same bars, same signals, same sizing.

## Result

| | V3 as written | Cap OFF (real P&L) |
|---|---:|---:|
| Daily pooled | **+600.89%** (DD -14.82%) | **-45.40%** (DD -71.27%) |
| 4H pooled | **+4,633.64%** (DD -11.20%) | **+37.97%** (DD -64.89%) |
| 1H pooled | **+1,627.20%** (DD -15.46%) | **-68.28%** (DD -74.22%) |

Every month, same story. Mar26 4H: +374% becomes **-16%**. Jun26 4H: +28% becomes
**-51%**. Feb26 1H: +65% becomes **-38%**.

**The entire performance is the cap.** Turn it off and the model loses money.

## Where the money comes from — hand-checked against raw bars

Worst event, 2026-03-02 16:00 UTC, 4H. Verified directly from the Investing.com
bars in this repo (`research/onebar.py`):

    SIGNAL 12:00  gold -1.299%  eur -0.452%  aud -0.367%  -> all DOWN -> SHORT
    TRADE  16:00  grade A, 300x, equity $875,580

      gold  short @5314.40 -> 5330.45   -0.302%   notional $17,511,600   -$52,887
      eur   short @1.16800 -> 1.17110   -0.265%   notional $17,511,600   -$46,478
      aud   short @0.70580 -> 0.71040   -0.652%   notional $17,511,600  -$114,131

      REAL P&L      -$213,495  = -24.38% of equity
      V3 books        -$17,512 = -2.00%
      IGNORED        -$195,983

Note the notional: **$17.5m per leg on $875k of equity** — 60x equity across the
basket. Three small moves (-0.3%, -0.27%, -0.65%) become -24% of the account.
That is the arithmetic I described before, in one concrete trade you can check.

Across the pooled run the cap absorbs losses **57 times on 4H** and **77 times on
1H**, hiding **$5,305,744** and **$1,743,698** of real losses respectively.

## Why no broker gives you this

The -2% cap assumes someone closes all three legs, mid-bar, at exactly -2% of
account equity. Nobody offers that. What actually exists:

- A **stop per instrument** — already in the model, at 1%. It did not save these
  trades; on the March 2 bar no leg even hit its stop.
- A **margin call** — fires at the broker's convenience, at the worst price, and
  it is the -24% that lands in your account, not -2%.

So the cap is not a risk control. It is an accounting rule that deletes losses
after the market has already charged them.

## The honest comparison

|  | monthly ROI | real? |
|---|---:|---|
| V3 as written | +600% to +4,600% pooled | **no** — cap absorbs $7.0m of real losses |
| V3, cap off | -68% to +38% pooled | yes |
| My 4H gold model | +4.06% | yes, but fails a noise test |
| My 10-instrument portfolio | +1.24% | yes |

My numbers are smaller because they are the ones a broker would actually pay.
V3's numbers are larger because the loss column is switched off.

Reproduce: `python3 -m research.capproof`, `research.capmoney`, `research.onebar`
