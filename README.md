**# Helldivers 2 Patch Quality Control Chart

Applying statistical process control (the control-chart stuff used in
manufacturing QA) to live-service game patches — using player reviews as the
quality signal to figure out which patches actually broke the game vs. which
ones just got normal complaints.

## What this does

Games ship patches constantly and some of them are genuinely bad. Instead of
just going off vibes ("this patch sucked"), this pulls real Steam review data
and runs it through a control-chart method to statistically flag which
patches were actual quality failures.

## How it works

1. **Pull reviews** — pages through Steam's `appreviews` API, grabbing
   review text, timestamp, thumbs up/down. Handles pagination, rate-limit
   backoff, and checkpoints to disk so a long pull doesn't get wiped if
   something breaks.

2. **Bucket by patch window** — each patch has a release date, reviews get
   sorted into the window between one patch and the next.

3. **Defect rate per patch** — % of thumbs-down reviews in that window. Went
   with this over keyword/bug-mention detection since overall negative
   sentiment is a better signal of "this patch was bad" than someone just
   mentioning a bug in an otherwise positive review.

4. **Iterative 3-sigma** — calculate mean/std dev, set limits at ±3 sigma,
   drop anything outside the limits, recalculate, repeat until stable.
   Doing it once would let the disaster patches drag the "normal" range up
   and hide themselves. 3-sigma specifically because ~99.7% of values fall
   within that range normally, so anything outside it is rare enough to
   call a real problem, not noise.

## Finding

33 patch windows, ~75k reviews (June 2025–Sept 2026). Two patches got
flagged as statistically out of control:

| Date | Negative review rate | Patch |
|---|---|---|
| 2026-04-28 | 71.0% | Machinery of Oppression 6.2.2 |
| 2026-05-06 | 56.5% | Machinery of Oppression 6.2.3 |

The April 28 one checks out — patch 6.2.2 buffed enemy durability (Hive
Guard armor, Terminid durable damage) and reworked Exosuits, and player
reception was reported as largely negative, Steam feedback "overwhelmingly
critical." The model flagged this purely off review data, no outside
context, press coverage just confirms it after the fact.

## Known limitations

- LCL comes out negative in this run, which isn't really meaningful for a
  rate that can't go below 0%, that's just a known quirk of applying 3-sigma
  to bounded data, not a bug.
- Steam rate limits meant scoping this to June 2025 onward instead of the
  full 2024 launch history.
- One game for now (Helldivers 2). Adding more titles for cross-validation
  is next.

## Dashboard

Streamlit, shows defect rate per patch, UCL/LCL overlay, and the flagged
patches with real dates.

```bash
streamlit run dashboard.py
```

## Stack

Python, `requests` (Steam API), `statistics`, `pandas`, Streamlit

## Files

- `pull_reviews.py` — pull, bucket, run the 3-sigma analysis
- `dashboard.py` — the dashboard
- `reviews_checkpoint.json` — cached review data**
