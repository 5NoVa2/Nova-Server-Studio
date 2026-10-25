# SignPath onboarding

Status: project preparation only. No application has been submitted, account
created, terms accepted, GitHub App access granted, or signing credential installed
by this change. Acceptance is at SignPath Foundation's discretion; the program
requires verifiable project reputation, which can be a barrier for a new project.

## Before applying

1. Review and merge the code-signing policy, privacy policy, and build workflow.
2. Enable MFA on GitHub. Ensure role assignments in CODE_SIGNING.md are accurate.
3. Add a Code signing policy link to the GitHub release/download page. Existing
   unsigned releases must remain clearly described as unsigned.
4. Run the main-branch Build installer for SignPath workflow to establish a public,
   verifiable Windows build. With SIGNPATH_ENABLED unset it only builds and uploads
   an unsigned installer. Configure the signpath-production environment before
   running, with main-only deployment and reviewer approval restrictions.
5. Review https://signpath.org/terms.html and apply at https://signpath.org/apply.
   Provide real reputation evidence; do not describe test counts as independent
   security audits or claim downloads/users that have not been verified.

## Suggested application project fields

- Project: Saturn Server Launcher
- Repository/homepage: https://github.com/5NoVa2/Saturn-Server-Launcher
- Downloads: https://github.com/5NoVa2/Saturn-Server-Launcher/releases
- Privacy: https://github.com/5NoVa2/Saturn-Server-Launcher/blob/main/docs/PRIVACY.md
  (valid after merging this change)
- Tagline: Free, open-source Minecraft server management for Windows.
- Maintainer: individual, GitHub account 5NoVa2.
- Build system: GitHub Actions, once the workflow is merged and a build succeeds.
- Discovery source: ChatGPT.

The applicant must supply their own account name/email and accept the applicable
terms and personal-data processing consent. No marketing opt-in is necessary.

## After acceptance

1. Follow SignPath's onboarding to link the repository through its GitHub App and
   trusted build system. Limit repository access to Saturn. Review the actual
   requested permissions before granting access.
2. Register the project, signing policy and artifact configuration with SignPath.
   docs/signpath-artifact.xml is a starter for the ZIP created by upload-artifact
   v4; enforce the exact product name/version and only sign SaturnSetup.exe.
   Do not sign upstream executables with this project certificate.
3. Require manual approval for every production signing request and constrain
   allowed origin to this repository, main, and signpath-installer.yml.
4. Configure the protected signpath-production environment with these variables:
   SIGNPATH_ORGANIZATION_ID, SIGNPATH_PROJECT_SLUG, SIGNPATH_SIGNING_POLICY_SLUG,
   SIGNPATH_ARTIFACT_CONFIGURATION_SLUG, SIGNPATH_CERTIFICATE_THUMBPRINT. Verify
   the certificate out of band with SignPath; do not obtain a trust pin solely
   from an untrusted release download.
5. Store the submitter-only SIGNPATH_API_TOKEN as an environment secret directly
   in GitHub. Never put it in chat, commits, screenshots or workflow logs.
6. Set SIGNPATH_ENABLED=true only after restrictions and approvals are configured.
7. Run the workflow, review the signing request, and approve in SignPath. Validate
   the returned installer's Windows signature and install/update behavior on
   Windows before publishing it. Generate checksums from the signed bytes.
8. Add required attribution to signed release notes only after approval/signing.
   Preserve a clear indication of which old releases remain unsigned.

## Updater trust must be finalized

The pending hardening patch pins Authenticode publisher certificate thumbprints.
SignPath Foundation is the publisher for multiple projects. Before re-enabling
automatic installer execution, confirm whether Saturn gets a project-exclusive
certificate. If it is shared, publisher pinning alone cannot distinguish Saturn
from other projects signed with that certificate. Add an independent Saturn-only
release-signature verification scheme before enabling automatic updates in that
case. Do not relax the updater checks merely to make signing work.

Production signing and updater activation are separate tasks. Until trust is
finalized, leave TRUSTED_PUBLISHER_THUMBPRINTS empty and automatic installation
blocked. The build workflow does not publish releases automatically.
