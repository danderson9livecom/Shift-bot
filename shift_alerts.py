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

CHECK_INTERVAL_SECONDS = 60
LOCAL_TZ = ZoneInfo("America/Phoenix")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

RECOMMENDED_GAMES = [
    # MLB — May 21, 2026
    {
        "sport": "baseball_mlb",
        "name": "Mets @ Nationals",
        "away": "New York Mets",
        "home": "Washington Nationals",
        "start_time_local": "2026-05-21 13:05",
        "play": "OVER",
        "strike_total": 7.5,
        "opening_total": 8.5,
        "true_projection": 10.5,
        "note": "MLB SHIFT OVER strike. Hit OVER if live total drops to 7.5 or lower.",
    },
    {
        "sport": "baseball_mlb",
        "name": "Braves @ Marlins",
        "away": "Atlanta Braves",
        "home": "Miami Marlins",
        "start_time_local": "2026-05-21 15:40",
        "play": "UNDER",
        "strike_total": 8.5,
        "opening_total": 7.5,
        "true_projection": 5.5,
        "note": "MLB SHIFT UNDER strike. Hit UNDER if live total rises to 8.5 or higher.",
    },
    {
        "sport": "baseball_mlb",
        "name": "Guardians @ Tigers",
        "away": "Cleveland Guardians",
        "home": "Detroit Tigers",
        "start_time_local": "2026-05-21 10:10",
        "play": "UNDER",
        "strike_total": 8.5,
        "opening_total": 7.5,
        "true_projection": 6.0,
        "note": "MLB SHIFT UNDER strike. Hit UNDER if live total rises to 8.5 or higher.",
    },
    {
        "sport": "baseball_mlb",
        "name": "Blue Jays @ Yankees",
        "away": "Toronto Blue Jays",
        "home": "New York Yankees",
        "start_time_local": "2026-05-21 16:05",
        "play": "OVER",
        "strike_total": 7.5,
        "opening_total": 8.0,
        "true_projection": 9.5,
        "note": "MLB SHIFT OVER strike. Hit OVER if live total drops to 7.5 or lower.",
    },

    # NBA — May 21, 2026
    {
        "sport": "basketball_nba",
        "name": "Cavaliers @ Knicks",
        "away": "Cleveland Cavaliers",
        "home": "New York Knicks",
        "start_time_local": "2026-05-21 17:00",
        "play": "OVER",
        "strike_total": 208.5,
        "opening_total": 215.5,
        "true_projection": 220.0,
        "note": "NBA SHIFT OVER strike. Hit OVER if live total drops to 208.5 or lower.",
    },

    # WNBA — May 21, 2026
    {
        "sport": "basketball_wnba",
        "name": "Sparks @ Mercury",
        "away": "Los Angeles Sparks",
        "home": "Phoenix Mercury",
        "start_time_local": "2026-05-21 19:00",
        "play": "OVER",
        "strike_total": 171.5,
        "opening_total": 177.5,
        "true_projection": 184.0,
        "note": "WNBA SHIFT OVER strike. Hit OVER if live total drops to 171.5 or lower.",
    },
    {
        "sport": "basketball_wnba",
        "name": "Valkyries @ Liberty",
        "away": "Golden State Valkyries",
        "home": "New York Liberty",
        "start_time_local": "2026-05-21 16:00",
        "play": "UNDER",
        "strike_total": 174.5,
        "opening_total": 169.5,
        "true_projection": 165.0,
        "note": "WNBA SHIFT UNDER strike. Hit UNDER if live total rises to 174.5 or higher.",
    },
    {
        "sport": "basketball_wnba",
        "name": "Tempo @ Lynx",
        "away": "Toronto Tempo",
        "home": "Minnesota Lynx",
        "start_time_local": "2026-05-21 17:00",
        "play": "UNDER",
        "strike_total": 177.5,
        "opening_total": 172.5,
        "true_projection": 170.5,
        "note": "WNBA SHIFT UNDER strike. Hit UNDER only if live total rises to 177.5 or higher.",
    },
]


def send_text(message):
    print(message)
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER,
    )


def parse_local_start(game):
    return datetime.strptime(
        game["start_time_local"], "%Y-%m-%d %H:%M"
    ).replace(tzinfo=LOCAL_TZ)


def fetch_scores(sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores/"
    params = {
        "apiKey": ODDS_API_KEY,
        "daysFrom": 1,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_live_odds(sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "american",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def team_match(api_game, target):
    home = api_game.get("home_team", "")
    away = api_game.get("away_team", "")

    home_ok = target["home"].lower() in home.lower() or home.lower() in target["home"].lower()
    away_ok = target["away"].lower() in away.lower() or away.lower() in target["away"].lower()

    return home_ok and away_ok


def find_game(data, target):
    for api_game in data:
        if team_match(api_game, target):
            return api_game
    return None


def get_live_total(api_game):
    if not api_game:
        return None

    totals = []

    for bookmaker in api_game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") == "totals":
                for outcome in market.get("outcomes", []):
                    point = outcome.get("point")
                    if point is not None:
                        totals.append(float(point))

    if not totals:
        return None

    return round(sum(totals) / len(totals), 1)


def is_completed(score_game):
    return bool(score_game and score_game.get("completed") is True)


def should_trigger(game, live_total):
    if live_total is None:
        return False

    if game["play"] == "OVER":
        return live_total <= game["strike_total"]

    if game["play"] == "UNDER":
        return live_total >= game["strike_total"]

    return False


def main():
    status = {}

    for game in RECOMMENDED_GAMES:
        status[game["name"]] = {
            "alert_sent": False,
            "completed": False,
            "start": parse_local_start(game),
        }

    send_text("SHIFT bot is live for today's MLB, NBA, and WNBA recommendations.")

    while True:
        now = datetime.now(LOCAL_TZ)
        all_done = True

        sports_needed = sorted(set(game["sport"] for game in RECOMMENDED_GAMES))

        scores_by_sport = {}
        odds_by_sport = {}

        for sport in sports_needed:
            try:
                scores_by_sport[sport] = fetch_scores(sport)
                odds_by_sport[sport] = fetch_live_odds(sport)
            except Exception as e:
                print(f"API error for {sport}: {e}")
                scores_by_sport[sport] = []
                odds_by_sport[sport] = []

        for game in RECOMMENDED_GAMES:
            game_status = status[game["name"]]

            if game_status["completed"]:
                continue

            all_done = False
            start_time = game_status["start"]

            if now < start_time - timedelta(minutes=10):
                print(f"{game['name']} dormant until {start_time.strftime('%I:%M %p')}")
                continue

            score_game = find_game(scores_by_sport.get(game["sport"], []), game)

            if is_completed(score_game):
                game_status["completed"] = True
                print(f"{game['name']} completed. Stopping only this game.")
                continue

            odds_game = find_game(odds_by_sport.get(game["sport"], []), game)
            live_total = get_live_total(odds_game)

            print(
                f"{game['name']} | {game['sport']} | "
                f"Play: {game['play']} | Strike: {game['strike_total']} | "
                f"Live total: {live_total}"
            )

            if (
                not game_status["alert_sent"]
                and live_total is not None
                and should_trigger(game, live_total)
            ):
                message = (
                    f"SHIFT STRIKE\n\n"
                    f"{game['name']}\n"
                    f"Sport: {game['sport']}\n"
                    f"Play: {game['play']}\n"
                    f"Live Total: {live_total}\n"
                    f"Strike Price: {game['strike_total']}\n"
                    f"Opening Total: {game['opening_total']}\n"
                    f"True Projection: {game['true_projection']}\n\n"
                    f"{game['note']}"
                )

                send_text(message)
                game_status["alert_sent"] = True

        if all_done:
            send_text("All SHIFT games are completed. Bot shutting down.")
            break

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
