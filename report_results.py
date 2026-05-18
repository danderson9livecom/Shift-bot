import csv
import os
from collections import defaultdict

TRACKER_LOG = "tracker_log.csv"


def load_results():
    if not os.path.exists(TRACKER_LOG):
        print(f"{TRACKER_LOG} not found.")
        return []

    rows = []
    with open(TRACKER_LOG, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def summarize_results(rows):
    total = 0
    open_count = 0
    settled_count = 0
    win_count = 0
    loss_count = 0
    push_count = 0

    by_sport = defaultdict(lambda: {"WIN": 0, "LOSS": 0, "PUSH": 0, "OPEN": 0})
    by_strike = defaultdict(lambda: {"WIN": 0, "LOSS": 0, "PUSH": 0, "OPEN": 0})

    for row in rows:
        status = (row.get("status") or "").upper().strip()
        result = (row.get("result") or "").upper().strip()
        sport = (row.get("sport") or "UNKNOWN").strip()
        strike_type = (row.get("strike_type") or "UNKNOWN").strip()

        total += 1

        if status == "OPEN":
            open_count += 1
            by_sport[sport]["OPEN"] += 1
            by_strike[strike_type]["OPEN"] += 1
            continue

        settled_count += 1

        if result == "WIN":
            win_count += 1
            by_sport[sport]["WIN"] += 1
            by_strike[strike_type]["WIN"] += 1
        elif result == "LOSS":
            loss_count += 1
            by_sport[sport]["LOSS"] += 1
            by_strike[strike_type]["LOSS"] += 1
        elif result == "PUSH":
            push_count += 1
            by_sport[sport]["PUSH"] += 1
            by_strike[strike_type]["PUSH"] += 1

    return {
        "total": total,
        "open_count": open_count,
        "settled_count": settled_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "push_count": push_count,
        "by_sport": by_sport,
        "by_strike": by_strike,
    }


def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_overall(summary):
    print_header("OVERALL RESULTS")

    total = summary["total"]
    settled = summary["settled_count"]
    wins = summary["win_count"]
    losses = summary["loss_count"]
    pushes = summary["push_count"]
    open_count = summary["open_count"]

    win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

    print(f"Total tracked:   {total}")
    print(f"Settled:         {settled}")
    print(f"Open:            {open_count}")
    print(f"Wins:            {wins}")
    print(f"Losses:          {losses}")
    print(f"Pushes:          {pushes}")
    print(f"Win %:           {win_pct:.1f}%")
    print(f"Net W-L-P:       {wins}-{losses}-{pushes}")


def print_group_summary(title, group_data):
    print_header(title)
    for key in sorted(group_data.keys()):
        wins = group_data[key]["WIN"]
        losses = group_data[key]["LOSS"]
        pushes = group_data[key]["PUSH"]
        open_count = group_data[key]["OPEN"]
        graded = wins + losses
        win_pct = (wins / graded * 100) if graded > 0 else 0.0

        print(
            f"{key}: "
            f"W {wins} | L {losses} | P {pushes} | Open {open_count} | Win% {win_pct:.1f}%"
        )


def print_recent_results(rows, limit=25):
    print_header(f"MOST RECENT {limit} RESULTS")

    sorted_rows = sorted(
        rows,
        key=lambda r: r.get("timestamp_utc", ""),
        reverse=True,
    )

    for row in sorted_rows[:limit]:
        timestamp = row.get("timestamp_utc", "")
        sport = row.get("sport", "")
        game = row.get("game", "")
        strike_type = row.get("strike_type", "")
        bet_side = row.get("bet_side", "")
        status = row.get("status", "")
        result = row.get("result", "")
        entry_total = row.get("entry_total", "")
        entry_ml = row.get("entry_ml", "")
        entry_spread = row.get("entry_spread", "")
        final_away = row.get("final_away_score", "")
        final_home = row.get("final_home_score", "")

        line_parts = []
        if entry_total not in ("", None):
            line_parts.append(f"total={entry_total}")
        if entry_ml not in ("", None):
            line_parts.append(f"ml={entry_ml}")
        if entry_spread not in ("", None):
            line_parts.append(f"spread={entry_spread}")

        line_text = ", ".join(line_parts) if line_parts else "no line saved"

        print(
            f"{timestamp} | {sport} | {game} | {strike_type} | {bet_side} | "
            f"{status}/{result} | {line_text} | final {final_away}-{final_home}"
        )


def main():
    rows = load_results()
    if not rows:
        return

    summary = summarize_results(rows)

    print_overall(summary)
    print_group_summary("RESULTS BY SPORT", summary["by_sport"])
    print_group_summary("RESULTS BY STRIKE TYPE", summary["by_strike"])
    print_recent_results(rows, limit=25)


if __name__ == "__main__":
    main()
