# Third-party notices

PT2VHF APRS Client contains or depends on third-party Open Source Software.

The MIT License in [LICENSE](LICENSE) applies to source code authored for this project. It does **not** relicense third-party components.

## Important distribution note

The Windows build currently bundles `aprslib`, which is published under **GNU GPL v2**.

Because that dependency is included in the distributed application, Windows releases must be distributed in a way that complies with the applicable GPLv2 obligations. The project must not describe the complete bundled Windows executable as "MIT-only".

The project's own MIT-licensed source remains MIT-licensed; GPL-covered third-party code retains its GPL terms.

## Principal dependencies

| Component | Purpose | License |
| --- | --- | --- |
| aprslib | APRS packet parsing | GNU GPL v2 |
| Flask | Local web application framework | BSD-3-Clause |
| Waitress | Local WSGI server | ZPL-2.1 |
| pystray | Windows system-tray integration | LGPL-3.0-or-later |
| Pillow | Tray/icon image handling | HPND |
| PyInstaller | Windows packaging tool | GPLv2 with bootloader/bundling exception |
| Leaflet | Interactive map client | BSD-2-Clause |
| OpenStreetMap | Map data / tile service | See OpenStreetMap attribution and service terms |

This list focuses on principal direct dependencies. Transitive Python dependencies retain their own licenses.

## Source availability

The project source and build scripts are published at:

https://github.com/alexpmr/PT2VHF-APRS-Client

Third-party source code and license texts are available from the respective upstream projects.

Before each public binary release, dependency changes should be reviewed so this notice remains accurate.
