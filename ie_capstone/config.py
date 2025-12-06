"""Configuration constants for the IE Capstone Experiment."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "socratic-debugging-benchmark"
LOGS_DIR = PROJECT_ROOT / "logs" / "sessions"

# Claude API
CLAUDE_MODEL = "claude-opus-4-5-20251101"
MAX_TOKENS = 16384

# Experiment settings
TOTAL_PROBLEMS = 6
JUDGE_ITERATIONS = 3

# Google Form URL (to be updated with actual form)
GOOGLE_FORM_URL = "https://forms.google.com/your-form-id"
