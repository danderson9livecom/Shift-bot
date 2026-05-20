import os
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from twilio.rest import Client

# =========================
# ENV VARIABLES
# =========================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

# =========================
# SETTINGS
# =========================
LOCAL_TZ = ZoneInfo("America/Phoenix")

CHECK_INTERVAL_SECONDS = 60
ACTIVATE_MINUTES_BEFORE_START = 5
STOP_MONITORING_HOURS_AFTER_START = 4

REGIONS = "us"
MARKETS = "totals"
ODDS_FORMAT = "american"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# =========================
# LIVE STRIKE LIST
# =========================
GAMES = [
    # =========================
    # NBA STRIKE
    # =========================
    {
        "sport": "basketball_nba",
        "name": "Spurs @ Thunder",
        "teams": ["San Antonio Spurs", "Oklahoma City Thunder"],
        "start_time": "2026-05-20 17:30",
        "play": "OVER",
        "strike_total": 208.5,
        "reason": "Best live strike from the Spurs/OKC analysis. Hit OVER if the live total falls to 208.5 or lower."
    },

    # =========================
    # WNBA STRIKES
    # =========================
    {
        "sport": "basketball_wnba",
        "name": "Dallas Wings @ Chicago Sky",
        "teams": ["Dallas Wings", "Chicago Sky"],
        "start_time": "2026-05-20 17:00",
        "play": "UNDER",
        "strike_total": 175.5,
        "reason": "Top WNBA live strike. Hit UNDER if the live total reaches 175.5 or higher."
    },
    {
        "sport": "basketball_wnba",
        "name": "Connecticut Sun @ Seattle Storm",
        "teams": ["Connecticut Sun", "Seattle Storm"],
        "start_time": "2026-05-20 19:00",
        "play": "UNDER",
        "strike_total": 174.5,
        "reason": "Second-best WNBA live strike. Hit UNDER if the live total reaches 174.5 or higher."
    },

    # =========================
    # MLB STRIKES
    # =========================
    {
        "sport": "baseball_mlb",
        "name": "Dodgers @ Padres",
        "teams": ["Los Angeles Dodgers", "San Diego Padres"],
        "start_time": "2026-05-20 17:40",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "Petco + strong starter setup. Strike inflated live total."
    },
    {
        "sport": "baseball_mlb",
        "name": "Brewers @ Cubs",
        "teams": ["Milwaukee Brewers", "Chicago Cubs"],
        "start_time": "2026-05-20 16:40",
        "play": "UNDER",
        "strike_total": 7.5,
        "reason": "Wrigley suppression setup. Strike only if live total rises."
    },
    {
        "sport": "baseball_mlb",
        "name": "Braves @ Marlins",
        "teams": ["Atlanta Braves", "Miami Marlins"],
        "start_time": "2026-05-20 15:40",
        "play": "OVER",
        "strike_total": 6.5,
        "reason": "Atlanta run path. Strike if live total drops too low."
    },
    {
        "sport": "baseball_mlb",
        "name": "Astros @ Twins",
        "teams": ["Houston Astros", "Minnesota Twins"],
        "start_time": "2026-05-20 10:40",
        "play": "UNDER",
        "strike_total": 9.0,
        "reason": "Controlled run environment. Strike inflated live total."
    },
    {
        "sport": "baseball_mlb",
        "name": "White Sox @ Mariners",
        "teams": ["Chicago White Sox", "Seattle Mariners"],
        "start_time": "2026-05-20 13:10",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "Seattle pitching edge + T-Mobile suppression."
    },
    {
        "sport": "baseball_mlb",
        "name": "Rangers @ Rockies",
        "teams": ["Texas Rangers", "Colorado Rockies"],
        "start_time": "2026-05-20 12:10",
        "play": "OVER",
        "strike_total": 9.0,
        "reason": "Coors Field volatility. Strike if live total falls."
    },
    {
        "sport": "baseball_mlb",
        "name": "Red Sox @ Royals",
        "teams": ["Boston Red Sox", "Kansas City Royals"],
        "start_time": "2026-05-20 16:40",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "Royals pace control. Strike inflated live total."
    },
    {
        "sport": "baseball_mlb",
        "name": "Blue Jays @ Yankees",
        "teams": ["Toronto Blue Jays", "New York Yankees"],
        "start_time": "2026-05-20 16:05",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "Yankee Stadium can inflate live totals after one HR."
    },
    {
        "sport": "baseball_mlb",
        "name": "Mets @ Nationals",
        "teams": ["New York Mets", "Washington Nationals"],
        "start_time": "2026-05-20 15:45",
        "play": "OVER",
        "strike_total": 8.5,
        "reason": "Nationals bullpen volatility. Strike if total drops."
    },
    {
        "sport": "baseball_mlb",
        "name": "Giants @ Diamondbacks",
        "teams": ["San Francisco Giants", "Arizona Diamondbacks"],
        "start_time": "2026-05-20 12:40",
        "play": "OVER",
        "strike_total": 7.5,
        "reason": "Arizona late-scoring environment. Strike low live total."
    },
    {
        "sport": "baseball_mlb",
        "name": "Reds @ Phillies",
        "teams": ["Cincinnati Reds", "Philadelphia Phillies"],
        "start_time": "2026-05-20 10:05",
        "play": "OVER",
        "strike_total": 8.5,
        "reason": "Citizens Bank scoring variance. Strike low live total."
    },
    {
        "sport": "baseball_mlb",
        "name": "Pirates @ Cardinals",
        "teams": ["Pittsburgh Pirates", "St. Louis Cardinals"],
        "start_time": "2026-05-20 16:45",
        "play": "OVER",
        "strike_total": 6.5,
        "reason": "Low total creates value if starter exits early."
    },
    {
        "sport": "baseball_mlb",
        "name": "Athletics @ Angels",
        "teams": ["Athletics", "Los Angeles Angels"],
        "start_time": "2026-05-20 18:38",
        "play": "UNDER",
        "strike_total": 10.5,
        "reason": "Market can overprice Angels scoring volatility."
    },
    {
        "sport": "baseball_mlb",
        "name": "Guardians @ Tigers",
        "teams": ["Cleveland Guardians", "Detroit Tigers"],
        "start_time": "2026-05-20 15:40",
        "play": "UNDER",
        "strike_total": 8.5,
        "reason": "Comerica suppresses power. Strike inflated live total."
    },
]

# =========================
# INITIALIZE GAME STATE
# =========================
for game in GAMES:
    game["start_dt"] = datetime.strptime(
        game["start_time"], "%Y-%m-%d %H:%M"
    ).replace(tzinfo=LOCAL_TZ)

    game["active"] = False
    game["alert_sent"] = False
    game["finished"] = False


# =========================
# TWILIO TEXT ALERT
# =========================
def send_text(message):
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )


# =========================
# ODDS API
# =========================
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


# =========================
# MATCH GAME BY TEAMS
# =========================
def teams_match(event, game):
    home = event.get("home_team", "").lower()
    away = event.get("away_team", "").lower()

    event_teams = [home, away]

    for team in game["teams"]:
        team_lower = team.lower()

        if not any(
            team_lower in event_team or event_team in team_lower
            for event_team in event_teams
        ):
            return False

    return True


# =========================
# GET BEST AVAILABLE LIVE TOTAL
# =========================
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


# =========================
# STRIKE LOGIC
# =========================
def should_strike(game, live_total):
    if game["play"] == "OVER":
        return live_total <= game["strike_total"]

    if game["play"] == "UNDER":
        return live_total >= game["strike_total"]

    return False


# =========================
# ACTIVATE / EXPIRE EACH GAME
# =========================
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


# =========================
# MAIN MONITOR LOOP
# =========================
def monitor_games():
    print("Live strike bot started.")
    print("Monitoring NBA, WNBA, and MLB totals.")
    print("Each game activates individually.")
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

            sports_needed = sorted(set(game["sport"] for game in active_games))
            odds_by_sport = {}

            for sport in sports_needed:
                odds_by_sport[sport] = get_live_totals(sport)

            for game in active_games:
                odds_data = odds_by_sport.get(game["sport"], [])
                matched_event = None

                for event in odds_data:
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


if __name__ == "__main__":
    monitor_games()
