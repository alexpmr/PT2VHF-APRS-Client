# Code signing policy

## Scope

This policy applies to official Windows releases of **PT2VHF APRS Client** published from the repository:

https://github.com/alexpmr/PT2VHF-APRS-Client

Project-authored source code is licensed under the MIT License. Third-party components retain their respective licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Current signing status

Official Windows releases are currently **unsigned** while the project completes the onboarding process for an Open Source Code Signing service.

The intended signing provider is SignPath.io through SignPath Foundation. Once the project is approved and signing is active, the repository and release pages will state:

> Free code signing provided by SignPath.io, certificate by SignPath Foundation.

Until that onboarding is complete, users should expect Windows to report the publisher as unknown.

## Build provenance

Official release binaries must:

1. Be built from this repository.
2. Be produced by GitHub Actions using GitHub-hosted Windows runners.
3. Pass the repository's automated test suite before packaging.
4. Be built using the version recorded in `VERSION`.
5. Be uploaded as GitHub Actions artifacts before any signing request.
6. Be published to the GitHub Releases page only from the release workflow.

No developer workstation is authorized to produce a code-signed official release.

## Team roles

This is currently a single-maintainer project.

- **Committer / reviewer:** Alex Rodrigues — GitHub [@alexpmr](https://github.com/alexpmr)
- **Signing approver:** Alex Rodrigues — GitHub [@alexpmr](https://github.com/alexpmr)

If additional maintainers are added, this section must be updated before they participate in the signing process.

## Release approval

A release signing request must correspond to a reviewed release commit/tag and must be manually approved through the configured signing service when required by the signing policy.

Signing must never be used for:

- locally modified binaries;
- artifacts built outside the trusted GitHub workflow;
- third-party executables that are not produced from this project's source;
- test binaries presented as production releases.

## Credential handling

- Code-signing private keys must never be stored in this repository.
- SignPath/API credentials must be stored only as protected GitHub repository or environment secrets.
- APRS-IS passcodes must never appear in workflow logs, issues, screenshots, releases, or signing metadata.
- The application masks APRS-IS passcodes before persisting/displaying APRS-IS traffic logs.

## Artifact identity

Signed binaries must use consistent metadata:

- Product name: **PT2VHF APRS Client**
- Executable: **PT2VHF_APRS_Client.exe**
- Installer: **PT2VHF_APRS_Client_Setup_x64.exe**
- Product version: identical to the value in `VERSION`

## Security requirements

Maintainers participating in source control and signing should use multi-factor authentication on GitHub and on the signing service.

See also [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).
