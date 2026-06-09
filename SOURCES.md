# Hitter Tool Source Registry

This file is the required source list for The Hitter Tool.

The tool should never claim it used a source unless that source is actually integrated into the data pipeline or manually supplied for that run.

## Required Core Sources

| Source | Purpose | Current Status |
|---|---|---|
| Baseball Savant | Statcast hitter and pitcher leaderboards: Barrel %, Hard Hit %, Avg EV, EV50-style metrics, xSLG, xISO, xwOBA, bat speed, pull %, FB%, HR, ISO | Integrated |
| MLB Stats API / MLB Starting Lineups | Official schedule, probable pitchers, confirmed lineups, batting order, handedness, boxscores, actual HR results | Integrated |
| FanGraphs | Additional hitter/pitcher validation metrics, optional park/context metrics, advanced leaderboards | Required future integration |
| RotoWire MLB Lineups | Cross-check confirmed lineups, batting order, game status, betting totals where visible | Required future integration |
| Ballpark Pal | Ballpark/weather HR environment, park/weather boosts, game-level HR conditions | Required future integration |
| VSiN | Betting market context, park-factor commentary, odds/prop context where available | Required future integration |
| OddsShopper | HR odds comparison and best available sportsbook lines | Required future integration |
| Action Network | Player prop odds, market comparison, public/consensus context | Required future integration |

## Current Automated Pipeline

Currently automated:

- Baseball Savant custom leaderboard CSVs
- MLB public game feed
- MLB public schedule
- MLB public boxscores
- MLB public player handedness endpoint

Not yet automated:

- FanGraphs
- RotoWire
- Ballpark Pal
- VSiN
- OddsShopper
- Action Network

Integration details and ordering are tracked in:

```text
INTEGRATION_PLAN.md
```

## First Availability Check

Initial public-access check:

- RotoWire daily lineups returned a public HTML page.
- Ballpark Pal returned public methodology/environment pages.
- VSiN returned public MLB/park-factor pages.
- Action Network MLB props returned a public HTML page.
- OddsShopper has public player-specific HR odds pages, but the generic MLB URL needs a more specific endpoint.
- FanGraphs blocked a basic scripted request, so FanGraphs should start as CSV import or another supported access method.

## Rules For Future Upgrades

1. Prefer official/public CSV or API endpoints where available.
2. Do not scrape behind logins, paywalls, or access controls.
3. Store source fields separately when possible, rather than overwriting one source with another.
4. Add a `source_notes` or `sources_used` field to outputs when multiple sources are active.
5. If sources disagree, preserve the disagreement for review instead of silently choosing one.
6. Odds and market data should be used for value labels, not to inflate the raw HR probability score.

## Source Links

- Baseball Savant Custom Leaderboards: https://baseballsavant.mlb.com/leaderboard/custom
- MLB Starting Lineups: https://www.mlb.com/starting-lineups
- RotoWire MLB Daily Lineups: https://www.rotowire.com/baseball/daily-lineups.php
- FanGraphs: https://www.fangraphs.com/
- Ballpark Pal: https://www.ballparkpal.com/
- VSiN MLB: https://vsin.com/mlb
- OddsShopper MLB: https://www.oddsshopper.com/mlb
- Action Network MLB Props: https://www.actionnetwork.com/mlb/props
