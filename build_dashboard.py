import json
from itertools import combinations
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
RANKINGS_CSV = OUTPUTS / "hr_rankings.csv"
LATE_SLATE_CSV = OUTPUTS / "auto_slate_late.csv"
FULL_SLATE_CSV = OUTPUTS / "auto_slate_full.csv"
DASHBOARD_HTML = OUTPUTS / "hitter_tool_dashboard.html"


def clean(value, default=""):
    if pd.isna(value):
        return default
    return value


def json_safe(value):
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def records(frame):
    return [
        {key: json_safe(value) for key, value in row.items()}
        for row in frame.to_dict("records")
    ]


def number(value, default=0.0):
    if pd.isna(value) or value == "":
        return default
    return float(value)


def badges_for(row):
    score = number(row.get("hr_score"))
    power = number(row.get("power_score"))
    pitcher = number(row.get("pitcher_score"))
    order = number(row.get("batting_order"), 9)
    env = number(row.get("environment_score"))
    badges = []

    if score >= 76:
        badges.append("BEST PICK")
    if power >= 75 and pitcher >= 55:
        badges.append("STAR + FIRE")
    if power >= 75 and pitcher < 45:
        badges.append("FIRE / TOUGH SP")
    if score >= 58 and order >= 5:
        badges.append("SLEEPER PICK")
    if env >= 70:
        badges.append("WEATHER EDGE")
    if pitcher >= 65:
        badges.append("PITCHER TARGET")
    return badges or ["WATCH"]


def primary_badge(row):
    return badges_for(row)[0]


def badge_class(label):
    return {
        "BEST PICK": "gold",
        "STAR + FIRE": "fire",
        "FIRE / TOUGH SP": "red",
        "SLEEPER PICK": "teal",
        "WEATHER EDGE": "green",
        "PITCHER TARGET": "red",
        "WATCH": "muted",
    }.get(label, "muted")


def confirmed_lineup(value):
    return str(value or "").strip().lower() in {"yes", "y", "true", "1"}


def game_key(row):
    teams = sorted([str(row["team"]), str(row["opponent"])])
    return f"{teams[0]}-{teams[1]}-{row['ballpark']}"


def pairing_payload(rankings, size, limit=8):
    candidates = rankings.head(30).copy()
    pairs = []
    for group in combinations(candidates.to_dict("records"), size):
        avg_score = sum(number(row["hr_score"]) for row in group) / size
        min_score = min(number(row["hr_score"]) for row in group)
        teams = [row["team"] for row in group]
        unique_teams = set(teams)
        games = {
            "-".join(sorted([str(row["team"]), str(row["opponent"])])) + f"-{row['ballpark']}"
            for row in group
        }
        max_game_exposure = max(
            sum(
                1
                for row in group
                if "-".join(sorted([str(row["team"]), str(row["opponent"])])) + f"-{row['ballpark']}" == game
            )
            for game in games
        )
        avg_environment = sum(number(row.get("environment_score")) for row in group) / size
        projected_count = sum(not confirmed_lineup(row.get("confirmed_lineup")) for row in group)
        badge_text = " / ".join(row.get("badge_summary", "WATCH") for row in group)
        edge_types = {
            edge
            for row in group
            for edge in row.get("badges", ["WATCH"])
            if edge in {"BEST PICK", "STAR + FIRE", "WEATHER EDGE", "PITCHER TARGET", "SLEEPER PICK"}
        }

        # General pairings should be more independent than a simple top-N list.
        # Same-team stacks can be useful, but they belong in a separate stack view.
        if len(unique_teams) < size:
            continue
        if max_game_exposure > 2:
            continue
        if size == 2 and max_game_exposure == 2 and avg_environment < 75:
            continue

        diversification_bonus = len(games) * 0.75 + len(unique_teams) * 0.35
        edge_bonus = min(len(edge_types), 3) * 0.45
        weather_stack_bonus = 0.55 if max_game_exposure == 2 and avg_environment >= 75 else 0
        floor_penalty = max(0, 60 - min_score) * 0.35
        projected_penalty = projected_count * 0.45
        combo_score = (
            avg_score
            + diversification_bonus
            + edge_bonus
            + weather_stack_bonus
            - floor_penalty
            - projected_penalty
        )

        risk = "Aggressive" if min_score < 58 or size >= 4 else "Balanced"
        if avg_score >= 70:
            risk = "Premium"
        if projected_count:
            risk = f"{risk} / Projected"

        reasons = []
        if len(games) == size:
            reasons.append("different games")
        elif avg_environment >= 75:
            reasons.append("weather stack")
        if edge_types:
            reasons.append(", ".join(sorted(edge_types)))
        if min_score >= 60:
            reasons.append("score floor")

        pairs.append(
            {
                "names": " + ".join(row["player"] for row in group),
                "avg_score": round(avg_score, 1),
                "combo_score": round(combo_score, 1),
                "risk": risk,
                "badges": badge_text,
                "reason": " · ".join(reasons),
            }
        )
    return sorted(pairs, key=lambda item: item["combo_score"], reverse=True)[:limit]


def apply_badges(rankings):
    rankings = rankings.copy()
    rankings["badges"] = rankings.apply(badges_for, axis=1)
    rankings["badge"] = rankings.apply(primary_badge, axis=1)
    rankings["badge_class"] = rankings["badge"].map(badge_class)
    rankings["badge_summary"] = rankings["badges"].apply(lambda values: " + ".join(values))
    rankings["badge_classes"] = rankings["badges"].apply(lambda values: [badge_class(value) for value in values])
    return rankings


def slate_path():
    return FULL_SLATE_CSV if FULL_SLATE_CSV.exists() else LATE_SLATE_CSV


def build_payload():
    if not RANKINGS_CSV.exists():
        raise SystemExit(f"Missing rankings file: {RANKINGS_CSV}")
    active_slate = slate_path()
    if not active_slate.exists():
        raise SystemExit(f"Missing slate file: {active_slate}")

    rankings = apply_badges(pd.read_csv(RANKINGS_CSV))
    slate = pd.read_csv(active_slate)
    confirmed_rankings = rankings[rankings["confirmed_lineup"].apply(confirmed_lineup)].copy()

    top20 = confirmed_rankings.head(20).copy()
    projected_top20 = rankings.head(20).copy()
    weather = (
        rankings.groupby(["ballpark", "wind_direction", "weather_temp"], dropna=False)
        .agg(
            environment_score=("environment_score", "mean"),
            top_player=("player", "first"),
            top_score=("hr_score", "max"),
            teams=("team", lambda values: " / ".join(sorted(set(values))[:4])),
        )
        .reset_index()
        .sort_values(["environment_score", "top_score"], ascending=False)
        .head(8)
    )

    games = []
    slate["game_key"] = slate.apply(game_key, axis=1)
    ranking_lookup = rankings.set_index(["player", "team"]).to_dict("index")
    for key, game_rows in slate.groupby("game_key", sort=False):
        teams = list(dict.fromkeys(game_rows["team"].tolist()))
        ballpark = clean(game_rows["ballpark"].iloc[0])
        temp = clean(game_rows["weather_temp"].iloc[0])
        wind = clean(game_rows["wind_direction"].iloc[0])
        disagreement_count = int((game_rows.get("lineup_disagreement", "") == "Yes").sum())
        players = []
        for _, slate_row in game_rows.iterrows():
            rank_info = ranking_lookup.get((slate_row["player"], slate_row["team"]), {})
            if not rank_info:
                continue
            player = {
                "player": slate_row["player"],
                "team": slate_row["team"],
                "order": int(number(slate_row["batting_order"], 9)),
                "pitcher": slate_row["pitcher"],
                "score": round(number(rank_info.get("hr_score")), 1),
                "rank": int(number(rank_info.get("rank"), 999)),
                "badge": rank_info.get("badge", "WATCH"),
                "badge_class": rank_info.get("badge_class", "muted"),
                "badges": rank_info.get("badges", ["WATCH"]),
                "badge_classes": rank_info.get("badge_classes", ["muted"]),
                "badge_summary": rank_info.get("badge_summary", "WATCH"),
                "lineup_disagreement": slate_row.get("lineup_disagreement", "No"),
                "source_warnings": clean(slate_row.get("source_warnings", "")),
            }
            players.append(player)

        players = sorted(players, key=lambda item: item["score"], reverse=True)[:5]
        games.append(
            {
                "teams": " vs ".join(teams[:2]),
                "ballpark": ballpark,
                "temp": temp,
                "wind": wind,
                "disagreement_count": disagreement_count,
                "players": players,
            }
        )

    return {
        "date": datetime.now().strftime("%A, %B %-d, %Y"),
        "generated_at": datetime.now().strftime("%I:%M %p %Z"),
        "slate_projection": len(slate),
        "games_count": len(games),
        "confirmed_count": len(confirmed_rankings),
        "projected_count": len(rankings) - len(confirmed_rankings),
        "top20": records(top20),
        "projected_top20": records(projected_top20),
        "weather": records(weather),
        "pairings": {
            "2": pairing_payload(confirmed_rankings, 2),
            "3": pairing_payload(confirmed_rankings, 3),
            "4": pairing_payload(confirmed_rankings, 4),
        },
        "projected_pairings": {
            "2": pairing_payload(rankings, 2),
            "3": pairing_payload(rankings, 3),
            "4": pairing_payload(rankings, 4),
        },
        "games": games,
        "lineup_disagreements": int((slate.get("lineup_disagreement", "") == "Yes").sum()),
        "rotowire_found": int((slate.get("rotowire_player_found", "") == "Yes").sum()),
        "slate_size": len(slate),
        "sources": "Baseball Savant; MLB Stats API; RotoWire",
    }


def render_html(payload):
    data = json.dumps(payload, ensure_ascii=False, default=json_safe)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Hitter Tool Dashboard</title>
  <style>
    :root {{
      --bg: #130908;
      --panel: #1b1512;
      --panel-2: #071a10;
      --line: #ff4b1f;
      --line-soft: rgba(255, 75, 31, .38);
      --gold: #ffd85a;
      --amber: #ff9c2f;
      --teal: #25f4d0;
      --green: #54ff8f;
      --blue: #76c7ff;
      --red: #ff573d;
      --text: #f7efe2;
      --muted: #a99b8e;
      --shadow: 0 0 18px rgba(255, 75, 31, .28);
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}

    .shell {{
      min-height: 100vh;
      border: 4px solid var(--line);
      background:
        linear-gradient(180deg, rgba(48, 0, 0, .82), rgba(7, 18, 12, .96) 45%, rgba(12, 12, 12, .98));
    }}

    header {{
      padding: 28px clamp(18px, 4vw, 52px) 22px;
      border-bottom: 4px solid var(--amber);
      box-shadow: var(--shadow);
    }}

    .brand {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 18px;
      align-items: center;
    }}

    .mark {{
      width: 74px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border: 3px solid var(--line);
      border-radius: 50%;
      background: #240a06;
      color: var(--gold);
      font-weight: 900;
      font-size: 26px;
      box-shadow: 0 0 22px rgba(255, 75, 31, .62);
    }}

    h1 {{
      margin: 0;
      color: var(--line);
      font-family: Impact, Haettenschweiler, "Arial Black", sans-serif;
      font-size: clamp(42px, 8vw, 92px);
      line-height: .86;
      text-transform: uppercase;
      text-shadow: 0 0 12px rgba(255, 75, 31, .5);
    }}

    .sub {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .18em;
    }}

    .stats-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}

    .stat {{
      border: 1px solid var(--line-soft);
      background: rgba(40, 12, 8, .72);
      padding: 12px 16px;
      border-radius: 6px;
      min-width: 150px;
    }}

    .stat b {{
      color: var(--gold);
      font-size: 24px;
    }}

    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
    }}

    .legend, .weather-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 18px clamp(18px, 4vw, 52px);
      border-bottom: 1px solid rgba(255, 216, 90, .25);
      background: rgba(11, 15, 10, .75);
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 35px;
      padding: 8px 12px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      white-space: nowrap;
      border: 1px solid rgba(255,255,255,.18);
    }}
    .gold {{ color: var(--gold); border-color: var(--gold); box-shadow: 0 0 12px rgba(255,216,90,.22); }}
    .fire {{ color: var(--amber); border-color: var(--line); box-shadow: 0 0 12px rgba(255,75,31,.22); }}
    .teal {{ color: var(--teal); border-color: var(--teal); box-shadow: 0 0 12px rgba(37,244,208,.2); }}
    .green {{ color: var(--green); border-color: rgba(84,255,143,.65); }}
    .red {{ color: var(--red); border-color: var(--red); }}
    .muted {{ color: var(--muted); border-color: rgba(169,155,142,.35); }}

    main {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 0;
    }}

    section {{
      padding: 24px clamp(18px, 4vw, 52px);
      border-bottom: 1px solid rgba(84,255,143,.18);
    }}

    .section-title {{
      margin: 0 0 18px;
      color: var(--green);
      font-family: Impact, Haettenschweiler, "Arial Black", sans-serif;
      font-size: 28px;
      text-transform: uppercase;
    }}

    .weather-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 10px;
    }}

    .weather-target {{
      padding: 12px;
      background: rgba(3, 42, 19, .72);
      border: 1px solid rgba(84, 255, 143, .28);
      border-radius: 6px;
    }}

    .weather-target strong {{ color: var(--gold); }}
    .weather-target small {{ display: block; color: var(--muted); margin-top: 4px; }}

    .search {{
      width: min(420px, 100%);
      min-height: 39px;
      border: 1px solid rgba(255,255,255,.2);
      background: rgba(0,0,0,.28);
      color: var(--text);
      border-radius: 5px;
      padding: 9px 12px;
      font-weight: 800;
      outline: none;
    }}

    .search:focus {{
      border-color: var(--teal);
      box-shadow: 0 0 12px rgba(37,244,208,.18);
    }}

    .top-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(300px, .95fr);
      gap: 18px;
      align-items: start;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      background: rgba(14,14,14,.72);
      border: 1px solid rgba(255,75,31,.25);
      border-radius: 6px;
      overflow: hidden;
    }}

    th, td {{
      padding: 10px 9px;
      text-align: left;
      border-bottom: 1px solid rgba(255,255,255,.06);
      font-size: 13px;
    }}
    th {{
      color: var(--muted);
      text-transform: uppercase;
      font-size: 11px;
      background: rgba(255,75,31,.08);
    }}
    td.score {{
      color: var(--gold);
      font-weight: 900;
      font-size: 16px;
    }}
    td.rank {{
      color: var(--amber);
      font-weight: 900;
    }}

    .game-list {{
      display: grid;
      gap: 14px;
    }}

    .game {{
      border-left: 5px solid var(--line);
      background: rgba(24, 22, 20, .88);
      border-radius: 6px;
      overflow: hidden;
      border-top: 1px solid rgba(255,255,255,.08);
      border-right: 1px solid rgba(255,255,255,.08);
      border-bottom: 1px solid rgba(255,255,255,.08);
    }}

    .game-head {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px 18px;
      padding: 14px 16px;
      background: rgba(255,75,31,.07);
    }}

    .game-title {{
      color: var(--line);
      font-family: Impact, Haettenschweiler, "Arial Black", sans-serif;
      font-size: 24px;
      text-transform: uppercase;
      margin-right: auto;
    }}

    .meta {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }}

    .player-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 14px 16px 16px;
    }}

    .pill {{
      min-height: 44px;
      padding: 9px 12px;
      border-radius: 5px;
      background: rgba(0,0,0,.24);
      border: 1px solid rgba(255,216,90,.38);
    }}
    .pill strong {{
      display: block;
      color: var(--text);
      font-size: 13px;
      text-transform: uppercase;
    }}
    .pill span {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
    }}

    .pairing-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}

    .pairing {{
      background: rgba(16, 17, 16, .82);
      border: 1px solid rgba(255, 216, 90, .25);
      border-radius: 6px;
      padding: 13px;
    }}

    .pairing strong {{
      display: block;
      color: var(--gold);
      font-size: 14px;
      line-height: 1.35;
      text-transform: uppercase;
    }}

    .pairing small {{
      display: block;
      margin-top: 7px;
      color: var(--muted);
      font-weight: 800;
    }}

    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}

    button {{
      border: 1px solid rgba(255,255,255,.2);
      background: rgba(0,0,0,.25);
      color: var(--text);
      padding: 9px 12px;
      border-radius: 5px;
      font-weight: 900;
      text-transform: uppercase;
      cursor: pointer;
    }}
    button.active {{
      color: var(--gold);
      border-color: var(--gold);
    }}

    @media (max-width: 850px) {{
      .brand {{ grid-template-columns: 1fr; }}
      .top-layout {{ grid-template-columns: 1fr; }}
      th:nth-child(5), td:nth-child(5), th:nth-child(6), td:nth-child(6) {{ display: none; }}
      .game-title {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand">
        <div class="mark">HT</div>
        <div>
          <h1>The Hitter<br>Tool</h1>
          <div class="sub">HR Research Dashboard · {payload["date"]} · Updated {payload["generated_at"]}</div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat"><b>{payload["slate_projection"]}</b><span>Hitters Scanned</span></div>
        <div class="stat"><b>{payload["games_count"]}</b><span>Games</span></div>
        <div class="stat"><b>{payload["confirmed_count"]}</b><span>Confirmed Hitters</span></div>
        <div class="stat"><b>{payload["projected_count"]}</b><span>Projected Hitters</span></div>
        <div class="stat"><b>{payload["rotowire_found"]}/{payload["slate_size"]}</b><span>RotoWire Matches</span></div>
        <div class="stat"><b>{payload["lineup_disagreements"]}</b><span>Lineup Warnings</span></div>
      </div>
    </header>

    <div class="legend">
      <span class="badge gold">Best Pick</span>
      <span class="badge fire">Star + Fire</span>
      <span class="badge red">Fire / Tough SP</span>
      <span class="badge teal">Sleeper Pick</span>
      <span class="badge green">Weather Edge</span>
      <span class="badge red">Pitcher Target</span>
      <span class="badge muted">Watch</span>
    </div>

    <main>
      <section>
        <h2 class="section-title">Best Weather Targets Today</h2>
        <div class="weather-grid" id="weather"></div>
      </section>

      <section>
        <div class="top-layout">
          <div>
            <h2 class="section-title">Confirmed Lineup Targets</h2>
            <div class="controls">
              <button class="active" data-filter="all">All</button>
              <button data-filter="BEST PICK">Best</button>
              <button data-filter="STAR + FIRE">Great Matchup</button>
              <button data-filter="FIRE / TOUGH SP">Tough Pitcher</button>
              <button data-filter="SLEEPER PICK">Sleepers</button>
              <button data-filter="WEATHER EDGE">Weather</button>
              <input class="search" id="search" placeholder="Search player, team, pitcher">
            </div>
            <table>
              <thead>
                <tr><th>Rank</th><th>Player</th><th>Team</th><th>Score</th><th>Order</th><th>Pitcher</th><th>Badge</th></tr>
              </thead>
              <tbody id="topRows"></tbody>
            </table>
          </div>

          <div>
            <h2 class="section-title">Source Check</h2>
            <div class="weather-target">
              <strong>{payload["sources"]}</strong>
              <small>Lineup cross-check is active. Rows with disagreements are flagged in the CSV and Excel output.</small>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h2 class="section-title">Full Slate Projection</h2>
        <div class="weather-target" style="margin-bottom: 12px;">
          <strong>Includes projected and confirmed lineups.</strong>
          <small>Use this for later games before lineups lock. Confirmed-lineup targets above remain the cleaner board.</small>
        </div>
        <table>
          <thead>
            <tr><th>Rank</th><th>Player</th><th>Team</th><th>Score</th><th>Order</th><th>Pitcher</th><th>Status</th><th>Badge</th></tr>
          </thead>
          <tbody id="projectedRows"></tbody>
        </table>
      </section>

      <section>
        <h2 class="section-title">Confirmed HR Pairings</h2>
        <div class="controls">
          <button class="active" data-pairing="2">2-Leg</button>
          <button data-pairing="3">3-Leg</button>
          <button data-pairing="4">4-Leg</button>
        </div>
        <div class="pairing-grid" id="pairings"></div>
      </section>

      <section>
        <h2 class="section-title">Full Slate Projection Pairings</h2>
        <div class="controls">
          <button class="active" data-projected-pairing="2">2-Leg</button>
          <button data-projected-pairing="3">3-Leg</button>
          <button data-projected-pairing="4">4-Leg</button>
        </div>
        <div class="pairing-grid" id="projectedPairings"></div>
      </section>

      <section>
        <h2 class="section-title">Game Boards</h2>
        <div class="controls">
          <button class="active" data-game-filter="all">All Games</button>
          <button data-game-filter="warnings">Warnings</button>
          <button data-game-filter="top">Top Targets</button>
        </div>
        <div class="game-list" id="games"></div>
      </section>
    </main>
  </div>

  <script>
    const payload = {data};
    const topRows = document.querySelector("#topRows");
    const weather = document.querySelector("#weather");
    const games = document.querySelector("#games");
    const pairings = document.querySelector("#pairings");
    const projectedRows = document.querySelector("#projectedRows");
    const projectedPairings = document.querySelector("#projectedPairings");
    const search = document.querySelector("#search");
    let activeFilter = "all";
    let activeGameFilter = "all";

    function fmt(value, fallback = "") {{
      return value === null || value === undefined || Number.isNaN(value) ? fallback : value;
    }}

    function renderWeather() {{
      weather.innerHTML = payload.weather.map((item, index) => `
        <div class="weather-target">
          <strong>#${{index + 1}} · ${{fmt(item.ballpark)}} · ${{Number(item.environment_score || 0).toFixed(1)}} ENV</strong>
          <small>${{fmt(item.weather_temp)}}° · ${{fmt(item.wind_direction, "Wind neutral")}} · Top target: ${{fmt(item.top_player)}} (${{Number(item.top_score || 0).toFixed(1)}})</small>
        </div>
      `).join("");
    }}

    function matchesSearch(row) {{
      const query = (search?.value || "").trim().toLowerCase();
      if (!query) return true;
      return [row.player, row.team, row.opponent, row.pitcher, row.badge_summary]
        .join(" ")
        .toLowerCase()
        .includes(query);
    }}

    function renderTop(filter = activeFilter) {{
      activeFilter = filter;
      const rows = payload.top20.filter(row => (filter === "all" || (row.badges || []).includes(filter)) && matchesSearch(row));
      topRows.innerHTML = rows.map(row => `
        <tr>
          <td class="rank">${{row.rank}}</td>
          <td><strong>${{row.player}}</strong></td>
          <td>${{row.team}}</td>
          <td class="score">${{Number(row.hr_score || 0).toFixed(1)}}</td>
          <td>${{row.batting_order}}</td>
          <td>${{row.pitcher}}</td>
          <td>${{(row.badges || ["WATCH"]).map((badge, idx) => `<span class="badge ${{(row.badge_classes || ["muted"])[idx] || "muted"}}">${{badge}}</span>`).join(" ")}}</td>
        </tr>
      `).join("") || `<tr><td colspan="7">No targets in this filter.</td></tr>`;
    }}

    function renderProjectedRows() {{
      projectedRows.innerHTML = payload.projected_top20.map(row => `
        <tr>
          <td class="rank">${{row.rank}}</td>
          <td><strong>${{row.player}}</strong></td>
          <td>${{row.team}}</td>
          <td class="score">${{Number(row.hr_score || 0).toFixed(1)}}</td>
          <td>${{row.batting_order}}</td>
          <td>${{row.pitcher}}</td>
          <td>${{String(row.confirmed_lineup || "").toLowerCase() === "yes" ? "Confirmed" : "Projected"}}</td>
          <td>${{(row.badges || ["WATCH"]).map((badge, idx) => `<span class="badge ${{(row.badge_classes || ["muted"])[idx] || "muted"}}">${{badge}}</span>`).join(" ")}}</td>
        </tr>
      `).join("") || `<tr><td colspan="8">No projection targets available.</td></tr>`;
    }}

    function renderPairings(size = "2") {{
      const rows = payload.pairings[size] || [];
      pairings.innerHTML = rows.map((row, index) => `
        <div class="pairing">
          <strong>#${{index + 1}} · ${{row.names}}</strong>
          <small>Avg HR Score: ${{Number(row.avg_score || 0).toFixed(1)}} · ${{row.risk}} · ${{row.reason || "balanced edge mix"}} · ${{row.badges}}</small>
        </div>
      `).join("");
    }}

    function renderProjectedPairings(size = "2") {{
      const rows = payload.projected_pairings[size] || [];
      projectedPairings.innerHTML = rows.map((row, index) => `
        <div class="pairing">
          <strong>#${{index + 1}} · ${{row.names}}</strong>
          <small>Avg HR Score: ${{Number(row.avg_score || 0).toFixed(1)}} · ${{row.risk}} · ${{row.reason || "balanced edge mix"}} · ${{row.badges}}</small>
        </div>
      `).join("");
    }}

    function renderGames(filter = activeGameFilter) {{
      activeGameFilter = filter;
      const visibleGames = payload.games.filter(game => {{
        if (filter === "warnings") return game.disagreement_count > 0;
        if (filter === "top") return game.players.some(player => player.rank <= 10);
        return true;
      }});
      games.innerHTML = visibleGames.map(game => `
        <article class="game">
          <div class="game-head">
            <div class="game-title">${{game.teams}}</div>
            <div class="meta">${{game.ballpark}}</div>
            <div class="meta">${{game.temp}}°</div>
            <div class="meta">${{game.wind}}</div>
            <span class="badge ${{game.disagreement_count ? "red" : "green"}}">${{game.disagreement_count ? game.disagreement_count + " lineup warnings" : "lineups matched"}}</span>
          </div>
          <div class="player-pills">
            ${{game.players.map(player => `
              <div class="pill">
                <strong>#${{player.rank}} ${{player.player}}</strong>
                <span>${{player.team}} · order ${{player.order}} · ${{player.score.toFixed(1)}} HR · ${{player.badge_summary}}</span>
              </div>
            `).join("")}}
          </div>
        </article>
      `).join("") || `<div class="weather-target"><strong>No games match this filter.</strong></div>`;
    }}

    document.querySelectorAll("button[data-filter]").forEach(button => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll("button[data-filter]").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        renderTop(button.dataset.filter);
      }});
    }});

    document.querySelectorAll("button[data-pairing]").forEach(button => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll("button[data-pairing]").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        renderPairings(button.dataset.pairing);
      }});
    }});

    document.querySelectorAll("button[data-projected-pairing]").forEach(button => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll("button[data-projected-pairing]").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        renderProjectedPairings(button.dataset.projectedPairing);
      }});
    }});

    document.querySelectorAll("button[data-game-filter]").forEach(button => {{
      button.addEventListener("click", () => {{
        document.querySelectorAll("button[data-game-filter]").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        renderGames(button.dataset.gameFilter);
      }});
    }});

    search?.addEventListener("input", () => renderTop(activeFilter));

    renderWeather();
    renderTop();
    renderProjectedRows();
    renderPairings("2");
    renderProjectedPairings("2");
    renderGames();
  </script>
</body>
</html>
"""


def main():
    payload = build_payload()
    DASHBOARD_HTML.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
