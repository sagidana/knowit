from pathlib import Path

KNOWIT_HOME = Path.home() / ".knowit"
BIN_DIR = KNOWIT_HOME / "bin"

FZF_BIN = str(BIN_DIR / "fzf")
BAT_BIN = str(BIN_DIR / "bat")
