# Nova Server Studio 1.0.0-beta.1

First free, MIT-licensed public beta. Created by Nova.

Includes multi-server profiles, automatic named server folders, Java/Bedrock
SSH tunnels, custom ports, server settings/config/mod management, console and
player controls, CurseForge browsing, manual backups and tray hosting.

## Before installing

- Windows 10/11 x64 and Python 3.10+ with pip/Tcl-Tk/Python launcher are required.
- First run downloads Qt. Public hosting needs your own VPS; local hosting does not.
- The installer is unsigned and this is a beta.
- Backups are manual. Installing/switching replaces the selected server folder.
- No VPS/domain/account secrets or shared API keys are bundled.

## Validation

Public-build tests verify blank connection defaults, local-only profile saving,
automatic named subfolder creation, persisted storage location, privacy of the
source package and QML initialization under software rendering. Internal
regression checks also exercised installer flows, configuration conflict guards,
concurrent test server processes, protocol-specific port routing and sshd
configuration generation. Native Windows/live multiplayer needs wider testing.

Release assets: `NovaSetup.exe`, `NovaServerStudio-source.zip`, `SHA256SUMS.txt`.
