import os
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from twilio.rest import Client

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

LOCAL_TZ = ZoneInfo("America/Phoenix")

CHECK_INTERVAL_SECONDS = 60
ACTIVATE_MINUTES_BEFORE_START = 5
STOP_MONITORING_HOURS_AFTER_START = 4

REGIONS = "us"
MARKETS = "totals"
ODDS_FORMAT = "american"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

GAMES = [
    {
        "sport": "basketball_nba",
        "name": "Cavaliers @ Knicks",
        "teams": ["Cleveland Cavaliers", "New York Knicks"],
        "start_time": "2026-05-21 17:00",
        "play": "OVER",
        "strike_total": 209.5,
        "reason": "NBA live strike. Hit OVER if live total falls to 209.5 or lower."
    },

    {
        "sport": "basketball_wnba",
        "name": "Portland Fire @ Indiana Fever",
        "teams": ["Portland Fire", "Indiana Fever"],
        "start_time": "2026-05-21 16:00",
        "play": "UNDER",
        "strike_total": 184.5,
        "reason": "WNBA live strike. Hit UNDER if live total reaches 184.5 or higher."
    },
    {
        "sport": "basketball_wnba",
        "name": "Dallas Wings @ Chicago Sky",
        "teams": ["Dallas Wings", "Chicago Sky"],
        "start_time": "2026-05-21 17:00",
        "play": "UNDER",
        "strike_total": 175.5,
        "reason": "WNBA live strike. Hit UNDER if live total reaches 175.5 or higher."
    },
    {
        "sport": "basketball_wnba",
        "name": "Connecticut Sun @ Seattle Storm",
        "teams": ["Connecticut Sun", "Seattle Storm"],
        "start_time": "2026-05-21 19:00",
        "play": "UNDER",
        "strike_total": 174.5,
        "reason": "WNBA live strike. Hit UNDER if live total reaches 174.5 or higher."
    },

    {
        "sport": "baseball_mlb",
        "name": "Guardians @ Tigers",
        "teams": ["Cleveland Guardians", "Detroit Tigers"],
        "start_time": "2026-05-21 10:10",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "MLB live strike. Hit UNDER if live total reaches 8.5 or higher."
    },
    {
        "sport": "baseball_mlb",
        "name": "Pirates @ Cardinals",
        "teams": ["Pittsburgh Pirates", "St. Louis Cardinals"],
        "start_time": "2026-05-21 10:15",
        "play": "OVER",
        "strike_total": 6.5,
        "reason": "MLB live strike. Hit OVER if live total falls to 6.5 or lower."
    },
    {
        "sport": "baseball_mlb",
        "name": "Mets @ Nationals",
        "teams": ["New York Mets", "Washington Nationals"],
        "start_time": "2026-05-21 13:05",
        "play": "OVER",
        "strike_total": 8.5,
        "reason": "MLB live strike. Hit OVER if live total falls to 8.5 or lower."
    },
    {
        "sport": "baseball_mlb",
        "name": "Braves @ Marlins",
        "teams": ["Atlanta Braves", "Miami Marlins"],
        "start_time": "2026-05-21 15:40",
        "play": "OVER",
        "strike_total": 6.5,
        "reason": "MLB live strike. Hit OVER if live total falls to 6.5 or lower."
    },
    {
        "sport": "baseball_mlb",
        "name": "Blue Jays @ Yankees",
        "teams": ["Toronto Blue Jays", "New York Yankees"],
        "start_time": "2026-05-21 16:05",
        "play": "UNDER",
        "strike_total": 9.5,
        "reason": "MLB live strike. Hit UNDER if live total reaches 9.5 or higher."
    },
    {
        "sport": "baseball_mlb",
        "name": "Athletics @ Angels",
        "teams": ["Athletics", "Los Angeles Angels"],
        "start_time": "2026-05-21 18:38",
        "play": "UNDER",
        "strike_total": 10.5,
        "reason": "MLB live strike. Hit UNDER if live total reaches 10.5 or higher."
    },
    {
        "sport": "baseball_mlb",
        "name": "Rockies @ Diamondbacks",
        "teams": ["Colorado Rockies", "Arizona Diamondbacks"],
        "start_time": "2026-05-21 18:40",
        "play": "OVER",
        "strike_total": 8.5,
        "reason": "MLB live strike. Hit OVER if live total falls to 8.5 or lower."
    },
]

for game in GAMES:
    game["start_dt"] = datetime.strptime(game["start_time"], "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TZ)
    game["active"] = False
    game["alert_sent"] = False
    game["finished"] = False


def send_text(message):
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )


def get_live_totals(sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def teams_match(event, game):
    home = event.get("home_team", "").lower()
    away = event.get("away_team", "").lower()
    event_teams = [home, away]

    for team in game["teams"]:
        team_lower = team.lower()

        if not any(team_lower in event_team or event_team in team_lower for event_team in event_teams):
            return False

    return True


def extract_live_total(event):
    totals = []

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "totals":
                continue

            for outcome in market.get("outcomes", []):
                point = outcome.get("point")
                if point is not None:
                    totals.append(float(point))

    if not totals:
        return None

    return sum(totals) / len(totals)


def should_strike(game, live_total):
    if game["play"] == "OVER":
        return live_total <= game["strike_total"]

    if game["play"] == "UNDER":
        return live_total >= game["strike_total"]

    return False


def activate_and_expire_games():
    now = datetime.now(LOCAL_TZ)

    for game in GAMES:
        activate_time = game["start_dt"] - timedelta(minutes=ACTIVATE_MINUTES_BEFORE_START)
        expire_time = game["start_dt"] + timedelta(hours=STOP_MONITORING_HOURS_AFTER_START)

        if game["finished"]:
            continue

        if now >= expire_time:
            game["finished"] = True
            game["active"] = False
            print(f"STOPPED: {game['name']} expired.")
            continue

        if now >= activate_time and not game["alert_sent"]:
            game["active"] = True


def monitor_games():
    print("Live strike bot started.")
    print("Monitoring NBA, WNBA, and MLB totals.")
    print("Each game stays dormant until its own activation window.")
    print("Each game shuts off individually after alert or expiration.")

    while True:
        try:
            activate_and_expire_games()

            active_games = [
                game for game in GAMES
                if game["active"] and not game["alert_sent"] and not game["finished"]
            ]

            if not active_games:
                print("No active games right now.")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            odds_by_sport = {}

            for sport in sorted(set(game["sport"] for game in active_games)):
                odds_by_sport[sport] = get_live_totals(sport)

            for game in active_games:
                matched_event = None

                for event in odds_by_sport.get(game["sport"], []):
                    if teams_match(event, game):
                        matched_event = event
                        break

                if not matched_event:
                    print(f"{game['name']}: no matching live odds found yet.")
                    continue

                live_total = extract_live_total(matched_event)

                if live_total is None:
                    print(f"{game['name']}: no live total available.")
                    continue

                print(
                    f"{game['name']} | {game['sport']} | "
                    f"Play: {game['play']} | "
                    f"Live Total: {live_total:.1f} | "
                    f"Strike: {game['strike_total']}"
                )

                if should_strike(game, live_total):
                    message = (
                        f"STRIKE ALERT\n\n"
                        f"{game['name']}\n"
                        f"SPORT: {game['sport']}\n"
                        f"PLAY: {game['play']}\n"
                        f"Live Total: {live_total:.1f}\n"
                        f"Strike Number: {game['strike_total']}\n\n"
                        f"Reason: {game['reason']}"
                    )

                    send_text(message)

                    game["alert_sent"] = True
                    game["active"] = False
                    game["finished"] = True

                    print(f"ALERT SENT AND GAME STOPPED: {game['name']}")

            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS)


def main():
    monitor_games()


if __name__ == "__main__":
    main()
