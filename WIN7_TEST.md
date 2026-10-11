# Windows 7 SP1 x64 legacy test

This branch produces a test-only Windows 7 SP1 x64 Portable executable.

## Design

- Python 3.8.10
- PyInstaller 5.13.2
- no pywebview / WebView2 dependency
- UI opened in the default browser through the existing local Flask/Waitress server
- automatic in-app installation is disabled for the legacy channel
- normal Windows 10/11 artifacts are not changed

## Minimum target

Windows 7 SP1 x64. Windows Vista and Windows XP are not supported by this test build.

## Test checklist

1. Start the executable.
2. Confirm no `api-ms-win-core-path-l1-1-0.dll` error appears.
3. Confirm the default browser opens the local PT2VHF APRS Client page.
4. Configure/copy an existing database and verify APRS-IS.
5. Verify Map, Messages, Stations, Statistics and Configurations.
6. Verify serial/TNC detection if hardware is available.
7. Close the application from the tray and confirm the local server exits.

A modern browser compatible with the machine is required; Internet Explorer 11 is not a supported UI target.
