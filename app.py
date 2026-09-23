from __future__ import annotations

import os

from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.web import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("PT2VHF_HOST", "127.0.0.1")
    port = int(os.getenv("PT2VHF_PORT", "8080"))
    service.start_if_configured()
    print(f"PT2VHF APRS Client: http://{host}:{port}")
    app.run(host=host, port=port, threaded=True, use_reloader=False)
