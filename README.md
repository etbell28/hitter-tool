# Hitter Tool

This is the starter version of your MLB home run prediction tool.

You do not need to know coding to use this first version. The workflow is:

1. Put today's hitter/matchup data into `work/sample_slate.csv`.
2. Run the tool.
3. Open the ranked report in `outputs/hr_rankings.csv` and `outputs/hr_rankings.md`.

The model is intentionally transparent. Every player receives an `HR Score` from five parts:

- Power Score
- Pitcher Vulnerability Score
- Environment Score
- Lineup Opportunity Score
- Platoon Matchup Score

## How To Run It

From this folder, run:

```bash
python3 hitter_tool.py
```

If that gives you a developer-tools message on Mac, use this Codex-bundled Python instead:

```bash
/Users/ebell/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 hitter_tool.py
```

The tool will read:

```text
work/sample_slate.csv
```

and write:

```text
outputs/hr_rankings.csv
outputs/hr_rankings.md
```

## What The Columns Mean

Required hitter fields:

- `player`
- `team`
- `opponent`
- `pitcher`
- `hitter_hand`
- `pitcher_hand`
- `barrel_pct`
- `iso`
- `avg_exit_velocity`
- `hard_hit_pct`
- `hr_total`

Required pitcher fields:

- `pitcher_barrel_pct_allowed`
- `pitcher_hr_allowed`
- `pitcher_hr_allowed_vs_lhh`
- `pitcher_hr_allowed_vs_rhh`

Required environment and lineup fields:

- `ballpark`
- `weather_temp`
- `wind_speed`
- `wind_direction`
- `batting_order`
- `confirmed_lineup`

Optional value/public fields:

- `public_attention`
- `odds`

## Important First Rule

If `confirmed_lineup` is `No`, the hitter is removed from the ranked plays.

That is one of the main edges of this project.

## Daily Data Collection

Use the beginner collection guide here:

```text
DATA_COLLECTION_GUIDE.md
```

Use this blank upload template when starting a slate:

```text
outputs/hitter_tool_upload_template.csv
```

Required and planned data sources are tracked here:

```text
SOURCES.md
INTEGRATION_PLAN.md
```

## Automated Late Slate

To build a slate for games that have not started yet and generate rankings, run:

```bash
/Users/ebell/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 run_late_slate.py
```

To build the full day of non-final games and generate rankings, run:

```bash
/Users/ebell/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 run_full_slate.py
```

That command pulls:

- confirmed MLB lineups
- batting order
- probable pitchers
- player handedness
- venue/weather
- Baseball Savant hitter and pitcher metrics

Then it writes:

```text
outputs/auto_slate_full.csv
outputs/auto_slate_late.csv
outputs/hr_rankings.csv
outputs/hr_rankings.xlsx
outputs/hr_rankings.md
outputs/hitter_tool_dashboard.html
outputs/daily/collected_slate_YYYY-MM-DD_all.csv
outputs/daily/collected_slate_YYYY-MM-DD_upcoming.csv
outputs/daily/hr_rankings_YYYY-MM-DD.csv
outputs/daily/hr_rankings_YYYY-MM-DD.xlsx
outputs/daily/top_20_hr_hitters_YYYY-MM-DD.csv
```

## Dashboard

The dashboard is a local HTML view:

```text
outputs/hitter_tool_dashboard.html
```

It includes:

- Top HR targets with badge filters and search
- Best weather targets
- 2-leg, 3-leg, and 4-leg pairing tabs
- Game-by-game boards
- MLB/RotoWire lineup cross-check status

## Phone Link / Vercel

The deployable dashboard site lives here:

```text
dashboard_site/
```

To refresh that folder from the latest generated dashboard, run:

```bash
/Users/ebell/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 publish_dashboard.py
```

Then deploy `dashboard_site/` to Vercel.

For full GitHub + Vercel automation, follow:

```text
GITHUB_VERCEL_SETUP.md
```
