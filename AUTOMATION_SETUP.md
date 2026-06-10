# Hitter Tool Automation Setup

This project is designed to run without daily chat commands once the files are uploaded to GitHub.

## What Runs Automatically

- Overnight audit: reviews the prior slate against actual MLB home runs.
- Morning full slate: builds the first full-board projection.
- Afternoon full slate refreshes: updates probable pitchers, lineups, weather, and model output.
- Lineup-window refreshes: runs every 30 minutes during the main MLB lineup window.
- Late/remaining slate: after games begin, only games that have not started remain on the action board.

## How The Website Updates

GitHub Actions runs the tool and commits the refreshed dashboard file:

`dashboard_site/index.html`

Because Vercel is connected to the GitHub repo, that commit should trigger a Vercel deploy. Your public website then updates without you doing anything.

## Manual Override

In GitHub:

1. Open the repo.
2. Click `Actions`.
3. Click `Automate Hitter Tool`.
4. Click `Run workflow`.
5. Choose `full`, `remaining`, or `audit`.

Use `full` before games start. Use `remaining` after games have started.

## Important Notes

- GitHub scheduled jobs can run a few minutes late. That is normal.
- The dashboard is only as current as the last completed scheduled run.
- True always-live updates would require a small backend/database service. The current setup is the free/low-maintenance version: scheduled refresh plus automatic Vercel deploy.
