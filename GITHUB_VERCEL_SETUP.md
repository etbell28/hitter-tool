# GitHub + Vercel Setup

This makes the phone link update automatically while you are away from your computer.

## What This Setup Does

1. GitHub stores the Hitter Tool project.
2. GitHub Actions runs the tool on a schedule.
3. The workflow updates `dashboard_site/index.html`.
4. Vercel detects the GitHub change and redeploys the same public link.

## Step 1: Create A GitHub Account

Go to:

```text
https://github.com
```

Create a free account if you do not already have one.

## Step 2: Create A New GitHub Repository

1. Click the `+` button in the top right.
2. Choose `New repository`.
3. Repository name:

```text
hitter-tool
```

4. Choose `Private` if you do not want anyone else to see it.
5. Do not add a README, .gitignore, or license from GitHub.
6. Click `Create repository`.

## Step 3: Upload This Project

If you want the easiest non-technical path:

1. On the new GitHub repo page, click `uploading an existing file`.
2. Drag this entire project folder's contents into GitHub.
3. Commit/upload the files.

Important files/folders to include:

- `.github/workflows/update-dashboard.yml`
- `dashboard_site/`
- `build_automated_slate.py`
- `hitter_tool.py`
- `build_dashboard.py`
- `publish_dashboard.py`
- `run_late_slate.py`
- `run_full_slate.py`
- `requirements.txt`

## Step 4: Connect Vercel To GitHub

1. Go to:

```text
https://vercel.com
```

2. Click `Add New...`
3. Choose `Project`.
4. Import your `hitter-tool` GitHub repo.
5. Set the project/root directory to:

```text
dashboard_site
```

6. Framework preset:

```text
Other
```

7. Build command:

```text
None
```

8. Output directory:

```text
.
```

9. Deploy.

## Step 5: Confirm The Link

After deploy, Vercel gives you a public URL. Open it on your phone.

## Step 6: Confirm Automatic Updates

In GitHub:

1. Open the repo.
2. Click `Actions`.
3. Click `Update Hitter Tool Dashboard`.
4. Click `Run workflow`.
5. Choose `late` or `full`.
6. Click `Run workflow`.

When the workflow finishes, Vercel should redeploy automatically.

## Schedule

The workflow currently runs several times through the MLB evening slate window:

- 4:00 PM Eastern
- 5:30 PM Eastern
- 7:00 PM Eastern
- 8:30 PM Eastern
- 10:00 PM Eastern

GitHub schedules can run a little late. That is normal.

