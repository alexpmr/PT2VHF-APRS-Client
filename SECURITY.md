# Security policy

## Supported releases

Security fixes are normally applied to the latest published release and to the current `main` branch.

## Reporting a vulnerability

Do **not** publish APRS-IS passcodes, exported configuration files, private location data, exploit details, or other secrets in a public GitHub issue.

Preferred reporting path:

1. Use GitHub's private **Report a vulnerability / Security Advisory** feature for this repository when available.
2. If private reporting is not available, open a minimal public issue requesting a private contact channel **without including exploit details or secrets**.

Please include, privately where appropriate:

- affected version;
- Windows version;
- reproduction steps;
- expected and observed behavior;
- impact;
- relevant logs with credentials and precise private location data removed.

## Release integrity

Official Windows installers and portable packages are published on this repository's GitHub Releases page.

Until code signing is activated, release executables may be reported by Windows as having an unknown publisher. See [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md).

## Secret handling

Never commit or publish:

- APRS-IS passcodes;
- SignPath/API tokens;
- signing credentials;
- exported application configuration containing credentials.

The repository's `.gitignore` excludes common local databases and build outputs, but contributors remain responsible for reviewing commits before publishing them.
