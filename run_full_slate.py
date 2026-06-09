import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent
PYTHON = sys.executable
FULL_SLATE = ROOT / "outputs" / "auto_slate_full.csv"


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    run([PYTHON, "build_automated_slate.py", "--mode", "all", "--output", str(FULL_SLATE)])
    run([PYTHON, "hitter_tool.py", str(FULL_SLATE)])
    run([PYTHON, "build_dashboard.py"])
    run([PYTHON, "publish_dashboard.py"])
    print("Full-day slate and HR rankings are ready.")
    print(f"Slate: {FULL_SLATE}")
    print(f"Rankings CSV: {ROOT / 'outputs' / 'hr_rankings.csv'}")
    print(f"Rankings Excel: {ROOT / 'outputs' / 'hr_rankings.xlsx'}")
    print(f"Dashboard: {ROOT / 'outputs' / 'hitter_tool_dashboard.html'}")
    print(f"Deployable site: {ROOT / 'dashboard_site' / 'index.html'}")
    print(f"Report: {ROOT / 'outputs' / 'hr_rankings.md'}")


if __name__ == "__main__":
    main()
