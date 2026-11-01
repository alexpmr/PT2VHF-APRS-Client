"""Run the real application UI against an isolated database and loopback server."""
import os
import logging
from pathlib import Path
import subprocess
import sys
import tempfile
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="pt2vhf-i18n-", ignore_cleanup_errors=True) as data:
        os.environ["PT2VHF_DATA_DIR"] = data
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        from pt2vhf_aprs.local_server import start_local_server
        from pt2vhf_aprs.web import create_app
        handle = start_local_server(create_app(), host="127.0.0.1", start_port=18763, attempts=30)
        try:
            assert handle.wait_ready(10), "Isolated HTTP server did not start"
            env = dict(os.environ, I18N_APP_URL=f"http://127.0.0.1:{handle.port}")
            script = 'i18n_visible.browser.cjs' if args.audit else 'i18n_app.browser.cjs'
            subprocess.run(["node", str(ROOT / "tests" / script)], env=env, cwd=ROOT, check=True, timeout=600 if args.audit else 180)
        finally:
            handle.close()


if __name__ == "__main__":
    main()
