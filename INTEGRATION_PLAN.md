# Hitter Tool Integration Plan

This is the source-by-source plan for expanding The Hitter Tool without turning the daily workflow back into manual data entry.

## Current Baseline

Already working:

- MLB public feed for schedule, lineups, probable pitchers, handedness, weather, boxscores, and result auditing.
- Baseball Savant custom leaderboard CSVs for hitter and pitcher Statcast metrics.
- Daily CSV and Excel output.
- Daily prediction archive.
- Nightly result audit automation.

## Integration Order

### 1. RotoWire / MLB Lineups Cross-Check

Goal:

- Keep MLB as the primary official lineup source.
- Use RotoWire as a second opinion for confirmed lineup status, batting order, and late changes.

Why first:

- Lineup accuracy is the biggest operational edge.
- RotoWire pages are publicly reachable.

Implementation:

- Add a `lineup_sources` step that stores:
  - `mlb_confirmed_lineup`
  - `rotowire_confirmed_lineup`
  - `lineup_disagreement`
  - `lineup_sources_used`
- If MLB and RotoWire disagree, keep the player but flag the row.
- Do not silently overwrite MLB official data.

Status:

- Planned next.

### 2. Ballpark Pal Environment Layer

Goal:

- Improve the park/weather portion of the Environment Score.
- Replace or supplement the current static `park_hr_factor` lookup table.

Why second:

- Weather/park conditions materially affect HR probability.
- Current tool uses MLB weather plus a hardcoded park factor table.

Implementation:

- Add fields:
  - `ballpark_pal_hr_factor`
  - `ballpark_pal_run_environment`
  - `ballpark_pal_weather_note`
  - `environment_sources_used`
- Use Ballpark Pal/VSiN environment data as an environment modifier, not as a replacement for hitter and pitcher skill.

Status:

- Planned after lineup cross-check.

### 3. OddsShopper / Action Network Odds Layer

Goal:

- Add HR odds and market context.
- Improve `Best Value` and `Longshot` labels.

Why third:

- Odds should not decide who has the best HR probability.
- Odds should decide whether a model-ranked hitter is a good price.

Implementation:

- Add fields:
  - `best_hr_odds`
  - `best_hr_book`
  - `implied_probability`
  - `model_probability_estimate`
  - `value_gap`
  - `odds_sources_used`
- Keep raw `HR Score` independent from sportsbook odds.
- Use odds only for value tags and betting report sections.

Status:

- Planned after environment layer.

### 4. FanGraphs Validation Layer

Goal:

- Add non-Statcast validation metrics from FanGraphs.
- Use FanGraphs to cross-check ISO, plate appearances, batted-ball profile, and pitcher context.

Why fourth:

- FanGraphs blocked basic scripted access in the first availability test.
- This may require a supported export workflow, manual CSV drop, or approved API path.

Implementation:

- Add optional import path:
  - `inputs/fangraphs_batters.csv`
  - `inputs/fangraphs_pitchers.csv`
- Merge by player name/team or player IDs when available.
- Add fields:
  - `fangraphs_iso`
  - `fangraphs_fb_pct`
  - `fangraphs_pull_pct`
  - `fangraphs_pa`
  - `fangraphs_sources_used`

Status:

- Future integration, likely CSV-import first.

### 5. VSiN Context Layer

Goal:

- Add betting-market and environment notes where public.
- Use VSiN mainly as a contextual review source, not a core scoring source.

Implementation:

- Add daily notes field:
  - `vsin_context_note`
  - `vsin_sources_used`
- Use this for report commentary and sanity checks.

Status:

- Future integration.

## Source Rule

The tool should report three categories:

- `sources_used`: sources actually pulled into the run.
- `sources_checked`: sources checked but not used in scoring.
- `source_warnings`: missing data, blocked access, disagreement, or low confidence.

## Immediate Next Build

The next code change should be RotoWire lineup cross-check scaffolding:

1. Fetch RotoWire daily lineups page.
2. Extract team/player/order/status if reliably available.
3. Add source fields to the collected slate.
4. Add warnings when MLB and RotoWire disagree.
5. Preserve MLB as the primary official lineup source.

