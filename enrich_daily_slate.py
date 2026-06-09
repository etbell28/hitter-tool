import csv
import json
import re
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parent
SOURCE_CSV = ROOT / "outputs" / "data_1_export.csv"
ENRICHED_CSV = ROOT / "outputs" / "data_1_enriched.csv"


PARK_HR_FACTORS = {
    "Angel Stadium": 101,
    "Busch Stadium": 90,
    "Camden Yards": 108,
    "Chase Field": 101,
    "Citi Field": 95,
    "Citizens Bank Park": 112,
    "Coors Field": 120,
    "Dodger Stadium": 104,
    "Fenway Park": 102,
    "George M. Steinbrenner Field": 105,
    "Great American Ball Park": 121,
    "Kauffman Stadium": 92,
    "loanDepot park": 89,
    "Minute Maid Park": 103,
    "Nationals Park": 101,
    "Oracle Park": 85,
    "Oriole Park at Camden Yards": 108,
    "Petco Park": 91,
    "PNC Park": 94,
    "Progressive Field": 100,
    "Rogers Centre": 105,
    "Sutter Health Park": 106,
    "T-Mobile Park": 96,
    "Target Field": 99,
    "Truist Park": 106,
    "Wrigley Field": 104,
    "Yankee Stadium": 119,
}


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def simple_name(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]", "", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def team_key(value):
    team = str(value or "").strip().upper()
    aliases = {
        "NY": "NYY",
    }
    return aliases.get(team, team)


def weather_parts(weather):
    temp = weather.get("temp", "")
    wind = weather.get("wind", "")
    speed_match = re.search(r"(\d+)", wind)
    speed = speed_match.group(1) if speed_match else ""
    direction = wind.split(",", 1)[1].strip() if "," in wind else wind
    return temp, speed, direction


def game_feed(game_pk):
    return fetch_json(f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live")


def boxscore(game_pk):
    return fetch_json(f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore")


def build_daily_context(run_date):
    schedule = fetch_json(
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={run_date}&hydrate=probablePitcher,team,linescore"
    )
    context = {}

    for day in schedule.get("dates", []):
        for game in day.get("games", []):
            game_pk = game["gamePk"]
            feed = game_feed(game_pk)
            box = boxscore(game_pk)
            venue = feed["gameData"].get("venue", {}).get("name", "")
            weather = feed["gameData"].get("weather", {})
            temp, wind_speed, wind_direction = weather_parts(weather)
            park_factor = PARK_HR_FACTORS.get(venue, 100)

            for side in ("away", "home"):
                team = box["teams"][side]
                team_abbr = team["team"]["abbreviation"]
                batters = team.get("batters", [])
                for batting_slot, player_id in enumerate(batters[:9], start=1):
                    player = team["players"].get(f"ID{player_id}", {})
                    full_name = player.get("person", {}).get("fullName", "")
                    context[(team_key(team_abbr), simple_name(full_name))] = {
                        "batting_order": batting_slot,
                        "confirmed_lineup": "Yes",
                        "ballpark": venue,
                        "park_hr_factor": park_factor,
                        "weather_temp": temp,
                        "wind_speed": wind_speed,
                        "wind_direction": wind_direction,
                    }
    return context


def ensure_columns(headers, columns):
    headers = list(headers)
    for column in columns:
        if column not in headers:
            headers.append(column)
    return headers


def main():
    run_date = date.today().isoformat()
    if not SOURCE_CSV.exists():
        raise SystemExit(f"Missing source CSV: {SOURCE_CSV}")

    context = build_daily_context(run_date)
    with SOURCE_CSV.open(newline="") as file:
        rows = list(csv.reader(file))

    headers = ensure_columns(
        rows[0],
        [
            "ballpark",
            "park_hr_factor",
            "weather_temp",
            "wind_speed",
            "wind_direction",
            "batting_order",
            "confirmed_lineup",
            "public_attention",
        ],
    )
    index = {name: position for position, name in enumerate(headers)}
    enriched = [headers]
    matched = 0

    for raw_row in rows[1:]:
        row = raw_row + [""] * (len(headers) - len(raw_row))
        key = (team_key(row[index["team"]]), simple_name(row[index["player"]]))
        player_context = context.get(key)
        if player_context:
            matched += 1
            for column, value in player_context.items():
                row[index[column]] = value
        elif "confirmed_lineup" in index:
            row[index["confirmed_lineup"]] = "No"
        enriched.append(row)

    ENRICHED_CSV.parent.mkdir(parents=True, exist_ok=True)
    with ENRICHED_CSV.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(enriched)

    print(f"Matched {matched} hitters to confirmed MLB lineups.")
    print(f"Wrote {ENRICHED_CSV}")


if __name__ == "__main__":
    main()
