import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent
PYTHON = sys.executable
REMAINING_SLATE = ROOT / "outputs" / "auto_slate_remaining.csv"


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    run([PYTHON, "build_automated_slate.py", "--mode", "upcoming", "--output", str(REMAINING_SLATE)])
    run([PYTHON, "hitter_tool.py", str(REMAINING_SLATE)])
    run([PYTHON, "build_dashboard.py"])
    run([PYTHON, "publish_dashboard.py"])
    print("Remaining-game slate and HR rankings are ready.")
    print("Only games that have not started are included.")
    print(f"Slate: {REMAINING_SLATE}")
    print(f"Rankings CSV: {ROOT / 'outputs' / 'hr_rankings.csv'}")
    print(f"Rankings Excel: {ROOT / 'outputs' / 'hr_rankings.xlsx'}")
    print(f"Dashboard: {ROOT / 'outputs' / 'hitter_tool_dashboard.html'}")
    print(f"Deployable site: {ROOT / 'dashboard_site' / 'index.html'}")
    print(f"Report: {ROOT / 'outputs' / 'hr_rankings.md'}")


if __name__ == "__main__":
    main()
