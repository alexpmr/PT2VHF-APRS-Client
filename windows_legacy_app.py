from __future__ import annotations

import os
import sys

# The Windows 7 build intentionally avoids WebView2. The existing local
# Flask/Waitress UI is opened in the user's default browser instead.
os.environ["PT2VHF_WIN7_LEGACY"] = "1"

if "--browser" not in sys.argv:
    sys.argv.append("--browser")

from windows_app import main


if __name__ == "__main__":
    raise SystemExit(main())
