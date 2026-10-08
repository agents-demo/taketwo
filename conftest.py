import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from taketwo.bootstrap import setup  # noqa: E402

# Configure logging to runtime/logs before any test imports openjiuwen.
setup()
