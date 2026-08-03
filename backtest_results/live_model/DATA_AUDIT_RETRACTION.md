# RETRACTION — July 2026 AUD+GBP+CAD 1H/4H results are NOT valid

I audited my own transcribed data against the source. I found a real error and
I am withdrawing the 4H and 1H numbers from `JULY2026_AUDGBPCAD_ALL_TF.md`.

## What I claimed

> GBPUSD 312 bars, **16 days**, 2026-07-01 → 2026-07-23, envelope_fixes=0
> USDCAD 312 bars, **16 days**, 2026-07-01 → 2026-07-23, envelope_fixes=0

## What is actually in the files

    FULL days present : 07-01, 07-02, 07-03, 07-06, 07-07, 07-08,
                        07-13, 07-14, 07-15, 07-16, 07-20, 07-21, 07-22   = 13 days
    "Days" that are only a single boundary bar : 07-09, 07-17, 07-23
    July weekdays missing entirely : 07-10, 07-24, 07-27, 07-28, 07-29, 07-30, 07-31

**13 real days out of 23 July weekdays = 57% coverage.**

My "16 days" counted three window-endpoint stubs as if they were trading days.
That was a counting error in my own save routine, and I reported it without
checking.

## The concrete miss: 2026-07-17

I re-fetched 07-17 from the source. It returns **21 real hourly bars**:

    1783641600  o 1.3413  h 1.3425  l 1.3409  c 1.3423
    1783645200  o 1.3422  h 1.3439  l 1.3420  c 1.3436
    1783648800  o 1.3435  h 1.3452  l 1.3434  c 1.3448
    1783652400  o 1.3449  h 1.3450  l 1.3437  c 1.3438
    1783656000  o 1.3439  h 1.3439  l 1.3428  c 1.3430   ... (21 total)

My stored file contains **0 bars** for 07-17. I fetched the window
`1783555200..1783641600`, which *ends* at 07-17 00:00, and never fetched
`1783641600..1783728000`. The same off-by-one dropped 07-10 and everything from
07-24 onward.

## Why the verification I ran did not catch it

I compared each day's aggregated 1H high/low against the daily OHLC and reported
"12 of 13 full days consistent." That check only inspects days that *are*
present. It is structurally incapable of detecting a missing day. I presented a
passing check on 13 days as if it validated a 16-day, 23-weekday month.

## What is retracted

- **4H: −8.18%** and **1H: −9.81%** for AUD+GBP+CAD — withdrawn. Computed on 57%
  of the month with 6 and 13 signals respectively. Not valid.
- The claim "1H/4H window 2026-07-01 → 2026-07-23" — false; it is 13
  non-contiguous days.
- The statement "intraday is less bad than daily" — unsupported. It rested on
  those two numbers.

## What still stands

- **DAILY −46.73%** for AUD+GBP+CAD. This used the separately fetched daily OHLC
  (30 bars, 2026-06-22 → 2026-07-31), which I cross-checked 107/108 against the
  existing feed. That file is complete and the result holds.
- The core XAU/EUR/AUD Daily/4H/1H July results, which used the pre-existing
  verified intraday panels, not this new transcription.
- The signal-bar vs next-bar timing finding, which reproduces on every dataset
  independently.

## To do this properly

7 missing weekdays × 2 pairs = 14 more fetches, then re-run the day-count check
as an explicit assertion against the July weekday calendar rather than a
self-reported total. I will not report 4H/1H for this basket again until the
month is actually complete.
