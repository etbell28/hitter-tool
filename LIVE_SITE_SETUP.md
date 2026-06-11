# Live Hitter Tool Setup

This version changes the dashboard from a static-only page to a live page.

## What It Does

- The dashboard loads normally at `https://hittertoolv1.vercel.app/`.
- The page asks `/api/slate` for current slate data every 60 seconds.
- GitHub Actions runs the Python model during MLB lineup windows, then posts the finished JSON to `/api/update-slate`.
- `/api/refresh` rebuilds the slate, scores hitters, and writes the newest JSON payload to Vercel Blob.

## One-Time Setup Required

The live API needs persistent storage. Use Vercel Blob.

1. Open Vercel.
2. Open the `hittertoolv1` project.
3. Go to `Storage`.
4. Create a new `Blob` store.
5. Connect it to the `hittertoolv1` project.
6. Confirm Vercel added `BLOB_READ_WRITE_TOKEN` to the project environment variables.
7. Redeploy the project.

Without `BLOB_READ_WRITE_TOKEN`, the dashboard still opens, but it can only serve bundled fallback data.

## How To Test

After redeploy:

1. Open GitHub Actions.
2. Run `Live Hitter Tool Refresh` manually with `remaining`.
3. Wait for the workflow to complete successfully.
4. Open `https://hittertoolv1.vercel.app/api/slate`.
5. Confirm the JSON timestamp is current.
6. Open `https://hittertoolv1.vercel.app/`.

## Why GitHub Actions Handles Scheduling

Vercel Hobby only allows daily cron jobs. Frequent refreshes are handled by `.github/workflows/live-refresh.yml` instead. GitHub Actions computes the data and sends the finished JSON to Vercel.

## Important Limitation

This is near-live, not websocket livestreaming. GitHub Actions triggers HTTP refresh requests on a schedule. The dashboard itself polls every 60 seconds. That is the correct practical setup for lineup-confirmation updates without manual uploads on the free Vercel Hobby plan.
