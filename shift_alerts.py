import os
import time
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
ALERT_TO_NUMBER = os.getenv("ALERT_TO_NUMBER")

BOOKMAKER = "draftkings"
REGION = "us"
MARKET = "totals"

LOCAL_TIMEZONE = ZoneInfo("America/Phoenix")

ACTIVE_CHECK_SECONDS = 30
DORMANT_CHECK_SECONDS = 300

START_ALERT_MINUTES_BEFORE = 15
ACTIVE_WINDOW_MINUTES_BEFORE = 30
ACTIVE_WINDOW_HOURS_AFTER = 6


WATCHLIST = [
    # ================= MLB =================
    {
        "sport_key": "baseball_mlb",
        "name": "Orioles @ Rays",
        "teams": ["Baltimore Orioles", "Tampa Bay Rays"],
        "trigger": 6.0,
        "condition": "below",
        "message": "MLB SHIFT: Orioles/Rays live total hit 6 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Braves @ Marlins",
        "teams": ["Atlanta Braves", "Miami Marlins"],
        "trigger": 10.5,
        "condition": "above",
        "message": "MLB SHIFT: Braves/Marlins live total hit 10.5 or higher. HIT UNDER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Guardians @ Tigers",
        "teams": ["Cleveland Guardians", "Detroit Tigers"],
        "trigger": 6.0,
        "condition": "below",
        "message": "MLB SHIFT: Guardians/Tigers live total hit 6 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Reds @ Phillies",
        "teams": ["Cincinnati Reds", "Philadelphia Phillies"],
        "trigger": 8.0,
        "condition": "below",
        "message": "MLB SHIFT: Reds/Phillies live total hit 8 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Mets @ Nationals",
        "teams": ["New York Mets", "Washington Nationals"],
        "trigger": 8.0,
        "condition": "below",
        "message": "MLB SHIFT: Mets/Nationals live total hit 8 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Blue Jays @ Yankees",
        "teams": ["Toronto Blue Jays", "New York Yankees"],
        "trigger": 7.5,
        "condition": "below",
        "message": "MLB SHIFT: Blue Jays/Yankees full-game total dropped to 7.5 or lower. CHECK Yankees team total OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Red Sox @ Royals",
        "teams": ["Boston Red Sox", "Kansas City Royals"],
        "trigger": 10.5,
        "condition": "above",
        "message": "MLB SHIFT: Red Sox/Royals live total hit 10.5 or higher. HIT UNDER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Astros @ Twins",
        "teams": ["Houston Astros", "Minnesota Twins"],
        "trigger": 8.0,
        "condition": "below",
        "message": "MLB SHIFT: Astros/Twins live total hit 8 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Brewers @ Cubs",
        "teams": ["Milwaukee Brewers", "Chicago Cubs"],
        "trigger": 9.0,
        "condition": "below",
        "message": "MLB SHIFT: Brewers/Cubs live total hit 9 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Rangers @ Rockies",
        "teams": ["Texas Rangers", "Colorado Rockies"],
        "trigger": 8.0,
        "condition": "below",
        "message": "MLB SHIFT: Rangers/Rockies live total hit 8 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Athletics @ Angels",
        "teams": ["Athletics", "Los Angeles Angels"],
        "trigger": 10.5,
        "condition": "above",
        "message": "MLB SHIFT: Athletics/Angels live total hit 10.5 or higher. HIT UNDER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "White Sox @ Mariners",
        "teams": ["Chicago White Sox", "Seattle Mariners"],
        "trigger": 6.0,
        "condition": "below",
        "message": "MLB SHIFT: White Sox/Mariners live total hit 6 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Dodgers @ Padres",
        "teams": ["Los Angeles Dodgers", "San Diego Padres"],
        "trigger": 9.0,
        "condition": "above",
        "message": "MLB SHIFT: Dodgers/Padres live total hit 9 or higher. HIT UNDER.",
        "sent": False,
    },
    {
        "sport_key": "baseball_mlb",
        "name": "Giants @ D-backs",
        "teams": ["San Francisco Giants", "Arizona Diamondbacks"],
        "trigger": 7.0,
        "condition": "below",
        "message": "MLB SHIFT: Giants/D-backs live total hit 7 or lower. HIT OVER.",
        "sent": False,
    },

    # ================= WNBA =================
    {
        "sport_key": "basketball_wnba",
        "name": "Mystics @ Wings OVER",
        "teams": ["Washington Mystics", "Dallas Wings"],
        "trigger": 160.0,
        "condition": "below",
        "message": "WNBA SHIFT: Mystics/Wings live total hit 160 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "basketball_wnba",
        "name": "Mystics @ Wings UNDER",
        "teams": ["Washington Mystics", "Dallas Wings"],
        "trigger": 181.0,
        "condition": "above",
        "message": "WNBA SHIFT: Mystics/Wings live total hit 181 or higher. HIT UNDER.",
        "sent": False,
    },
    {
        "sport_key": "basketball_wnba",
        "name": "Sun @ Fire OVER",
        "teams": ["Connecticut Sun", "Portland Fire"],
        "trigger": 160.0,
        "condition": "below",
        "message": "WNBA SHIFT: Sun/Fire live total hit 160 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "basketball_wnba",
        "name": "Sun @ Fire UNDER",
        "teams": ["Connecticut Sun", "Portland Fire"],
        "trigger": 185.0,
        "condition": "above",
        "message": "WNBA SHIFT: Sun/Fire live total hit 185 or higher. HIT UNDER.",
        "sent": False,
    },

    # ================= NBA =================
    {
        "sport_key": "basketball_nba",
        "name": "Spurs @ Thunder OVER",
        "teams": ["San Antonio Spurs", "Oklahoma City Thunder"],
        "trigger": 208.0,
        "condition": "below",
        "message": "NBA SHIFT: Spurs/Thunder live total hit 208 or lower. HIT OVER.",
        "sent": False,
    },
    {
        "sport_key": "basketball_nba",
        "name": "Spurs @ Thunder UNDER",
        "teams": ["San Antonio Spurs", "Oklahoma City Thunder"],
        "trigger": 240.0,
        "condition": "above",
        "message": "NBA SHIFT: Spurs/Thunder live total hit 240 or higher. HIT UNDER.",
        "sent": False,
    },
]


START_ALERTS_SENT = set()


def send_text(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )
    print(f"TEXT SENT: {message}")


def get_live_totals(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "bookmakers": BOOKMAKER,
        "oddsFormat": "american",
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        print(f"Odds API error for {sport_key}: {response.status_code} {response.text}")
        return []

    return response.json()


def normalize_team_name(name):
    name = name.lower().strip()

    aliases = {
        "oakland athletics": "athletics",
        "sacramento athletics": "athletics",
        "athletics": "athletics",

        "arizona diamondbacks": "arizona diamondbacks",
        "d-backs": "arizona diamondbacks",
        "diamondbacks": "arizona diamondbacks",

        "phoenix mercury": "portland fire",
        "portland fire": "portland fire",
        "fire": "portland fire",
    }

    return aliases.get(name, name)


def teams_match(game, watch):
    home = normalize_team_name(game.get("home_team", ""))
    away = normalize_team_name(game.get("away_team", ""))

    game_teams = {home, away}
    watch_teams = {normalize_team_name(team) for team in watch["teams"]}

    return watch_teams.issubset(game_teams)


def extract_total(game):
    for book in game.get("bookmakers", []):
        if book.get("key") != BOOKMAKER:
            continue

        for market in book.get("markets", []):
            if market.get("key") != MARKET:
                continue

            for outcome in market.get("outcomes", []):
                if outcome.get("name", "").lower() == "over":
                    return float(outcome.get("point"))

    return None


def parse_game_time(game):
    commence_time = game.get("commence_time")

    if not commence_time:
        return None

    try:
        return datetime.fromisoformat(
            commence_time.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except Exception:
        return None


def format_local_time(game_time):
    local_time = game_time.astimezone(LOCAL_TIMEZONE)
    return local_time.strftime("%I:%M %p").lstrip("0")


def trigger_hit(current_total, watch):
    if watch["condition"] == "below":
        return current_total <= watch["trigger"]

    if watch["condition"] == "above":
        return current_total >= watch["trigger"]

    return False


def start_alert_key(game):
    home = normalize_team_name(game.get("home_team", ""))
    away = normalize_team_name(game.get("away_team", ""))
    start = game.get("commence_time", "")
    return f"{away}@{home}:{start}"


def maybe_send_start_alert(game):
    game_time = parse_game_time(game)

    if game_time is None:
        return

    now = datetime.now(timezone.utc)
    minutes_until_start = (game_time - now).total_seconds() / 60

    if 0 <= minutes_until_start <= START_ALERT_MINUTES_BEFORE:
        key = start_alert_key(game)

        if key not in START_ALERTS_SENT:
            away = game.get("away_team", "Away")
            home = game.get("home_team", "Home")
            local_start = format_local_time(game_time)

            send_text(
                f"SHIFT BOT: {away} @ {home} starts at {local_start} Arizona time. Monitoring live totals now."
            )

            START_ALERTS_SENT.add(key)


def game_is_active_or_close(game):
    game_time = parse_game_time(game)

    if game_time is None:
        return True

    now = datetime.now(timezone.utc)

    active_start = game_time - timedelta(minutes=ACTIVE_WINDOW_MINUTES_BEFORE)
    active_end = game_time + timedelta(hours=ACTIVE_WINDOW_HOURS_AFTER)

    return active_start <= now <= active_end


def main():
    print("SHIFT bot started.")
    print("Watching MLB, WNBA, and NBA scenarios.")

    send_text("SHIFT bot started. Watching MLB, WNBA, and NBA scenarios.")

    sport_keys = sorted(set(watch["sport_key"] for watch in WATCHLIST))

    while True:
        try:
            should_check_fast = False

            for sport_key in sport_keys:
                games = get_live_totals(sport_key)

                for game in games:
                    matched_any_watch = False

                    for watch in WATCHLIST:
                        if watch["sport_key"] != sport_key:
                            continue

                        if teams_match(game, watch):
                            matched_any_watch = True

                            maybe_send_start_alert(game)

                            if game_is_active_or_close(game):
                                should_check_fast = True

                            current_total = extract_total(game)

                            if current_total is None:
                                print(f"{watch['name']}: No total found yet.")
                                continue

                            print(f"{watch['name']} live total: {current_total}")

                            if trigger_hit(current_total, watch) and not watch["sent"]:
                                alert = f"{watch['message']} Current total: {current_total}"
                                send_text(alert)
                                watch["sent"] = True

                    if matched_any_watch and game_is_active_or_close(game):
                        should_check_fast = True

            if should_check_fast:
                print(f"Active mode. Checking again in {ACTIVE_CHECK_SECONDS} seconds.")
                time.sleep(ACTIVE_CHECK_SECONDS)
            else:
                print(f"Dormant mode. Checking again in {DORMANT_CHECK_SECONDS} seconds.")
                time.sleep(DORMANT_CHECK_SECONDS)

        except Exception as e:
            print("Error:", e)
            time.sleep(DORMANT_CHECK_SECONDS)


if __name__ == "__main__":
    main()
