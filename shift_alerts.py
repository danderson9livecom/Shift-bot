import os
import time
import requests
from datetime import datetime, timedelta
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
DORMANT_CHECK_SECONDS = 900

START_ALERT_MINUTES_BEFORE = 15
ACTIVE_WINDOW_HOURS_AFTER = 6


WATCHLIST = [
    {"sport_key": "baseball_mlb", "name": "Orioles @ Rays OVER", "teams": ["Baltimore Orioles", "Tampa Bay Rays"], "start_time": "2026-05-18 15:40", "trigger": 6.0, "condition": "below", "message": "MLB SHIFT: Orioles/Rays live total hit 6 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Braves @ Marlins UNDER", "teams": ["Atlanta Braves", "Miami Marlins"], "start_time": "2026-05-18 15:40", "trigger": 10.5, "condition": "above", "message": "MLB SHIFT: Braves/Marlins live total hit 10.5 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Guardians @ Tigers OVER", "teams": ["Cleveland Guardians", "Detroit Tigers"], "start_time": "2026-05-18 15:40", "trigger": 6.0, "condition": "below", "message": "MLB SHIFT: Guardians/Tigers live total hit 6 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Reds @ Phillies OVER", "teams": ["Cincinnati Reds", "Philadelphia Phillies"], "start_time": "2026-05-18 15:40", "trigger": 8.0, "condition": "below", "message": "MLB SHIFT: Reds/Phillies live total hit 8 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Mets @ Nationals OVER", "teams": ["New York Mets", "Washington Nationals"], "start_time": "2026-05-18 15:45", "trigger": 8.0, "condition": "below", "message": "MLB SHIFT: Mets/Nationals live total hit 8 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},

    {"sport_key": "baseball_mlb", "name": "Blue Jays @ Yankees TEAM TOTAL CHECK", "teams": ["Toronto Blue Jays", "New York Yankees"], "start_time": "2026-05-18 16:05", "trigger": 7.5, "condition": "below", "message": "MLB SHIFT: Blue Jays/Yankees full-game total dropped to 7.5 or lower. CHECK Yankees team total OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Red Sox @ Royals UNDER", "teams": ["Boston Red Sox", "Kansas City Royals"], "start_time": "2026-05-18 16:40", "trigger": 10.5, "condition": "above", "message": "MLB SHIFT: Red Sox/Royals live total hit 10.5 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Astros @ Twins OVER", "teams": ["Houston Astros", "Minnesota Twins"], "start_time": "2026-05-18 16:40", "trigger": 8.0, "condition": "below", "message": "MLB SHIFT: Astros/Twins live total hit 8 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Brewers @ Cubs OVER", "teams": ["Milwaukee Brewers", "Chicago Cubs"], "start_time": "2026-05-18 16:40", "trigger": 9.0, "condition": "below", "message": "MLB SHIFT: Brewers/Cubs live total hit 9 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},

    {"sport_key": "baseball_mlb", "name": "Rangers @ Rockies OVER", "teams": ["Texas Rangers", "Colorado Rockies"], "start_time": "2026-05-18 17:40", "trigger": 8.0, "condition": "below", "message": "MLB SHIFT: Rangers/Rockies live total hit 8 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Athletics @ Angels UNDER", "teams": ["Athletics", "Los Angeles Angels"], "start_time": "2026-05-18 18:38", "trigger": 10.5, "condition": "above", "message": "MLB SHIFT: Athletics/Angels live total hit 10.5 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "White Sox @ Mariners OVER", "teams": ["Chicago White Sox", "Seattle Mariners"], "start_time": "2026-05-18 18:40", "trigger": 6.0, "condition": "below", "message": "MLB SHIFT: White Sox/Mariners live total hit 6 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Dodgers @ Padres UNDER", "teams": ["Los Angeles Dodgers", "San Diego Padres"], "start_time": "2026-05-18 18:40", "trigger": 9.0, "condition": "above", "message": "MLB SHIFT: Dodgers/Padres live total hit 9 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "baseball_mlb", "name": "Giants @ D-backs OVER", "teams": ["San Francisco Giants", "Arizona Diamondbacks"], "start_time": "2026-05-18 18:40", "trigger": 7.0, "condition": "below", "message": "MLB SHIFT: Giants/D-backs live total hit 7 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},

    {"sport_key": "basketball_wnba", "name": "Mystics @ Wings OVER", "teams": ["Washington Mystics", "Dallas Wings"], "start_time": "2026-05-18 17:00", "trigger": 160.0, "condition": "below", "message": "WNBA SHIFT: Mystics/Wings live total hit 160 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "basketball_wnba", "name": "Mystics @ Wings UNDER", "teams": ["Washington Mystics", "Dallas Wings"], "start_time": "2026-05-18 17:00", "trigger": 181.0, "condition": "above", "message": "WNBA SHIFT: Mystics/Wings live total hit 181 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "basketball_wnba", "name": "Sun @ Fire OVER", "teams": ["Connecticut Sun", "Portland Fire"], "start_time": "2026-05-18 19:00", "trigger": 160.0, "condition": "below", "message": "WNBA SHIFT: Sun/Fire live total hit 160 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "basketball_wnba", "name": "Sun @ Fire UNDER", "teams": ["Connecticut Sun", "Portland Fire"], "start_time": "2026-05-18 19:00", "trigger": 185.0, "condition": "above", "message": "WNBA SHIFT: Sun/Fire live total hit 185 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},

    {"sport_key": "basketball_nba", "name": "Spurs @ Thunder OVER", "teams": ["San Antonio Spurs", "Oklahoma City Thunder"], "start_time": "2026-05-18 17:30", "trigger": 208.0, "condition": "below", "message": "NBA SHIFT: Spurs/Thunder live total hit 208 or lower. HIT OVER.", "sent": False, "start_alert_sent": False},
    {"sport_key": "basketball_nba", "name": "Spurs @ Thunder UNDER", "teams": ["San Antonio Spurs", "Oklahoma City Thunder"], "start_time": "2026-05-18 17:30", "trigger": 240.0, "condition": "above", "message": "NBA SHIFT: Spurs/Thunder live total hit 240 or higher. HIT UNDER.", "sent": False, "start_alert_sent": False},
]


def send_text(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_FROM_NUMBER,
        to=ALERT_TO_NUMBER
    )
    print(f"TEXT SENT: {message}")


def parse_manual_start_time(watch):
    return datetime.strptime(watch["start_time"], "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TIMEZONE)


def watch_is_active(watch):
    now = datetime.now(LOCAL_TIMEZONE)
    start = parse_manual_start_time(watch)
    active_end = start + timedelta(hours=ACTIVE_WINDOW_HOURS_AFTER)

    # IMPORTANT FIX:
    # A game does NOT become active before its own start time.
    return start <= now <= active_end


def maybe_send_start_alert(watch):
    now = datetime.now(LOCAL_TIMEZONE)
    start = parse_manual_start_time(watch)

    minutes_until_start = (start - now).total_seconds() / 60

    if 0 <= minutes_until_start <= START_ALERT_MINUTES_BEFORE:
        if not watch["start_alert_sent"]:
            start_text = start.strftime("%I:%M %p").lstrip("0")
            send_text(f"SHIFT BOT: {watch['name']} starts at {start_text} Arizona time. Monitoring will activate at game start.")
            watch["start_alert_sent"] = True


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


def trigger_hit(current_total, watch):
    if watch["condition"] == "below":
        return current_total <= watch["trigger"]

    if watch["condition"] == "above":
        return current_total >= watch["trigger"]

    return False


def next_wake_seconds():
    now = datetime.now(LOCAL_TIMEZONE)
    next_start_time = None

    for watch in WATCHLIST:
        if watch["sent"]:
            continue

        start = parse_manual_start_time(watch)

        if start > now:
            if next_start_time is None or start < next_start_time:
                next_start_time = start

    if next_start_time is None:
        return DORMANT_CHECK_SECONDS

    seconds_until = int((next_start_time - now).total_seconds())

    return max(30, min(DORMANT_CHECK_SECONDS, seconds_until))


def print_dormant_games():
    now = datetime.now(LOCAL_TIMEZONE)

    for watch in WATCHLIST:
        start = parse_manual_start_time(watch)

        if now < start:
            print(f"DORMANT: {watch['name']} starts at {start.strftime('%I:%M %p').lstrip('0')}")
        elif watch["sent"]:
            print(f"DONE: {watch['name']} alert already sent")


def main():
    print("SHIFT bot started.")
    print("Per-game start-time activation mode active.")
    send_text("SHIFT bot started. Per-game activation mode active.")

    while True:
        try:
            active_watches = []

            for watch in WATCHLIST:
                maybe_send_start_alert(watch)

                if watch_is_active(watch) and not watch["sent"]:
                    active_watches.append(watch)

            if not active_watches:
                print_dormant_games()
                sleep_seconds = next_wake_seconds()
                print(f"Dormant mode. No active games. Checking again in {sleep_seconds} seconds.")
                time.sleep(sleep_seconds)
                continue

            print("ACTIVE WATCHES:")
            for watch in active_watches:
                print(f"ACTIVE: {watch['name']}")

            active_sport_keys = sorted(set(watch["sport_key"] for watch in active_watches))

            for sport_key in active_sport_keys:
                games = get_live_totals(sport_key)

                for watch in active_watches:
                    matched_game_found = False

                    for game in games:
                        if not teams_match(game, watch):
                            continue

                        matched_game_found = True
                        current_total = extract_total(game)

                        if current_total is None:
                            print(f"{watch['name']}: No live total found yet.")
                            continue

                        print(f"{watch['name']} live total: {current_total}")

                        if trigger_hit(current_total, watch):
                            send_text(f"{watch['message']} Current total: {current_total}")
                            watch["sent"] = True

                    if not matched_game_found:
                        print(f"{watch['name']}: Game not found yet in Odds API.")

            print(f"Active mode. Checking again in {ACTIVE_CHECK_SECONDS} seconds.")
            time.sleep(ACTIVE_CHECK_SECONDS)

        except Exception as e:
            print("Error:", e)
            time.sleep(300)


if __name__ == "__main__":
    main()
