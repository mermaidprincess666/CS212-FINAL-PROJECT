"""Run main.py as a child process while developing.

Ctrl+C stops the runner, which terminates the game instead of raising a
KeyboardInterrupt inside its own loop. It does not watch files or restart.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_DIR / "main.py"

print("Starting game...")
# cwd keeps the child's asset paths relative to the project, not the shell.
process = subprocess.Popen(
    [sys.executable, str(MAIN_FILE)],
    cwd=str(PROJECT_DIR)
)

print("Game is running.")
print("You can edit your code without automatic restarts.")
print("Press Ctrl+C here to stop the game.")

try:
    process.wait()
except KeyboardInterrupt:
    print("\nStopping game...")
    process.terminate()
    process.wait()