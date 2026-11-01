"""Expose a bounded public build diagnostic as a GitHub check annotation."""
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")[-7000:]
print(text)
print("::error::" + text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A"))
