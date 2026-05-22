import os
import json
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from twilio.rest import Client

# =========================
# ENV VARIABLES REQUIRED
# =========================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

ARIZONA = ZoneInfo("America/Phoenix")
STATE_FILE = "shift_alert_state.json"

CHECK_INTERVAL_SECONDS = 30
PRE_START_LOOKAHEAD_MINUTES = 5
NOT_FOUND_GRACE_MINUTES = 30

# =========================
# GAME CONFIG
# Times are Arizona time
# =========================
GAMES = [
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Astros @ Cubs",
        "away": "Houston Astros",
        "home": "Chicago Cubs",
        "start_time": "2026-05-22 11:20",
        "opening_total": 7.0,
        "over_strike": 5.0,
        "under_strike": 9.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Guardians @ Phillies",
        "away": "Cleveland Guardians",
        "home": "Philadelphia Phillies",
        "start_time": "2026-05-22 15:45",
        "opening_total": 6.5,
        "over_strike": 4.0,
        "under_strike": 8.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Cardinals @ Reds",
        "away": "St. Louis Cardinals",
        "home": "Cincinnati Reds",
        "start_time": "2026-05-22 15:40",
        "opening_total": 9.0,
        "over_strike": 7.0,
        "under_strike": 12.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Rays @ Yankees",
        "away": "Tampa Bay Rays",
        "home": "New York Yankees",
        "start_time": "2026-05-22 16:05",
        "opening_total": 8.5,
        "over_strike": 6.0,
        "under_strike": 10.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Pirates @ Blue Jays",
        "away": "Pittsburgh Pirates",
        "home": "Toronto Blue Jays",
        "start_time": "2026-05-22 16:07",
        "opening_total": 8.5,
        "over_strike": 6.5,
        "under_strike": 10.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Twins @ Red Sox",
        "away": "Minnesota Twins",
        "home": "Boston Red Sox",
        "start_time": "2026-05-22 16:10",
        "opening_total": 8.0,
        "over_strike": 5.5,
        "under_strike": 10.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Tigers @ Orioles",
        "away": "Detroit Tigers",
        "home": "Baltimore Orioles",
        "start_time": "2026-05-22 16:05",
        "opening_total": 8.5,
        "over_strike": 6.5,
        "under_strike": 11.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Nationals @ Braves",
        "away": "Washington Nationals",
        "home": "Atlanta Braves",
        "start_time": "2026-05-22 16:20",
        "opening_total": 9.0,
        "over_strike": 7.0,
        "under_strike": 12.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Dodgers @ Brewers",
        "away": "Los Angeles Dodgers",
        "home": "Milwaukee Brewers",
        "start_time": "2026-05-22 17:10",
        "opening_total": 8.0,
        "over_strike": 5.5,
        "under_strike": 10.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Mariners @ Royals",
        "away": "Seattle Mariners",
        "home": "Kansas City Royals",
        "start_time": "2026-05-22 17:10",
        "opening_total": 7.5,
        "over_strike": 4.5,
        "under_strike": 9.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Rangers @ Angels",
        "away": "Texas Rangers",
        "home": "Los Angeles Angels",
        "start_time": "2026-05-22 18:38",
        "opening_total": 8.5,
        "over_strike": 5.5,
        "under_strike": 10.5,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Athletics @ Padres",
        "away": "Athletics",
        "home": "San Diego Padres",
        "start_time": "2026-05-22 18:40",
        "opening_total": 8.0,
        "over_strike": 5.5,
        "under_strike": 10.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "Rockies @ Diamondbacks",
        "away": "Colorado Rockies",
        "home": "Arizona Diamondbacks",
        "start_time": "2026-05-22 18:40",
        "opening_total": 9.0,
        "over_strike": 6.5,
        "under_strike": 11.0,
    },
    {
        "league": "MLB",
        "sport_key": "baseball_mlb",
        "game": "White Sox @ Giants",
        "away": "Chicago White Sox",
        "home": "San Francisco Giants",
        "start_time": "2026-05-22 19:15",
        "opening_total": 7.0,
        "over_strike": 3.5,
        "under_strike": 8.5,
    },

    # NBA
    {
        "league": "NBA",
        "sport_key": "basketball_nba",
        "game": "Spurs @ Thunder",
        "away": "San Antonio Spurs",
        "home": "Oklahoma City Thunder",
        "start_time": "2026-05-22 17:30",
        "spread_team": "San Antonio Spurs",
        "spread_strike": 4.5,
        "spread_best_value": 6.5,
        "over_strike": 209.5,
        "under_strike": 229.5,
    },

    # WNBA
    {
        "league": "WNBA",
        "sport_key": "basketball_wnba",
        "game": "Fever @ Valkyries",
        "away": "Indiana Fever",
        "home": "Golden State Valkyries",
        "start_time": "2026-05-22 19:00",
        "over_strike": 162.5,
        "under_strike": None,
    },
    {
        "league": "WNBA",
        "sport_key": "basketball_wnba",
        "game": "Dream live spread",
        "away": "Atlanta Dream",
        "home": "",
        "start_time": "2026-05-22 16:30",
        "spread_team": "Atlanta Dream",
        "spread_strike": -2.5,
    },
    {
        "league": "WNBA",
        "sport_key": "basketball_wnba",
        "game": "Seattle live spread",
        "away": "Seattle Storm",
        "home": "",
        "start_time": "2026-05-22 19:00",
        "spread_team": "Seattle Storm",
        "spread_strike": 2.5,
    },
    {
        "league": "WNBA",
        "sport_key": "basketball_wnba",
        "game": "Sun @ Storm",
        "away": "Connecticut Sun",
        "home": "Seattle Storm",
        "start_time": "2026-05-22 19:00",
        "over_strike": None,
        "under_strike": 171.5,
    },
]


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_sms(message):
    print(message)

    if not all([
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_FROM_NUMBER,
        ALERT_TO_NUMBER
    ]):
        print("Twilio env vars missing. SMS not sent.")
        return

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )


def parse_start_time(game):
    return datetime.strptime(game["start_time"], "%Y-%m-%d %H:%M").replace(tzinfo=ARIZONA)


def fetch_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals,spreads",
        "bookmakers": "draftkings",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_scores(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores"
    params = {
        "apiKey": ODDS_API_KEY,
        "daysFrom": 1,
        "dateFormat": "iso",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def names_match(api_event, game):
    api_home = api_event.get("home_team", "").lower()
    api_away = api_event.get("away_team", "").lower()

    target_home = game.get("home", "").lower()
    target_away = game.get("away", "").lower()

    if target_home and target_away:
        return target_home in api_home and target_away in api_away

    if game.get("spread_team"):
        team = game["spread_team"].lower()
        return team in api_home or team in api_away

    return False


def find_event(events, game):
    for event in events:
        if names_match(event, game):
            return event
    return None


def get_live_total(event):
    for bookmaker in event.get("bookmakers", []):
        if bookmaker.get("key") != "draftkings":
            continue

        for market in bookmaker.get("markets", []):
            if market.get("key") != "totals":
                continue

            outcomes = market.get("outcomes", [])
            for outcome in outcomes:
                if outcome.get("name", "").lower() == "over":
                    return float(outcome.get("point"))

    return None


def get_live_spread(event, team_name):
    team_name = team_name.lower()

    for bookmaker in event.get("bookmakers", []):
        if bookmaker.get("key") != "draftkings":
            continue

        for market in bookmaker.get("markets", []):
            if market.get("key") != "spreads":
                continue

            for outcome in market.get("outcomes", []):
                if team_name in outcome.get("name", "").lower():
                    return float(outcome.get("point"))

    return None


def is_game_completed(score_event):
    return bool(score_event and score_event.get("completed") is True)


def mark_done(state, key, status):
    state[key]["status"] = status
    state[key]["done"] = True
    save_state(state)


def build_start_message(game):
    parts = [
        f"GAME STARTING: {game['game']}",
        f"League: {game['league']}",
    ]

    if game.get("opening_total") is not None:
        parts.append(f"Opening total: {game['opening_total']}")

    if game.get("over_strike") is not None:
        parts.append(f"Over strike: {game['over_strike']} or lower")

    if game.get("under_strike") is not None:
        parts.append(f"Under strike: {game['under_strike']} or higher")

    if game.get("spread_team"):
        parts.append(f"Spread team: {game['spread_team']}")
        parts.append(f"Spread strike: {game['spread_strike']} or better")
        if game.get("spread_best_value") is not None:
            parts.append(f"Best value: {game['spread_best_value']} or better")

    return "\n".join(parts)


def monitor_game(game, state, odds_by_sport, scores_by_sport):
    key = game["game"]
    now = datetime.now(ARIZONA)
    start = parse_start_time(game)

    if key not in state:
        state[key] = {
            "status": "dormant",
            "done": False,
            "start_alert_sent": False,
            "first_not_found_after_start": None,
        }
        save_state(state)

    game_state = state[key]

    if game_state.get("done"):
        return

    if now < start - timedelta(minutes=PRE_START_LOOKAHEAD_MINUTES):
        game_state["status"] = "dormant"
        save_state(state)
        return

    if now >= start and not game_state.get("start_alert_sent"):
        send_sms(build_start_message(game))
        game_state["start_alert_sent"] = True
        game_state["status"] = "active"
        save_state(state)

    odds_events = odds_by_sport.get(game["sport_key"], [])
    score_events = scores_by_sport.get(game["sport_key"], [])

    odds_event = find_event(odds_events, game)
    score_event = find_event(score_events, game)

    if is_game_completed(score_event):
        send_sms(f"GAME ENDED: {game['game']}\nNo strike hit.")
        mark_done(state, key, "finished_no_strike")
        return

    if not odds_event:
        if now >= start:
            if not game_state.get("first_not_found_after_start"):
                game_state["first_not_found_after_start"] = now.isoformat()
                save_state(state)
                return

            first_missing = datetime.fromisoformat(game_state["first_not_found_after_start"])

            if now - first_missing >= timedelta(minutes=NOT_FOUND_GRACE_MINUTES):
                send_sms(
                    f"GAME NOT FOUND: {game['game']}\n"
                    f"Could not locate live odds after {NOT_FOUND_GRACE_MINUTES} minutes. "
                    f"Stopped monitoring this game only."
                )
                mark_done(state, key, "not_found")
                return

        return

    game_state["status"] = "active"
    game_state["first_not_found_after_start"] = None
    save_state(state)

    live_total = get_live_total(odds_event)
    live_spread = None

    if game.get("spread_team"):
        live_spread = get_live_spread(odds_event, game["spread_team"])

    if live_total is not None:
        over_strike = game.get("over_strike")
        under_strike = game.get("under_strike")

        if over_strike is not None and live_total <= over_strike:
            send_sms(
                f"SHIFT ALERT: {game['game']}\n"
                f"PLAY: OVER\n"
                f"Live total: {live_total}\n"
                f"Strike: {over_strike} or lower"
            )
            mark_done(state, key, "over_strike_hit")
            return

        if under_strike is not None and live_total >= under_strike:
            send_sms(
                f"SHIFT ALERT: {game['game']}\n"
                f"PLAY: UNDER\n"
                f"Live total: {live_total}\n"
                f"Strike: {under_strike} or higher"
            )
            mark_done(state, key, "under_strike_hit")
            return

    if live_spread is not None and game.get("spread_team"):
        spread_strike = game.get("spread_strike")

        if spread_strike is not None:
            # Positive spread example: Spurs +4.5 or better means +4.5, +5.5, +6.5, etc.
            if spread_strike > 0 and live_spread >= spread_strike:
                send_sms(
                    f"SHIFT ALERT: {game['game']}\n"
                    f"PLAY: {game['spread_team']} live spread\n"
                    f"Live spread: {live_spread}\n"
                    f"Strike: +{spread_strike} or better"
                )
                mark_done(state, key, "spread_strike_hit")
                return

            # Negative spread example: Atlanta -2.5 or better means -2.5, -1.5, pick'em, + points.
            if spread_strike < 0 and live_spread >= spread_strike:
                send_sms(
                    f"SHIFT ALERT: {game['game']}\n"
                    f"PLAY: {game['spread_team']} live spread\n"
                    f"Live spread: {live_spread}\n"
                    f"Strike: {spread_strike} or better"
                )
                mark_done(state, key, "spread_strike_hit")
                return


def main():
    if not ODDS_API_KEY:
        raise RuntimeError("Missing ODDS_API_KEY")

    state = load_state()

    send_sms("SHIFT BOT STARTED\nDormant until each game reaches start window.")

    while True:
        try:
            active_sports = sorted(set(game["sport_key"] for game in GAMES))
            odds_by_sport = {}
            scores_by_sport = {}

            for sport_key in active_sports:
                odds_by_sport[sport_key] = fetch_odds(sport_key)
                scores_by_sport[sport_key] = fetch_scores(sport_key)

            for game in GAMES:
                monitor_game(game, state, odds_by_sport, scores_by_sport)

            unfinished = [
                g for g in GAMES
                if not state.get(g["game"], {}).get("done")
            ]

            if not unfinished:
                send_sms("SHIFT BOT COMPLETE\nAll games finished, hit a strike, or were marked not found.")
                break

            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
