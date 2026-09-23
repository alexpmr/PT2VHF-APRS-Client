# SignPath Foundation onboarding plan

This document describes the repository preparation and the remaining external setup required before PT2VHF APRS Client releases can be code signed.

## Repository preparation already completed

- MIT license for project-authored source code.
- Code signing policy.
- Privacy policy.
- Security policy.
- Third-party license notices.
- GitHub-hosted Windows build workflow.
- Automated tests before packaging.
- PyInstaller build.
- Inno Setup installer build.
- GitHub Actions artifact upload.
- GitHub Release publication.

## External onboarding steps

1. Apply for an Open Source Code Signing subscription through SignPath Foundation.
2. Ensure the project and all distributed components satisfy the SignPath Foundation Open Source conditions.
3. Enable multi-factor authentication for maintainers on GitHub and SignPath.
4. Install/authorize the SignPath GitHub App for this repository.
5. Create a SignPath project pointing to:
   `https://github.com/alexpmr/PT2VHF-APRS-Client`
6. Link the predefined GitHub.com Trusted Build System.
7. Define an artifact configuration for the Windows artifact(s).
8. Enforce product metadata:
   - Product name: `PT2VHF APRS Client`
   - Product version: same value as `VERSION`
9. Create a release-signing policy with origin verification restricted to the intended release source.
10. Configure manual approval as required by the SignPath Foundation policy.
11. Create a SignPath API token with only the required submission permissions.
12. Store the API token as a protected GitHub secret, for example:
    `SIGNPATH_API_TOKEN`
13. Store non-secret identifiers as repository/environment variables where appropriate:
    - `SIGNPATH_ORGANIZATION_ID`
    - `SIGNPATH_PROJECT_SLUG`
    - `SIGNPATH_SIGNING_POLICY_SLUG`
    - `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG`

## Planned GitHub Actions integration

The signing step should be inserted only after the unsigned build has been uploaded as a GitHub Actions artifact.

The current SignPath GitHub integration uses the `signpath/github-action-submit-signing-request` action and the GitHub artifact ID produced by `actions/upload-artifact`.

Conceptually:

```yaml
- name: Upload unsigned artifact
  id: upload-unsigned-artifact
  uses: actions/upload-artifact@v4
  with:
    name: PT2VHF-APRS-Client-Windows-x64-unsigned
    path: path-to-artifact

- name: Submit SignPath signing request
  uses: signpath/github-action-submit-signing-request@v3
  with:
    api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
    organization-id: ${{ vars.SIGNPATH_ORGANIZATION_ID }}
    project-slug: ${{ vars.SIGNPATH_PROJECT_SLUG }}
    signing-policy-slug: ${{ vars.SIGNPATH_SIGNING_POLICY_SLUG }}
    artifact-configuration-slug: ${{ vars.SIGNPATH_ARTIFACT_CONFIGURATION_SLUG }}
    github-artifact-id: ${{ steps.upload-unsigned-artifact.outputs.artifact-id }}
    wait-for-completion: true
    output-artifact-directory: signed
```

The release step must then publish the **signed output**, not the unsigned artifact.

## Do not enable signing prematurely

Do not add a live signing step until:

- the SignPath Foundation project has been approved;
- project identifiers are known;
- the artifact configuration is validated;
- GitHub App/trusted-build integration is active;
- the API token is stored as a secret;
- third-party licensing obligations for the bundled Windows binary have been reviewed.

This avoids creating a workflow that appears signed but silently publishes unsigned artifacts.
