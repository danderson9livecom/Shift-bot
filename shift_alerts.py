import os
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from twilio.rest import Client

# =========================
# ENVIRONMENT VARIABLES
# =========================

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

SPORT = "baseball_mlb"
REGION = "us"
MARKETS = "totals,h2h,spreads"
ODDS_FORMAT = "american"

LOCAL_TZ = ZoneInfo("America/Phoenix")

CHECK_INTERVAL_SECONDS = 30
START_BUFFER_MINUTES = 10

# A game will NOT be marked done just because odds are missing.
# It must either be confirmed completed, or missing repeatedly after a long time.
MAX_MISSING_LIVE_CHECKS = 20
SAFE_FINAL_HOURS_AFTER_START = 5


# =========================
# WATCH LIST
# =========================

WATCH_LIST = [
    {
        "game": "Braves @ Marlins",
        "away": "Atlanta Braves",
        "home": "Miami Marlins",
        "start_time": "2026-05-19 13:10",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Reds @ Phillies",
        "away": "Cincinnati Reds",
        "home": "Philadelphia Phillies",
        "start_time": "2026-05-19 15:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Guardians @ Tigers",
        "away": "Cleveland Guardians",
        "home": "Detroit Tigers",
        "start_time": "2026-05-19 15:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Mets @ Nationals",
        "away": "New York Mets",
        "home": "Washington Nationals",
        "start_time": "2026-05-19 15:45",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Blue Jays @ Yankees",
        "away": "Toronto Blue Jays",
        "home": "New York Yankees",
        "start_time": "2026-05-19 16:05",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Red Sox @ Royals",
        "away": "Boston Red Sox",
        "home": "Kansas City Royals",
        "start_time": "2026-05-19 16:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Astros @ Twins",
        "away": "Houston Astros",
        "home": "Minnesota Twins",
        "start_time": "2026-05-19 16:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Brewers @ Cubs",
        "away": "Milwaukee Brewers",
        "home": "Chicago Cubs",
        "start_time": "2026-05-19 16:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Pirates @ Cardinals",
        "away": "Pittsburgh Pirates",
        "home": "St. Louis Cardinals",
        "start_time": "2026-05-19 16:45",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Rangers @ Rockies",
        "away": "Texas Rangers",
        "home": "Colorado Rockies",
        "start_time": "2026-05-19 17:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Athletics @ Angels",
        "away": "Athletics",
        "home": "Los Angeles Angels",
        "start_time": "2026-05-19 18:38",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "White Sox @ Mariners",
        "away": "Chicago White Sox",
        "home": "Seattle Mariners",
        "start_time": "2026-05-19 18:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Dodgers @ Padres",
        "away": "Los Angeles Dodgers",
        "home": "San Diego Padres",
        "start_time": "2026-05-19 18:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
    {
        "game": "Orioles @ Rays",
        "away": "Baltimore Orioles",
        "home": "Tampa Bay Rays",
        "start_time": "2026-05-19 15:40",
        "over_trigger": 6.5,
        "under_trigger": 11.5,
    },
]


# =========================
# STATE
# =========================

state = {}

for item in WATCH_LIST:
    state[item["game"]] = {
        "active": False,
        "done": False,
        "over_alert_sent": False,
        "under_alert_sent": False,
        "missing_live_checks": 0,
    }


# =========================
# HELPERS
# =========================

def now_local():
    return datetime.now(LOCAL_TZ)


def parse_start_time(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TZ)


def send_text(message):
    print(message)

    if not all([
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
        TWILIO_FROM_NUMBER,
        ALERT_TO_NUMBER
    ]):
        print("SMS skipped: missing Twilio environment variables.")
        return

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )


def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGION,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        print(f"ODDS API ERROR: {response.status_code} | {response.text}")
        return []

    return response.json()


def teams_match(api_game, watched_game):
    api_home = api_game.get("home_team", "").lower()
    api_away = api_game.get("away_team", "").lower()

    watched_home = watched_game["home"].lower()
    watched_away = watched_game["away"].lower()

    return (
        watched_home in api_home or api_home in watched_home
    ) and (
        watched_away in api_away or api_away in watched_away
    )


def is_confirmed_completed(api_game):
    completed = api_game.get("completed")

    if completed is True:
        return True

    status = str(api_game.get("status", "")).lower()

    if status in ["final", "completed", "complete", "closed"]:
        return True

    return False


def extract_live_total(api_game):
    best_total = None

    bookmakers = api_game.get("bookmakers", [])

    for book in bookmakers:
        markets = book.get("markets", [])

        for market in markets:
            if market.get("key") != "totals":
                continue

            outcomes = market.get("outcomes", [])

            for outcome in outcomes:
                point = outcome.get("point")

                if point is not None:
                    best_total = float(point)
                    return best_total

    return None


def find_game(api_games, watched_game):
    for api_game in api_games:
        if teams_match(api_game, watched_game):
            return api_game

    return None


# =========================
# MAIN LOOP
# =========================

def monitor():
    send_text("MLB live betting bot started. Dormant game protection is active.")

    while True:
        current_time = now_local()
        api_games = get_odds()

        active_count = 0
        waiting_count = 0

        for watched_game in WATCH_LIST:
            game_name = watched_game["game"]
            game_state = state[game_name]

            if game_state["done"]:
                continue

            start_time = parse_start_time(watched_game["start_time"])
            activation_time = start_time - timedelta(minutes=START_BUFFER_MINUTES)

            if current_time < activation_time:
                waiting_count += 1
                print(
                    f"DORMANT: {game_name} starts at "
                    f"{start_time.strftime('%I:%M %p').lstrip('0')}"
                )
                continue

            if not game_state["active"]:
                game_state["active"] = True
                send_text(f"ACTIVE: {game_name} monitoring started.")

            active_count += 1

            api_game = find_game(api_games, watched_game)

            if api_game is None:
                game_state["missing_live_checks"] += 1

                print(
                    f"NO LIVE DATA YET: {game_name} | "
                    f"missing check {game_state['missing_live_checks']}/"
                    f"{MAX_MISSING_LIVE_CHECKS}"
                )

                hours_since_start = (current_time - start_time).total_seconds() / 3600

                if (
                    hours_since_start >= SAFE_FINAL_HOURS_AFTER_START
                    and game_state["missing_live_checks"] >= MAX_MISSING_LIVE_CHECKS
                ):
                    game_state["done"] = True
                    send_text(
                        f"DONE: {game_name} removed after long post-start missing data. "
                        f"This was NOT marked final immediately."
                    )

                continue

            game_state["missing_live_checks"] = 0

            if is_confirmed_completed(api_game):
                game_state["done"] = True
                send_text(f"DONE: {game_name} confirmed final by API.")
                continue

            live_total = extract_live_total(api_game)

            if live_total is None:
                print(f"ACTIVE: {game_name} | No total available right now.")
                continue

            print(
                f"ACTIVE: {game_name} | live total: {live_total} | "
                f"over trigger: {watched_game['over_trigger']} | "
                f"under trigger: {watched_game['under_trigger']}"
            )

            if (
                live_total <= watched_game["over_trigger"]
                and not game_state["over_alert_sent"]
            ):
                game_state["over_alert_sent"] = True
                send_text(
                    f"OVER TRIGGER: {game_name}\n"
                    f"Live total is {live_total}.\n"
                    f"Target was {watched_game['over_trigger']} or lower."
                )

            if (
                live_total >= watched_game["under_trigger"]
                and not game_state["under_alert_sent"]
            ):
                game_state["under_alert_sent"] = True
                send_text(
                    f"UNDER TRIGGER: {game_name}\n"
                    f"Live total is {live_total}.\n"
                    f"Target was {watched_game['under_trigger']} or higher."
                )

        print(f"ACTIVE MODE: {active_count} game(s) active.")
        print(f"Still monitoring/waiting on {active_count + waiting_count} game(s).")

        if all(state[item["game"]]["done"] for item in WATCH_LIST):
            send_text("All watched MLB games are done. Bot shutting down.")
            break

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    monitor()
