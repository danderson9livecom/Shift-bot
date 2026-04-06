import csv
import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load .env from the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("ODDS_API_KEY", "").strip()
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
TRACKER_FILE = os.path.join(BASE_DIR, "tracker_log.csv")
POLL_INTERVAL = 60

SPORT_KEYS = {
    "MLB": "baseball_mlb",
    "NBA": "basketball_nba",
    "NHL": "icehockey_nhl"
}

TRIGGER_FIELDS = [
    "id",
    "sport",
    "event_id",
    "game",
    "trigger_type",
    "bet_side",
    "opening_total",
    "entry_total",
    "opening_home_ml",
    "opening_away_ml",
    "entry_home_ml",
    "entry_away_ml",
    "entry_odds",
    "entry_spread",
    "entry_time",
    "status",
    "final_home_score",
    "final_away_score",
    "result",
    "units"
]


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        raise FileNotFoundError(f"watchlist.json not found at {WATCHLIST_FILE}")

    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "games" not in data or not isinstance(data["games"], list):
        raise ValueError("watchlist.json must contain a top-level 'games' list.")

    return data["games"]


def init_tracker_csv():
    if not os.path.exists(TRACKER_FILE) or os.path.getsize(TRACKER_FILE) == 0:
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TRIGGER_FIELDS)
            writer.writeheader()


def existing_trigger_ids():
    seen = set()

    if not os.path.exists(TRACKER_FILE):
        return seen

    with open(TRACKER_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trigger_id = row.get("id", "").strip()
            if trigger_id:
                seen.add(trigger_id)

    return seen


def log_trigger(row):
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRIGGER_FIELDS)
        writer.writerow(row)


def fetch_odds_for_sport(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso"
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def find_matching_event(events, away_team, home_team):
    for event in events:
        if event.get("away_team") == away_team and event.get("home_team") == home_team:
            return event
    return None


def choose_bookmaker(event):
    bookmakers = event.get("bookmakers", [])
    if not bookmakers:
        return None

    preferred = ["draftkings", "fanduel", "betmgm", "caesars", "espnbet", "betrivers"]
    bm_map = {b["key"]: b for b in bookmakers}

    for key in preferred:
        if key in bm_map:
            return bm_map[key]

    return bookmakers[0]


def extract_market_data(event):
    bookmaker = choose_bookmaker(event)
    if not bookmaker:
        return {
            "live_total": None,
            "home_ml": None,
            "away_ml": None,
            "home_spread": None,
            "away_spread": None
        }

    home_team = event["home_team"]
    away_team = event["away_team"]

    live_total = None
    home_ml = None
    away_ml = None
    home_spread = None
    away_spread = None

    for market in bookmaker.get("markets", []):
        if market.get("key") == "totals":
            for outcome in market.get("outcomes", []):
                if outcome.get("point") is not None:
                    live_total = float(outcome["point"])
                    break

        elif market.get("key") == "h2h":
            for outcome in market.get("outcomes", []):
                if outcome.get("name") == home_team:
                    home_ml = int(outcome["price"])
                elif outcome.get("name") == away_team:
                    away_ml = int(outcome["price"])

        elif market.get("key") == "spreads":
            for outcome in market.get("outcomes", []):
                if outcome.get("name") == home_team and outcome.get("point") is not None:
                    home_spread = float(outcome["point"])
                elif outcome.get("name") == away_team and outcome.get("point") is not None:
                    away_spread = float(outcome["point"])

    return {
        "live_total": live_total,
        "home_ml": home_ml,
        "away_ml": away_ml,
        "home_spread": home_spread,
        "away_spread": away_spread
    }


def build_trigger_row(game_cfg, event, trigger_type, bet_side, market_data, entry_odds="", entry_spread=""):
    return {
        "id": f"{event['id']}|{trigger_type}",
        "sport": game_cfg["sport"],
        "event_id": event["id"],
        "game": f"{game_cfg['away_team']} @ {game_cfg['home_team']}",
        "trigger_type": trigger_type,
        "bet_side": bet_side,
        "opening_total": game_cfg.get("opening_total", ""),
        "entry_total": market_data["live_total"] if market_data["live_total"] is not None else "",
        "opening_home_ml": "",
        "opening_away_ml": "",
        "entry_home_ml": market_data["home_ml"] if market_data["home_ml"] is not None else "",
        "entry_away_ml": market_data["away_ml"] if market_data["away_ml"] is not None else "",
        "entry_odds": entry_odds,
        "entry_spread": entry_spread,
        "entry_time": datetime.utcnow().isoformat(),
        "status": "pending",
        "final_home_score": "",
        "final_away_score": "",
        "result": "",
        "units": ""
    }


def check_total_triggers(game_cfg, event, market_data, seen_ids):
    rows = []
    live_total = market_data["live_total"]

    if live_total is None:
        return rows

    total_rules = [
        ("UNDER_1", "under", game_cfg["under_1"], live_total >= game_cfg["under_1"]),
        ("UNDER_2", "under", game_cfg["under_2"], live_total >= game_cfg["under_2"]),
        ("OVER_1", "over", game_cfg["over_1"], live_total <= game_cfg["over_1"]),
        ("OVER_2", "over", game_cfg["over_2"], live_total <= game_cfg["over_2"]),
    ]

    for trigger_name, bet_side, _, fired in total_rules:
        trigger_id = f"{event['id']}|{trigger_name}"
        if fired and trigger_id not in seen_ids:
            row = build_trigger_row(
                game_cfg=game_cfg,
                event=event,
                trigger_type=trigger_name,
                bet_side=bet_side,
                market_data=market_data,
                entry_odds=-110,
                entry_spread=""
            )
            rows.append(row)
            seen_ids.add(trigger_id)

    return rows


def check_moneyline_buy_low(game_cfg, event, market_data, seen_ids):
    rows = []
    buy_low_team = game_cfg.get("buy_low_team", "").strip()
    if not buy_low_team:
        return rows

    trigger_id = f"{event['id']}|BUY_LOW"
    if trigger_id in seen_ids:
        return rows

    min_odds = game_cfg.get("buy_low_min")
    max_odds = game_cfg.get("buy_low_max")

    if min_odds is None or max_odds is None:
        return rows

    if buy_low_team == game_cfg["home_team"]:
        current_ml = market_data["home_ml"]
        bet_side = "home_ml"
    else:
        current_ml = market_data["away_ml"]
        bet_side = "away_ml"

    if current_ml is None:
        return rows

    if min_odds <= current_ml <= max_odds:
        row = build_trigger_row(
            game_cfg=game_cfg,
            event=event,
            trigger_type="BUY_LOW",
            bet_side=bet_side,
            market_data=market_data,
            entry_odds=current_ml,
            entry_spread=""
        )
        rows.append(row)
        seen_ids.add(trigger_id)

    return rows


def check_nba_spread_buy_low(game_cfg, event, market_data, seen_ids):
    rows = []
    buy_low_team = game_cfg.get("buy_low_team", "").strip()
    if not buy_low_team:
        return rows

    trigger_id = f"{event['id']}|BUY_LOW_SPREAD"
    if trigger_id in seen_ids:
        return rows

    min_spread = game_cfg.get("buy_low_spread_min")
    max_spread = game_cfg.get("buy_low_spread_max")

    if min_spread is None or max_spread is None:
        return rows

    if buy_low_team == game_cfg["home_team"]:
        current_spread = market_data["home_spread"]
        bet_side = "home_spread"
    else:
        current_spread = market_data["away_spread"]
        bet_side = "away_spread"

    if current_spread is None:
        return rows

    if min_spread <= current_spread <= max_spread:
        row = build_trigger_row(
            game_cfg=game_cfg,
            event=event,
            trigger_type="BUY_LOW_SPREAD",
            bet_side=bet_side,
            market_data=market_data,
            entry_odds=-110,
            entry_spread=current_spread
        )
        rows.append(row)
        seen_ids.add(trigger_id)

    return rows


def main():
    if not API_KEY:
        raise ValueError(
            "Missing ODDS_API_KEY environment variable. "
            "Make sure .env is in the shift-bot folder and contains ODDS_API_KEY=your_key"
        )

    watchlist = load_watchlist()
    init_tracker_csv()

    print("Tracking watchlist games...")

    while True:
        try:
            seen_ids = existing_trigger_ids()

            grouped = {"MLB": [], "NBA": [], "NHL": []}
            for game in watchlist:
                grouped[game["sport"]].append(game)

            for sport, sport_games in grouped.items():
                if not sport_games:
                    continue

                print(f"\nChecking {sport}...")
                events = fetch_odds_for_sport(SPORT_KEYS[sport])

                for game_cfg in sport_games:
                    event = find_matching_event(
                        events,
                        game_cfg["away_team"],
                        game_cfg["home_team"]
                    )

                    if not event:
                        print(f"[NOT FOUND] {game_cfg['away_team']} @ {game_cfg['home_team']}")
                        continue

                    market_data = extract_market_data(event)

                    print(
                        f"[FOUND] {game_cfg['away_team']} @ {game_cfg['home_team']} | "
                        f"live_total={market_data['live_total']} | "
                        f"home_ml={market_data['home_ml']} | away_ml={market_data['away_ml']} | "
                        f"home_spread={market_data['home_spread']} | away_spread={market_data['away_spread']}"
                    )

                    trigger_rows = []
                    trigger_rows.extend(check_total_triggers(game_cfg, event, market_data, seen_ids))

                    if sport in ["MLB", "NHL"]:
                        trigger_rows.extend(check_moneyline_buy_low(game_cfg, event, market_data, seen_ids))
                    elif sport == "NBA":
                        trigger_rows.extend(check_nba_spread_buy_low(game_cfg, event, market_data, seen_ids))

                    for row in trigger_rows:
                        log_trigger(row)
                        print(
                            f"[TRIGGER] {row['sport']} | {row['game']} | "
                            f"{row['trigger_type']} | total={row['entry_total']} | "
                            f"odds={row['entry_odds']} | spread={row['entry_spread']}"
                        )

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
