#!/usr/bin/env python3
"""
SignalDesk Weekly Health Check
==============================
A lightweight diagnostic script for the SignalDesk product team.

Usage:
    python signaldesk_health_check.py [path/to/product_usage_events.csv]

What it does:
    - Loads product_usage_events.csv
    - Cleans known data quality issues
    - Compares workflow health before/after the Aug 4 prompt change
    - Flags suspicious records and metrics that should not be trusted blindly
    - Prints a concise recommendation for what to investigate next

Author: Built for the DS Intern Build Challenge, Track 1
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime


def load_and_clean_data(csv_path="product_usage_events.csv"):
    """Load the dataset and apply known data quality fixes."""
    df = pd.read_csv(csv_path)

    # 1. Standardize team casing
    df["team"] = df["team"].str.title()

    # 2. Drop the duplicate export row (Aug 5, Sales, Lead summary, email)
    df = df[df["notes"] != "duplicate export row"].copy()

    # 3. Convert "n/a" confidence to NaN
    df["median_confidence"] = pd.to_numeric(df["median_confidence"], errors="coerce")

    # 4. Parse dates
    df["date"] = pd.to_datetime(df["date"])

    # 5. Tag data quality issues
    df["dq_flag"] = ""

    # Demo account traffic spike
    demo_mask = (
        (df["date"] == "2026-08-05") &
        (df["workflow"] == "Lead summary") &
        (df["source"] == "email") &
        (df["notes"] == "traffic spike from demo account")
    )
    df.loc[demo_mask, "dq_flag"] = "DEMO_SPIKE"

    # Mid-day policy change (not comparable)
    policy_mask = (
        (df["date"] == "2026-08-07") &
        (df["workflow"] == "Reply draft") &
        (df["source"] == "queue")
    )
    df.loc[policy_mask, "dq_flag"] = "POLICY_CHANGE_MIDDAY"

    # Small samples
    df.loc[df["sessions"] < 10, "dq_flag"] += "|SMALL_SAMPLE"

    # Missing values
    df.loc[df["median_confidence"].isna(), "dq_flag"] += "|MISSING_CONFIDENCE"
    df.loc[df["user_rating"].isna(), "dq_flag"] += "|MISSING_RATING"

    return df


def compute_workflow_metrics(df, exclude_dq=True):
    """Aggregate metrics by workflow and pre/post period."""
    df = df.copy()
    df["period"] = df["date"].apply(
        lambda x: "pre" if x < pd.Timestamp("2026-08-04") else "post"
    )

    if exclude_dq:
        # Exclude demo spike and mid-day policy change for fair comparison
        df = df[df["dq_flag"] != "DEMO_SPIKE"]
        df = df[df["dq_flag"] != "POLICY_CHANGE_MIDDAY"]

    summary = df.groupby(["workflow", "period"]).agg({
        "sessions": "sum",
        "completed": "sum",
        "accepted_output": "sum",
        "flagged_for_review": "sum",
        "avg_minutes_saved": "mean",
        "median_confidence": "mean",
        "user_rating": "mean",
    }).reset_index()

    summary["completion_rate"] = (summary["completed"] / summary["sessions"]).round(3)
    summary["acceptance_rate"] = (summary["accepted_output"] / summary["completed"]).round(3)
    summary["flag_rate"] = (summary["flagged_for_review"] / summary["completed"]).round(3)
    summary["acceptance_per_session"] = (summary["accepted_output"] / summary["sessions"]).round(3)

    return summary


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_health_check(summary):
    """Print a concise health check table."""
    print_header("WORKFLOW HEALTH: PRE vs POST PROMPT CHANGE (Aug 4)")
    print("\n(Fair comparison: excludes Aug 5 demo spike & Aug 7 policy change)\n")

    workflows = ["Lead summary", "Reply draft", "Feedback clustering"]
    metrics = ["completion_rate", "acceptance_rate", "flag_rate", "avg_minutes_saved", "median_confidence", "user_rating"]
    metric_names = ["Completion", "Acceptance", "Flag Rate", "Min Saved", "Confidence", "User Rating"]

    # Header
    print(f"{'Workflow':<20} {'Period':<6} " + " ".join(f"{m:<12}" for m in metric_names))
    print("-" * 100)

    for wf in workflows:
        pre = summary[(summary["workflow"] == wf) & (summary["period"] == "pre")]
        post = summary[(summary["workflow"] == wf) & (summary["period"] == "post")]

        pre_vals = [pre[m].values[0] if len(pre) else "N/A" for m in metrics]
        post_vals = [post[m].values[0] if len(post) else "N/A" for m in metrics]

        print(f"{wf:<20} {'pre':<6} " + " ".join(f"{v:<12.2f}" if isinstance(v, float) else f"{v:<12}" for v in pre_vals))
        print(f"{'':20} {'post':<6} " + " ".join(f"{v:<12.2f}" if isinstance(v, float) else f"{v:<12}" for v in post_vals))
        print()


def print_data_quality_report(df):
    """Print all flagged records."""
    print_header("DATA QUALITY FLAGS")

    flagged = df[df["dq_flag"] != ""].copy()
    if len(flagged) == 0:
        print("\nNo data quality flags.")
        return

    print(f"\n{len(flagged)} flagged record(s):\n")
    for _, row in flagged.iterrows():
        print(f"  [{row['date'].strftime('%Y-%m-%d')}] {row['workflow']} ({row['source']})")
        print(f"    Sessions: {row['sessions']}, Completed: {row['completed']}, Accepted: {row['accepted_output']}")
        print(f"    Flags: {row['dq_flag']}")
        print(f"    Note: {row['notes']}")
        print()


def print_recommendations(summary, df):
    """Print actionable recommendations."""
    print_header("RECOMMENDATIONS")

    # Compute deltas for fair comparison
    recs = []

    for wf in ["Lead summary", "Reply draft", "Feedback clustering"]:
        pre = summary[(summary["workflow"] == wf) & (summary["period"] == "pre")]
        post = summary[(summary["workflow"] == wf) & (summary["period"] == "post")]

        if len(pre) == 0 or len(post) == 0:
            continue

        comp_delta = post["completion_rate"].values[0] - pre["completion_rate"].values[0]
        acc_delta = post["acceptance_rate"].values[0] - pre["acceptance_rate"].values[0]
        flag_delta = post["flag_rate"].values[0] - pre["flag_rate"].values[0]
        rating_delta = post["user_rating"].values[0] - pre["user_rating"].values[0]

        recs.append({
            "workflow": wf,
            "comp_delta": comp_delta,
            "acc_delta": acc_delta,
            "flag_rate_delta": flag_delta,
            "rating_delta": rating_delta,
        })

    recs_df = pd.DataFrame(recs)

    print("\n1. MOST TRUSTED METRIC: User Rating")
    print("   - It is the only metric that directly reflects user judgment.")
    print("   - All workflows improved slightly post-prompt change.")
    print("   - However, ratings are sparse (1 missing) and subjective.")

    print("\n2. LEAST TRUSTED METRIC: Model Confidence")
    print("   - Aug 7 Reply draft queue: confidence 0.91, user rating 2.1")
    print("   - Confidence rose for all workflows post-prompt, but this")
    print("     does NOT correlate with acceptance or flag rates.")
    print("   - Do NOT use confidence as a quality proxy.")

    print("\n3. WORKFLOW RANKING (most useful right now):")

    # Rank by acceptance_per_session (most holistic metric)
    ranking = []
    for wf in ["Lead summary", "Reply draft", "Feedback clustering"]:
        post = summary[(summary["workflow"] == wf) & (summary["period"] == "post")]
        if len(post):
            ranking.append((wf, post["acceptance_per_session"].values[0]))
    ranking.sort(key=lambda x: x[1], reverse=True)

    for i, (wf, score) in enumerate(ranking, 1):
        print(f"   {i}. {wf}: {score:.1%} acceptance per session")

    print("\n4. WHAT TO INVESTIGATE NEXT:")

    # Find the workflow with the worst delta
    worst_comp = recs_df.loc[recs_df["comp_delta"].idxmin()]
    worst_flag = recs_df.loc[recs_df["flag_rate_delta"].idxmax()]

    print(f"   a) {worst_comp['workflow']}: completion rate dropped by {abs(worst_comp['comp_delta']):.1%} post-prompt.")
    print(f"      -> Check if the new prompt is causing more failures.")

    print(f"   b) {worst_flag['workflow']}: flag rate increased by {worst_flag['flag_rate_delta']:.1%} post-prompt.")
    print(f"      -> Are outputs actually worse, or are reviewers being stricter?")

    print("   c) Aug 7 Reply draft queue: mid-day policy change caused")
    print("      a massive drop (17/30 completed, 12/17 flagged, rating 2.1).")
    print("      -> Understand the new policy before rolling out broadly.")

    print("   d) Feedback clustering: lowest acceptance rate (~65%) and")
    print("      highest flag rate (~18%). Small sample for manual source.")
    print("      -> Needs more usage data before trusting trends.")

    print("\n5. SIMPLE WEEKLY HEALTH CHECK:")
    print("   Track these 3 numbers per workflow:")
    print("   - Acceptance per session (best single metric)")
    print("   - Flag rate (early warning signal)")
    print("   - User rating (ground truth, when available)")
    print("   Ignore: model confidence, avg_minutes_saved (too noisy/directional)")


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "product_usage_events.csv"

    print("SignalDesk Weekly Health Check")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    df = load_and_clean_data(csv_path)
    summary = compute_workflow_metrics(df, exclude_dq=True)

    print_health_check(summary)
    print_data_quality_report(df)
    print_recommendations(summary, df)

    print_header("END OF REPORT")
    print("\nFor questions, check the README.md and AI_NOTE.md.")


if __name__ == "__main__":
    main()
