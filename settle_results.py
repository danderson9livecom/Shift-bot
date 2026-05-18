import csv
import os
from datetime import datetime, timezone

import requests

TRACKER_LOG = "tracker_log.csv"

SPORT_CONFIG = {
    "MLB": {
        "espn_url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    },
    "NBA": {
        "espn_url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    },
    "NHL": {
        "espn_url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    },
}


def normalize_name(name):
    return (
        str(name).lower()
        .replace(".", "")
        .replace(",", "")
        .replace("&", "and")
        .replace("  ", " ")
        .strip()
    )


def build_matchup_key(away_team, home_team):
    return f"{normalize_name(away_team)} @ {normalize_name(home_team)}"


def load_rows():
    if not os.path.exists(TRACKER_LOG):
        print("tracker_log.csv not found.")
        return [], []

    with open(TRACKER_LOG, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    return rows, fieldnames


def save_rows(rows, fieldnames):
    with open(TRACKER_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_scoreboard_for_sport(sport_name, sport_cfg):
    try:
        r = requests.get(sport_cfg["espn_url"], timeout=20)
        r.raise_for_status()
        data = r.json()
        events = data.get("events", [])
        print(f"{sport_name}: loaded {len(events)} scoreboard events")
        return events
    except Exception as e:
        print(f"ERROR loading scoreboard for {sport_name}: {e}")
        return []


def parse_espn_competitor_data(event):
    competitions = event.get("competitions", [])
    if not competitions:
        return None

    comp = competitions[0]
    competitors = comp.get("competitors", [])

    home = None
    away = None

    for c in competitors:
        team = c.get("team", {})
        score_raw = c.get("score", "0")
        try:
            score_val = int(score_raw)
        except Exception:
            score_val = 0

        data = {
            "name": team.get("displayName"),
            "score": score_val,
            "homeAway": c.get("homeAway"),
        }

        if c.get("homeAway") == "home":
            home = data
        elif c.get("homeAway") == "away":
            away = data

    if not home or not away:
        return None

    status = comp.get("status", {})
    type_info = status.get("type", {})

    return {
        "home_team": home["name"],
        "away_team": away["name"],
        "home_score": home["score"],
        "away_score": away["score"],
        "state": type_info.get("state"),
        "short_detail": type_info.get("shortDetail"),
    }


def build_score_index():
    score_index = {}

    for sport_name, sport_cfg in SPORT_CONFIG.items():
        events = fetch_scoreboard_for_sport(sport_name, sport_cfg)
        for event in events:
            parsed = parse_espn_competitor_data(event)
            if not parsed:
                continue

            key = build_matchup_key(parsed["away_team"], parsed["home_team"])
            parsed["sport"] = sport_name
            score_index[key] = parsed

    return score_index


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def grade_total_over(entry_total, final_total):
    if final_total > entry_total:
        return "WIN"
    if final_total < entry_total:
        return "LOSS"
    return "PUSH"


def grade_total_under(entry_total, final_total):
    if final_total < entry_total:
        return "WIN"
    if final_total > entry_total:
        return "LOSS"
    return "PUSH"


def grade_moneyline(team, home_team, away_team, home_score, away_score):
    if team == home_team:
        return "WIN" if home_score > away_score else "LOSS"
    if team == away_team:
        return "WIN" if away_score > home_score else "LOSS"
    return "LOSS"


def grade_spread(team, spread, home_team, away_team, home_score, away_score):
    if spread is None:
        return None

    if team == home_team:
        adjusted_diff = (home_score + spread) - away_score
    elif team == away_team:
        adjusted_diff = (away_score + spread) - home_score
    else:
        return None

    if adjusted_diff > 0:
        return "WIN"
    if adjusted_diff < 0:
        return "LOSS"
    return "PUSH"


def settle_rows(rows, score_index):
    settled_count = 0

    for row in rows:
        if (row.get("status") or "").upper() != "OPEN":
            continue

        matchup_key = build_matchup_key(row.get("away_team", ""), row.get("home_team", ""))
        score_row = score_index.get(matchup_key)

        if not score_row:
            continue

        if score_row.get("state") != "post":
            continue

        home_score = score_row["home_score"]
        away_score = score_row["away_score"]
        final_total = home_score + away_score

        strike_type = row.get("strike_type", "")
        bet_side = row.get("bet_side", "")
        team = row.get("team", "")
        home_team = row.get("home_team", "")
        away_team = row.get("away_team", "")
        entry_total = safe_float(row.get("entry_total"))
        entry_spread = safe_float(row.get("entry_spread"))

        result = None

        if strike_type == "fast_start_under" and bet_side == "UNDER" and entry_total is not None:
            result = grade_total_under(entry_total, final_total)

        elif strike_type == "slow_start_over" and bet_side == "OVER" and entry_total is not None:
            result = grade_total_over(entry_total, final_total)

        elif strike_type in ["buy_low_ml", "buy_low_deficit"] and team:
            result = grade_moneyline(team, home_team, away_team, home_score, away_score)

        elif strike_type == "spread_swing" and bet_side == "SPREAD":
            result = grade_spread(team, entry_spread, home_team, away_team, home_score, away_score)

        if result:
            row["final_away_score"] = str(away_score)
            row["final_home_score"] = str(home_score)
            row["result"] = result
            row["status"] = "SETTLED"
            row["settled_timestamp"] = datetime.now(timezone.utc).isoformat()
            settled_count += 1

    return settled_count


def main():
    rows, fieldnames = load_rows()
    if not rows:
        return

    score_index = build_score_index()
    settled_count = settle_rows(rows, score_index)
    save_rows(rows, fieldnames)

    print(f"Settled {settled_count} open strikes.")


if __name__ == "__main__":
    main()
