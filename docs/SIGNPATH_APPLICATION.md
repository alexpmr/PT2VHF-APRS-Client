# SignPath Foundation — application data

Use this document as the source of truth when submitting the PT2VHF APRS Client to the SignPath Foundation Open Source Code Signing program.

## Project

**Project name:** PT2VHF APRS Client

**Repository:**  
https://github.com/alexpmr/PT2VHF-APRS-Client

**Primary maintainer:**  
Alex Rodrigues — GitHub @alexpmr

**Project type:**  
Open-source Windows desktop application for APRS/APRS-IS amateur-radio operation.

**Primary platform:**  
Windows x64

## Description

PT2VHF APRS Client is an open-source APRS-IS desktop client focused on Windows.

It provides:

- APRS-IS connection and authentication;
- live APRS station map;
- APRS symbol rendering;
- moving-station tracklogs;
- APRS messaging with ACK/REJ handling;
- station history stored in a local SQLite database;
- raw APRS-IS RX/TX monitor;
- periodic APRS beacon transmission;
- configurable APRS-IS filters;
- browser geolocation for centering the map;
- Windows system-tray integration.

The application does not contain advertising, analytics, telemetry, vulnerability-scanning, exploit or security-bypass functionality.

## License

Project-authored source code:

**MIT License**

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/LICENSE

The distributed build also uses third-party Open Source components under their own OSI-approved licenses.

Third-party notices:

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/THIRD_PARTY_NOTICES.md

The current build includes `aprslib` under GNU GPL v2; this is explicitly disclosed.

## Existing release

Current Windows release:

https://github.com/alexpmr/PT2VHF-APRS-Client/releases/tag/v0.2.1

Release artifacts are produced by GitHub Actions on GitHub-hosted Windows runners.

## Build system

**Trusted build system requested:** GitHub.com / GitHub Actions

Workflow:

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/.github/workflows/build-windows.yml

Build process:

1. Checkout repository.
2. Configure Python.
3. Install declared build/runtime dependencies.
4. Run automated tests.
5. Package the application with PyInstaller.
6. Generate CycloneDX SBOM and dependency license inventory.
7. Build Windows installer with Inno Setup.
8. Create portable ZIP.
9. Upload workflow artifacts.
10. Submit the build artifact for signing once SignPath integration is active.
11. Publish only the approved/signed release artifacts after signing is enabled.

## Code signing policy

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/CODE_SIGNING_POLICY.md

Required SignPath attribution after approval:

> Free code signing provided by SignPath.io, certificate by SignPath Foundation

## Team roles

This is currently a single-maintainer project.

**Committer / reviewer:**  
Alex Rodrigues — https://github.com/alexpmr

**Signing approver:**  
Alex Rodrigues — https://github.com/alexpmr

Additional maintainers will be documented in the code signing policy before participating in signing.

## Privacy

Privacy policy:

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/PRIVACY.md

The project does not operate a telemetry or analytics backend.

The program connects to networked systems only as part of user-visible application functionality, including:

- the APRS-IS server configured by the user;
- OpenStreetMap tile infrastructure;
- third-party static web resources documented in the privacy policy;
- browser geolocation only after explicit user request and browser permission.

The Windows installer displays a privacy notice before installation.

## Security

Security policy:

https://github.com/alexpmr/PT2VHF-APRS-Client/blob/main/SECURITY.md

APRS-IS credentials are not intended to be published. The raw traffic monitor masks the passcode before persistence/display.

## Installation and uninstallation

The Windows installer is built using Inno Setup.

It:

- installs the program under Program Files;
- stores mutable application data under the user's LocalAppData directory;
- provides normal Windows uninstallation support;
- optionally creates desktop/startup shortcuts only if the user selects those tasks;
- displays the MIT license and privacy notice during installation.

## Signing rationale

Unsigned Windows releases can be blocked or warned about by Windows security controls because the executable currently has no trusted Authenticode publisher identity.

Code signing is requested to:

- provide a verifiable publisher identity;
- establish a cryptographic link between the public source repository and distributed binaries;
- allow users to validate release provenance;
- reduce security warnings that result solely from unsigned publisher status.

## Signing constraints requested

Official signed artifacts must:

- originate from this repository;
- be built by the GitHub Actions workflow on GitHub-hosted Windows runners;
- pass automated tests;
- match the version in `VERSION`;
- use product name `PT2VHF APRS Client`;
- require manual release-signing approval;
- never use the project signing identity for unrelated or upstream third-party binaries.

## Requested artifact names

- `PT2VHF_APRS_Client.exe`
- `PT2VHF_APRS_Client_Setup_x64.exe`

The portable ZIP contains the application tree; signing should apply to signable project-owned Windows binaries inside the artifact according to the SignPath Artifact Configuration.

## Contact / ownership verification

Repository owner and maintainer:

https://github.com/alexpmr

Repository:

https://github.com/alexpmr/PT2VHF-APRS-Client
