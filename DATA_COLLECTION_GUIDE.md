# Hitter Tool Data Collection Guide

This is the beginner workflow for building a daily slate.

The goal is not to collect every possible baseball stat. The goal is to collect the most important fields quickly and consistently.

## Daily Workflow

1. Open `outputs/hitter_tool_upload_template.csv`.
2. Save a copy as `work/sample_slate.csv`.
3. Add one row for each hitter you want to evaluate.
4. Run the Hitter Tool.
5. Open the results in `outputs/hr_rankings.csv` or `outputs/hr_rankings.md`.

## Source 1: Confirmed Lineups

Use this first.

Recommended beginner source:

- MLB Starting Lineups: https://www.mlb.com/starting-lineups
- Lineups.com MLB Lineups: https://www.lineups.com/mlb/lineups/

Fill these columns from lineups:

- `player`
- `team`
- `opponent`
- `pitcher`
- `batting_order`
- `confirmed_lineup`

Use `Yes` only when the lineup is confirmed. If the lineup is projected, use `No` or wait.

## Source 2: Hitter Power Metrics

Recommended beginner source:

- Baseball Savant Custom Leaderboard: https://baseballsavant.mlb.com/custom-leaderboard

Use the Batters view and add these columns:

- `Barrel%`
- `ISO`
- `Avg EV (MPH)`
- `Hard Hit %`
- `HR`

Copy those values into:

- `barrel_pct`
- `iso`
- `avg_exit_velocity`
- `hard_hit_pct`
- `hr_total`

## Source 3: Pitcher Vulnerability Metrics

Recommended beginner source:

- Baseball Savant Custom Leaderboard: https://baseballsavant.mlb.com/custom-leaderboard

Use the Pitchers view and add:

- `Barrel%`
- `HR`

Copy those values into:

- `pitcher_barrel_pct_allowed`
- `pitcher_hr_allowed`

For the first manual version, if you do not have split HR allowed by hitter side, use an estimate:

- Put total HR allowed to lefties in `pitcher_hr_allowed_vs_lhh` if you have it.
- Put total HR allowed to righties in `pitcher_hr_allowed_vs_rhh` if you have it.
- If you do not have splits yet, put half of the pitcher's total HR allowed in each split column.

## Source 4: Park And Weather

For now, keep this simple.

Use any reliable game weather page and fill:

- `ballpark`
- `weather_temp`
- `wind_speed`
- `wind_direction`

For `wind_direction`, use simple wording:

- `out to center`
- `out to left`
- `out to right`
- `in from center`
- `neutral`

For `park_hr_factor`, use `100` if you do not know the park factor yet.

## Source 5: Optional Betting Context

These are not used to inflate famous players. They are only used to label value and longshot plays.

Fill:

- `public_attention`: `High`, `Medium`, or `Low`
- `odds`: American odds like `350`, `500`, or `900`

If you do not have them, leave them blank.

## Minimum Useful Version

If you are short on time, fill only confirmed starters and obvious candidates first.

Start with:

- Top 4 hitters in each confirmed lineup
- Any hitter with strong barrel rate or ISO
- Any hitter facing a vulnerable pitcher

That will usually produce a useful daily list faster than trying to enter every hitter on the slate.

