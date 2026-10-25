# Nova Server Studio 1.0.0-beta.2

Created by Nova. Free software under the MIT license.

- Batch installer logs and avoid redundant UI refreshes during CurseForge installation.
- Copy imported mod/plugin JARs on a background worker.
- Show only core server configuration files, including Paper global/default settings.
- Fix programmatic editor refreshes marking files as modified.
- Save installation preferences and generated files automatically; save pending edits before starting or adding a JAR.
- Add Save All / Ctrl+S for the active server editor, server settings and preferences, with conflict checks.
- Load version choices when opening the selector, include Vanilla snapshots/historical versions and the full numeric Forge Minecraft version catalog. Bedrock remains the latest official release; CurseForge versions follow the selected pack.
- Add Files > Backups with manual backups and confirmed staged restores. No automatic/scheduled backups.

Sleep-on-join is not included in this build. It requires an always-on connection listener and server startup coordination.

Windows x64 beta. Requires existing Python 3.10+ with pip, Tk and the Python launcher. First run downloads PySide6. Java/game files and third-party components download separately. Unsigned installer. Use your own CurseForge key and optional VPS.

Validation: 18 automated regression/UI tests passed on Linux with the Qt software renderer. Native Windows and live CurseForge/VPS performance testing remain to be done.
