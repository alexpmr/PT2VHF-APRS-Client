from __future__ import annotations

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.tnc_service import service as tnc_service
from pt2vhf_aprs.local_server import runtime_file_for, start_local_server
from pt2vhf_aprs.web import create_app

app = create_app()

if __name__ == "__main__":
    service.start_if_configured()
    tnc_service.start_if_configured()
    handle = start_local_server(app, runtime_file=runtime_file_for(db.DB_PATH.parent))
    print(f"PT2VHF APRS Client — Interface local: {handle.host}:{handle.port}")
    try:
        handle.thread.join()
    except KeyboardInterrupt:
        handle.close()
