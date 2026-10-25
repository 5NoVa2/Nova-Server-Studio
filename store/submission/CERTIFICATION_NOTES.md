# Draft reviewer notes — update after installed-package validation

Saturn is a desktop game-server administration utility, not Minecraft itself.
It requires runFullTrust to launch user-selected dedicated servers/Java runtimes,
manage files in user-chosen server folders, access native tray integration and
use SSH/network forwarding. It runs at normal user privilege on the PC. Configure
VPS can request root/passwordless sudo on the remote VPS supplied by the user;
there is no local elevation prompt in normal hosting.

The application itself and its Python/Qt/SSH libraries are bundled in MSIX.
The Store edition cannot download/install a GitHub update for Saturn and does not
run pip or a shortcut-installation script on startup.

User-initiated executable downloads remain part of the utility's core function:
Minecraft/Bedrock dedicated server, Java runtime, loaders, server packs and mods.
These are obtained from their upstream services under applicable terms. Please
review this behavior explicitly; Store eligibility is not presumed. No game assets,
server binaries, API keys, passwords or personal VPS details are bundled.

Safe first-run evaluation needs no VPS or CurseForge key: explore the Dashboard,
Settings, Files and task editor without starting hosting. Install a vanilla server
only after accepting the upstream EULA in-app. Local-only hosting is supported.
The PC must stay on for schedules. Closing minimizes to the tray; Exit Saturn stops
owned processes. An absent system tray falls back to taskbar minimization.

Before submission: replace preview identity, attach actual screenshots and WACK
results, document installed-MSIX data paths and uninstall behavior, verify all
server/tunnel processes, provide support/privacy URLs, and complete the actual
age-rating/export questionnaire. Do not submit these unresolved notes as certification results.
