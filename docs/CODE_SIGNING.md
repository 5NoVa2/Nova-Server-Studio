# Code signing policy

## Status

Saturn Server Launcher is preparing an application to the SignPath Foundation
open-source program. Acceptance and signing access have **not** been granted.
Existing releases, including 1.0.3, are unsigned.

If accepted, the required attribution for signed releases will be:

> Free code signing provided by [SignPath.io](https://signpath.io), certificate by
> [SignPath Foundation](https://signpath.org).

This attribution is prospective and does not describe existing releases.

## Team roles

- Author/committer: [5NoVa2](https://github.com/5NoVa2).
- Reviewer: [5NoVa2](https://github.com/5NoVa2). Proposed changes from contributors,
  including generated changes, must be reviewed before merging for a signed build.
- Release signing approver: [5NoVa2](https://github.com/5NoVa2).

All participants must enable MFA on GitHub and SignPath before signing is enabled.
Each production signing request requires explicit manual approval in SignPath.
Signing does not replace source review or establish that software has no bugs.

## Build and release controls

The proposed Windows workflow builds SaturnSetup.exe from repository source on a
GitHub-hosted runner and uploads the unsigned build as an Actions artifact.
After onboarding, SignPath checks build provenance and signs only the Saturn
installer. Third-party binaries must not be signed under Saturn's project.
Product name and version must be enforced in SignPath's artifact configuration.
Checksums are generated **after** signing. Signed output is retained as an Actions
artifact for inspection; this workflow does not publish or replace public releases.

Signing remains gated behind SIGNPATH_ENABLED and the signpath-production GitHub
environment. Configure that environment to allow only the protected main branch,
require the maintainer's approval, and store a submitter-only SignPath API token
there. Configure SignPath's origin restrictions for this repository and workflow.
Never expose signing secrets to pull request jobs or untrusted checkout refs.

## Privacy policy

See [Privacy policy](PRIVACY.md), including optional third-party services.

## Reporting

Report security concerns through the repository's GitHub reporting facilities.
Do not include passwords, private keys, API tokens, or playit secrets in public issues.
