import os
import time
import json
import statistics
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from twilio.rest import Client
from dotenv import load_dotenv


load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

RUN_BOT = os.getenv("RUN_BOT", "true").lower()

if RUN_BOT != "true":
    print("Bot disabled by RUN_BOT setting.")
    exit()

if not ODDS_API_KEY:
    raise RuntimeError("Missing ODDS_API_KEY")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


TZ = ZoneInfo("America/Phoenix")

ACTIVE_CHECK_SECONDS = 30
DORMANT_CHECK_SECONDS = 900
PREGAME_ALERT_CHECK_SECONDS = 300

START_ALERT_MINUTES_BEFORE = 15
NOT_FOUND_LIMIT = 3

STATE_FILE = "watch_state.json"
RESULTS_FILE = "strike_results.jsonl"


WATCHLIST = [
    {
        "id": "braves_marlins",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Braves @ Marlins",
        "away": "Braves",
        "home": "Marlins",
        "start_time": "2026-05-19 13:10",
        "total_triggers": {
            "over": 6.5,
            "under": 11.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "orioles_rays",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Orioles @ Rays",
        "away": "Orioles",
        "home": "Rays",
        "start_time": "2026-05-19 15:40",
        "total_triggers": {
            "over": 5.5,
            "under": 10.0,
        },
        "spread_triggers": [],
    },
    {
        "id": "reds_phillies",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Reds @ Phillies",
        "away": "Reds",
        "home": "Phillies",
        "start_time": "2026-05-19 15:40",
        "total_triggers": {
            "over": 6.5,
            "under": 11.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "guardians_tigers",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Guardians @ Tigers",
        "away": "Guardians",
        "home": "Tigers",
        "start_time": "2026-05-19 15:40",
        "total_triggers": {
            "over": 6.0,
            "under": 10.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "mets_nationals",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Mets @ Nationals",
        "away": "Mets",
        "home": "Nationals",
        "start_time": "2026-05-19 15:45",
        "total_triggers": {
            "over": 7.0,
            "under": 12.0,
        },
        "spread_triggers": [],
    },
    {
        "id": "bluejays_yankees",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Blue Jays @ Yankees",
        "away": "Blue Jays",
        "home": "Yankees",
        "start_time": "2026-05-19 16:05",
        "total_triggers": {
            "over": 6.0,
            "under": 11.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "redsox_royals",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Red Sox @ Royals",
        "away": "Red Sox",
        "home": "Royals",
        "start_time": "2026-05-19 16:40",
        "total_triggers": {
            "over": 5.0,
            "under": 9.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "astros_twins",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Astros @ Twins",
        "away": "Astros",
        "home": "Twins",
        "start_time": "2026-05-19 16:40",
        "total_triggers": {
            "over": 6.5,
            "under": 12.0,
        },
        "spread_triggers": [],
    },
    {
        "id": "brewers_cubs",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Brewers @ Cubs",
        "away": "Brewers",
        "home": "Cubs",
        "start_time": "2026-05-19 16:40",
        "total_triggers": {
            "over": 5.5,
            "under": 10.0,
        },
        "spread_triggers": [],
    },
    {
        "id": "pirates_cardinals",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Pirates @ Cardinals",
        "away": "Pirates",
        "home": "Cardinals",
        "start_time": "2026-05-19 16:45",
        "total_triggers": {
            "over": 5.5,
            "under": 10.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "rangers_rockies",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Rangers @ Rockies",
        "away": "Rangers",
        "home": "Rockies",
        "start_time": "2026-05-19 17:40",
        "total_triggers": {
            "over": 7.5,
            "under": 14.0,
        },
        "spread_triggers": [],
    },
    {
        "id": "athletics_angels",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Athletics @ Angels",
        "away": "Athletics",
        "home": "Angels",
        "start_time": "2026-05-19 18:38",
        "total_triggers": {
            "over": 6.5,
            "under": 12.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "whitesox_mariners",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "White Sox @ Mariners",
        "away": "White Sox",
        "home": "Mariners",
        "start_time": "2026-05-19 18:40",
        "total_triggers": {
            "over": 5.0,
            "under": 9.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "dodgers_padres",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Dodgers @ Padres",
        "away": "Dodgers",
        "home": "Padres",
        "start_time": "2026-05-19 18:40",
        "total_triggers": {
            "over": 6.0,
            "under": 12.5,
        },
        "spread_triggers": [],
    },
    {
        "id": "giants_diamondbacks",
        "sport_key": "baseball_mlb",
        "league": "MLB",
        "game": "Giants @ Diamondbacks",
        "away": "Giants",
        "home": "Diamondbacks",
        "start_time": "2026-05-19 18:40",
        "total_triggers": {
            "over": 6.5,
            "under": 11.5,
        },
        "spread_triggers": [],
    },

    {
        "id": "cavaliers_knicks",
        "sport_key": "basketball_nba",
        "league": "NBA",
        "game": "Cavaliers @ Knicks",
        "away": "Cavaliers",
        "home": "Knicks",
        "start_time": "2026-05-19 17:00",
        "total_triggers": {
            "over": 209.5,
            "under": 224.5,
        },
        "spread_triggers": [
            {
                "team": "Knicks",
                "condition": "at_or_above",
                "point": 4.5,
                "message": "BUY Knicks live spread",
            }
        ],
    },
    {
        "id": "tempo_mercury",
        "sport_key": "basketball_wnba",
        "league": "WNBA",
        "game": "Tempo @ Mercury",
        "away": "Tempo",
        "home": "Mercury",
        "start_time": "2026-05-19 19:00",
        "total_triggers": {
            "over": 164.5,
            "under": 181.5,
        },
        "spread_triggers": [
            {
                "team": "Mercury",
                "condition": "at_or_above",
                "point": -2.5,
                "message": "BUY Phoenix live spread",
            }
        ],
    },
]


def now_phoenix():
    return datetime.now(TZ)


def parse_start_time(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)


def normalize(value):
    return (
        value.lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("blue jays", "blue jays")
        .replace("d backs", "diamondbacks")
        .replace("dbacks", "diamondbacks")
        .replace("phoenix", "")
        .replace("new york", "")
        .replace("cleveland", "")
        .replace("toronto", "")
        .strip()
    )


def team_match(expected, actual):
    expected_norm = normalize(expected)
    actual_norm = normalize(actual)

    return expected_norm in actual_norm or actual_norm in expected_norm


def send_sms(message):
    client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER,
    )
    print(f"TEXT SENT: {message}")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_result(record):
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def initialize_state():
    state = load_state()

    for game in WATCHLIST:
        if game["id"] not in state:
            state[game["id"]] = {
                "status": "DORMANT",
                "alert_sent": False,
                "start_alert_sent": False,
                "not_found_count": 0,
                "trigger": None,
                "trigger_time": None,
                "trigger_value": None,
                "stop_reason": None,
            }

        if "start_alert_sent" not in state[game["id"]]:
            state[game["id"]]["start_alert_sent"] = False

    save_state(state)
    return state


def maybe_send_start_alert(game, game_state):
    current_time = now_phoenix()
    start_time = parse_start_time(game["start_time"])

    minutes_until_start = (start_time - current_time).total_seconds() / 60

    if 0 <= minutes_until_start <= START_ALERT_MINUTES_BEFORE:
        if not game_state.get("start_alert_sent", False):
            start_text = start_time.strftime("%I:%M %p").lstrip("0")

            message = (
                f"SHIFT BOT START ALERT\n"
                f"{game['game']} starts at {start_text} Arizona time.\n"
                f"Monitoring activates at game start.\n"
            )

            if game.get("total_triggers"):
                message += (
                    f"OVER total strike: {game['total_triggers']['over']} or lower\n"
                    f"UNDER total strike: {game['total_triggers']['under']} or higher\n"
                )

            for spread in game.get("spread_triggers", []):
                message += f"SPREAD strike: {spread['message']} at {spread['point']} or better\n"

            send_sms(message)
            game_state["start_alert_sent"] = True
            print(f"START ALERT SENT: {game['game']}")


def fetch_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals,spreads",
        "oddsFormat": "american",
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(f"Odds API error for {sport_key}: {response.status_code} {response.text}")

    return response.json()


def fetch_scores(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores"
    params = {
        "apiKey": ODDS_API_KEY,
        "daysFrom": 1,
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(f"Scores API error for {sport_key}: {response.status_code} {response.text}")

    return response.json()


def find_event(game, odds_events):
    for event in odds_events:
        home = event.get("home_team", "")
        away = event.get("away_team", "")

        if team_match(game["home"], home) and team_match(game["away"], away):
            return event

    return None


def find_score_event(game, score_events):
    for event in score_events:
        home = event.get("home_team", "")
        away = event.get("away_team", "")

        if team_match(game["home"], home) and team_match(game["away"], away):
            return event

    return None


def is_game_final(game, score_events):
    event = find_score_event(game, score_events)

    if not event:
        return False

    return bool(event.get("completed", False))


def extract_live_total(event):
    totals = []

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "totals":
                continue

            for outcome in market.get("outcomes", []):
                if outcome.get("name", "").lower() in ["over", "under"]:
                    point = outcome.get("point")
                    if point is not None:
                        totals.append(float(point))

    if not totals:
        return None

    return statistics.median(totals)


def extract_team_spread(event, team_name):
    spreads = []

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "spreads":
                continue

            for outcome in market.get("outcomes", []):
                outcome_name = outcome.get("name", "")
                point = outcome.get("point")

                if point is None:
                    continue

                if team_match(team_name, outcome_name):
                    spreads.append(float(point))

    if not spreads:
        return None

    return statistics.median(spreads)


def get_active_games(state):
    current_time = now_phoenix()
    active_games = []

    for game in WATCHLIST:
        game_state = state[game["id"]]

        if game_state["status"] == "DONE":
            continue

        start_time = parse_start_time(game["start_time"])

        maybe_send_start_alert(game, game_state)

        if current_time >= start_time:
            active_games.append(game)
        else:
            game_state["status"] = "DORMANT"

    return active_games


def next_sleep_seconds(state):
    current_time = now_phoenix()
    next_start = None

    for game in WATCHLIST:
        game_state = state[game["id"]]

        if game_state["status"] == "DONE":
            continue

        start_time = parse_start_time(game["start_time"])

        if start_time > current_time:
            if next_start is None or start_time < next_start:
                next_start = start_time

    if next_start is None:
        return DORMANT_CHECK_SECONDS

    seconds_until_start = int((next_start - current_time).total_seconds())

    if seconds_until_start <= START_ALERT_MINUTES_BEFORE * 60:
        return min(PREGAME_ALERT_CHECK_SECONDS, max(30, seconds_until_start))

    return min(DORMANT_CHECK_SECONDS, max(300, seconds_until_start - START_ALERT_MINUTES_BEFORE * 60))


def print_dormant_status(state):
    current_time = now_phoenix()

    for game in WATCHLIST:
        game_state = state[game["id"]]

        if game_state["status"] == "DONE":
            print(f"DONE: {game['game']} | Reason: {game_state.get('stop_reason')}")
            continue

        start_time = parse_start_time(game["start_time"])

        if current_time < start_time:
            start_text = start_time.strftime("%I:%M %p").lstrip("0")
            print(f"DORMANT: {game['game']} starts at {start_text}")
        else:
            print(f"WAITING ACTIVE CHECK: {game['game']}")


def finish_game_with_strike(game, game_state, market, direction, value, strike_message):
    current_time = now_phoenix()

    message = (
        f"STRIKE ALERT\n"
        f"{game['game']}\n"
        f"{strike_message}\n"
        f"Current value: {value}"
    )

    send_sms(message)

    game_state["alert_sent"] = True
    game_state["status"] = "DONE"
    game_state["trigger"] = f"{market}_{direction}"
    game_state["trigger_time"] = current_time.isoformat()
    game_state["trigger_value"] = value
    game_state["stop_reason"] = "strike hit"

    log_result({
        "game": game["game"],
        "date": current_time.strftime("%Y-%m-%d"),
        "league": game["league"],
        "market": market,
        "direction": direction,
        "value_at_alert": value,
        "alert_time": current_time.isoformat(),
        "status": "PENDING_RESULT",
    })

    print(f"TEXT SENT / DONE: {game['game']} | {market} | {direction} | {value}")


def check_total_trigger(game, game_state, event):
    total_triggers = game.get("total_triggers")

    if not total_triggers:
        return False

    live_total = extract_live_total(event)

    if live_total is None:
        print(f"NO TOTAL FOUND: {game['game']}")
        return False

    print(
        f"TOTAL CHECK: {game['game']} | "
        f"Live total: {live_total} | "
        f"Over <= {total_triggers['over']} | "
        f"Under >= {total_triggers['under']}"
    )

    if live_total <= total_triggers["over"]:
        finish_game_with_strike(
            game,
            game_state,
            "live_total",
            "OVER",
            live_total,
            f"HIT OVER live total at {total_triggers['over']} or lower",
        )
        return True

    if live_total >= total_triggers["under"]:
        finish_game_with_strike(
            game,
            game_state,
            "live_total",
            "UNDER",
            live_total,
            f"HIT UNDER live total at {total_triggers['under']} or higher",
        )
        return True

    return False


def check_spread_trigger(game, game_state, event):
    for spread in game.get("spread_triggers", []):
        team = spread["team"]
        live_spread = extract_team_spread(event, team)

        if live_spread is None:
            print(f"NO SPREAD FOUND: {game['game']} | {team}")
            continue

        print(
            f"SPREAD CHECK: {game['game']} | "
            f"{team} live spread: {live_spread} | "
            f"Strike: {spread['point']} or better"
        )

        if spread["condition"] == "at_or_above":
            if live_spread >= spread["point"]:
                finish_game_with_strike(
                    game,
                    game_state,
                    "live_spread",
                    team,
                    live_spread,
                    spread["message"],
                )
                return True

        if spread["condition"] == "at_or_below":
            if live_spread <= spread["point"]:
                finish_game_with_strike(
                    game,
                    game_state,
                    "live_spread",
                    team,
                    live_spread,
                    spread["message"],
                )
                return True

    return False


def monitor():
    state = initialize_state()

    print("SHIFT bot started.")
    print(f"Phoenix time: {now_phoenix().strftime('%Y-%m-%d %H:%M:%S')}")
    send_sms("SHIFT bot started. MLB, NBA, and WNBA monitoring active. Pregame alerts enabled.")

    while True:
        active_games = get_active_games(state)
        save_state(state)

        remaining_games = [
            game for game in WATCHLIST
            if state[game["id"]]["status"] != "DONE"
        ]

        if not remaining_games:
            print("All games are DONE. Bot shutting down.")
            break

        if not active_games:
            print_dormant_status(state)
            sleep_seconds = next_sleep_seconds(state)
            print(f"No active games. Sleeping {sleep_seconds} seconds to save credits.")
            time.sleep(sleep_seconds)
            continue

        print(f"ACTIVE MODE: {len(active_games)} game(s) active.")

        active_sport_keys = sorted(set(game["sport_key"] for game in active_games))

        odds_by_sport = {}
        scores_by_sport = {}

        for sport_key in active_sport_keys:
            try:
                odds_by_sport[sport_key] = fetch_odds(sport_key)
                scores_by_sport[sport_key] = fetch_scores(sport_key)
            except Exception as e:
                print(f"API error for {sport_key}: {e}")
                odds_by_sport[sport_key] = []
                scores_by_sport[sport_key] = []

        for game in active_games:
            game_state = state[game["id"]]

            if game_state["status"] == "DONE":
                continue

            game_state["status"] = "ACTIVE"

            odds_events = odds_by_sport.get(game["sport_key"], [])
            score_events = scores_by_sport.get(game["sport_key"], [])

            if is_game_final(game, score_events):
                game_state["status"] = "DONE"
                game_state["stop_reason"] = "game final"
                print(f"DONE: {game['game']} final.")
                continue

            event = find_event(game, odds_events)

            if not event:
                game_state["not_found_count"] += 1
                print(
                    f"NOT FOUND: {game['game']} "
                    f"({game_state['not_found_count']}/{NOT_FOUND_LIMIT})"
                )

                if game_state["not_found_count"] >= NOT_FOUND_LIMIT:
                    game_state["status"] = "DONE"
                    game_state["stop_reason"] = "game not found repeatedly"
                    print(f"DONE: {game['game']} stopped after repeated not found.")

                continue

            game_state["not_found_count"] = 0

            if check_total_trigger(game, game_state, event):
                continue

            if check_spread_trigger(game, game_state, event):
                continue

        save_state(state)

        remaining = [
            game["game"]
            for game in WATCHLIST
            if state[game["id"]]["status"] != "DONE"
        ]

        print(f"Still monitoring/waiting on {len(remaining)} game(s).")
        time.sleep(ACTIVE_CHECK_SECONDS)


if __name__ == "__main__":
    monitor()
