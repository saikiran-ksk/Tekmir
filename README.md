# SignalDesk Weekly Health Check

**Track:** Track 1 — Fictional Domain Packet  
**Built for:** A teammate on the SignalDesk product team who needs to decide what to investigate next.

## What I Built

A lightweight Python script (`signaldesk_health_check.py`) that loads the messy `product_usage_events.csv`, cleans known data quality issues, compares workflow health before and after the Aug 4 prompt change, and prints a concise diagnostic report with clear recommendations.

## Who It Is For

A product manager or engineer on the SignalDesk team who wants a 60-second read on what changed, what looks suspicious, and what to look at next — without building a BI dashboard.

## Data & Source

- `sample-data/product_usage_events.csv` from the challenge repo.
- 40 rows (after dropping 1 duplicate), Aug 1–7, 2026.
- 3 workflows: Lead summary, Reply draft, Feedback clustering.

## Key Assumptions

1. **"Completed" ≠ "good."** I treat completion rate as a throughput metric, not a quality metric.
2. **"Accepted output" is the best available quality signal**, but it is still rough (users may accept out of fatigue).
3. **Model confidence is NOT quality.** I explicitly warn against using it as a proxy.
4. **The Aug 5 demo spike and Aug 7 policy change are not comparable** to normal days, so I exclude them from pre/post comparisons but flag them.
5. **Small samples (Product manual source, 5–12 sessions/day) are directional only.**

## Issues Noticed

- **Duplicate export row** on Aug 5 (dropped).
- **"n/a" confidence** on Aug 5 Product manual (converted to NaN).
- **Missing user rating** on Aug 1 Support manual.
- **Team casing inconsistency** ("product" vs "Product") — fixed.
- **Most alarming:** Aug 7 Reply draft queue had a mid-day review policy change. Only 17 of 30 sessions completed, 12 of 17 were flagged, and user rating crashed to 2.1 — despite model confidence being 0.91. This is the strongest evidence that confidence ≠ quality.

## What I Would Do Next

1. **Validate the Aug 7 policy change** — interview the Support team lead who changed the policy. Was it a reaction to worse output, or a proactive stricter standard?
2. **Segment by source** — email/queue vs. manual inputs behave differently. The prompt change may have helped email inputs but hurt queue inputs.
3. **Add a simple weekly tracker** — acceptance-per-session, flag rate, and user rating per workflow. Ignore confidence and minutes-saved.
4. **Get more data** — 7 days is thin, especially for Feedback clustering (small sample) and manual sources.

## How to Run

```bash
python signaldesk_health_check.py
```

Requires: `pandas`, `numpy` (standard data science stack).
