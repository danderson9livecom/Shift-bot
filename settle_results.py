import csv

TRACKER_FILE = "tracker_log.csv"


def settle_total_bet(entry_total, final_total, bet_side):
    if bet_side == "over":
        if final_total > entry_total:
            return "win", 1
        elif final_total < entry_total:
            return "loss", -1
        return "push", 0

    if bet_side == "under":
        if final_total < entry_total:
            return "win", 1
        elif final_total > entry_total:
            return "loss", -1
        return "push", 0

    return "", ""


def settle_moneyline(bet_side, home_score, away_score):
    if bet_side == "home_ml":
        return ("win", 1) if home_score > away_score else ("loss", -1)
    if bet_side == "away_ml":
        return ("win", 1) if away_score > home_score else ("loss", -1)
    return "", ""


def settle_spread(bet_side, entry_spread, home_score, away_score):
    margin_home = home_score - away_score

    if bet_side == "home_spread":
        adjusted = margin_home + entry_spread
    elif bet_side == "away_spread":
        adjusted = (-margin_home) + entry_spread
    else:
        return "", ""

    if adjusted > 0:
        return "win", 1
    elif adjusted < 0:
        return "loss", -1
    return "push", 0


def settle_pending_rows():
    rows = []

    with open(TRACKER_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["status"] == "pending":
                print(f"\nSettle: {row['sport']} | {row['game']} | {row['trigger_type']}")
                home_score = int(input("Final home score: ").strip())
                away_score = int(input("Final away score: ").strip())

                row["final_home_score"] = home_score
                row["final_away_score"] = away_score

                if row["bet_side"] in ["over", "under"]:
                    final_total = home_score + away_score
                    result, units = settle_total_bet(
                        float(row["entry_total"]),
                        final_total,
                        row["bet_side"]
                    )
                elif row["bet_side"] in ["home_ml", "away_ml"]:
                    result, units = settle_moneyline(
                        row["bet_side"],
                        home_score,
                        away_score
                    )
                elif row["bet_side"] in ["home_spread", "away_spread"]:
                    result, units = settle_spread(
                        row["bet_side"],
                        float(row["entry_spread"]),
                        home_score,
                        away_score
                    )
                else:
                    result, units = "", ""

                row["result"] = result
                row["units"] = units
                row["status"] = "settled"

            rows.append(row)

    if rows:
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print("\nDone settling results.")


if __name__ == "__main__":
    settle_pending_rows()
