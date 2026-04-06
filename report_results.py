import csv
from collections import defaultdict

TRACKER_FILE = "tracker_log.csv"

overall = {"wins": 0, "losses": 0, "pushes": 0, "units": 0.0}
by_sport = defaultdict(lambda: {"wins": 0, "losses": 0, "pushes": 0, "units": 0.0})
by_trigger = defaultdict(lambda: {"wins": 0, "losses": 0, "pushes": 0, "units": 0.0})


with open(TRACKER_FILE, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["status"] != "settled":
            continue

        sport = row["sport"]
        trigger = row["trigger_type"]
        result = row["result"]
        units = float(row["units"])

        overall["units"] += units
        by_sport[sport]["units"] += units
        by_trigger[trigger]["units"] += units

        if result == "win":
            overall["wins"] += 1
            by_sport[sport]["wins"] += 1
            by_trigger[trigger]["wins"] += 1
        elif result == "loss":
            overall["losses"] += 1
            by_sport[sport]["losses"] += 1
            by_trigger[trigger]["losses"] += 1
        elif result == "push":
            overall["pushes"] += 1
            by_sport[sport]["pushes"] += 1
            by_trigger[trigger]["pushes"] += 1

print("\nOVERALL")
print(overall)

print("\nBY SPORT")
for sport, stats in by_sport.items():
    print(sport, stats)

print("\nBY TRIGGER")
for trigger, stats in by_trigger.items():
    print(trigger, stats)
