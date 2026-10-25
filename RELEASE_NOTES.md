# Nova Server Studio 1.0.0-beta.3

- Settings > VPS port ranges accepts inclusive ranges and comma-separated ports.
- Separate Java TCP and Bedrock UDP fields, with validation and saved preferences.
- Configure VPS includes ranges and all assigned ports for the same VPS/SSH user.
- New profiles inherit ranges and receive an unused public port; an exhausted range reports an error without creating a profile or folder.
- UFW rules use compact ranges; SSH permissions enumerate the allowed Java ports.
- Existing profiles retain their local/public ports. Extra ranges do not change server listeners. Additional ranges are limited to 256 ports per protocol per profile.
- Range changes apply after Configure VPS; provider firewalls must also allow these ports. Old UFW allowances are not automatically removed.

Validation: 23 regression/UI tests passed, including generated Bash syntax and real sshd validation at the maximum range size. Native Windows and live VPS testing remain to be done.

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
