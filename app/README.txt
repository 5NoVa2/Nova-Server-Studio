NOVA / MINECRAFT SERVER STUDIO 1.0.0-beta.4 - Windows x64
Created by Nova

INSTALL / UPGRADE
Exit Nova from the tray, then run NovaSetup.exe and install over the existing
location. Setup adds desktop and Start menu shortcuts and an uninstall entry.
Existing server folders, preferences, profiles and encrypted API keys are reused.
Uses your existing 64-bit Python 3.10+ with pip, Tcl/Tk and the Python launcher.
First launch downloads Qt if needed. Software rendering and normal window
startup are enabled by default. No console window is needed.
For the portable folder, extract all files and run Launch.vbs. The launcher
also refreshes your desktop shortcut. Keep the folder in a permanent location.

WHAT'S NEW IN v14.1
Settings > Main servers folder chooses a parent location once. + Add creates
a readable child folder automatically using the profile name, e.g.
MinecraftServers\Survival. Duplicate names receive a number. Install / switch
downloads and installs the selected server into that folder. No manual folder
creation is needed. The chosen parent is remembered across launches.
Existing servers keep their current locations; changing the parent only affects
new profiles. Renaming a profile changes its label, not its existing folder.

PREVIOUS v14 CHANGES
- Server settings track typing immediately, so live status updates no longer
  reset fields. Unsaved edits survive automatic refreshes and profile switching.
- Files/configuration load at startup, after installing/importing a server,
  after changing folders/profiles, and periodically for external changes.
  server.properties opens automatically. Manual reload remains available.
- Auto / Java / Bedrock tunnel selector, with protocol mismatch checks.
- Multiple servers run simultaneously with independent folders, ports, logs,
  player lists, settings and VPS connections. Stop all and Exit cover every host.
- Player management page: live player list, kick, op/deop, allowlist and Java
  ban/pardon. Standard console output is parsed; list is polled every 15 seconds.
- Smoother slide/fade transitions, responsive home tiles and stable menus.
  Reduce motion in Settings disables decorative movement and transitions.

MULTIPLE HOSTS
The top bar selects a saved server profile. Type a name and click + Add for a
new one. New profiles receive a separate folder and distinct game ports.
Choose its server software and version on Server, accept the EULA, and install.
Start hosting on each profile. Switching profiles keeps the others running.
Profiles share the CurseForge key, but SSH passwords/passphrases remain separate
and are kept in memory. A new profile copies the selected profile's non-secret
VPS connection details; change them in Settings when using a different VPS.
Rename changes the profile label. Remove forgets a stopped profile; its server
folder and backups remain. Stop all stops all servers/tunnels without exiting.

Java servers use TCP; Bedrock uses UDP. Auto follows the installed edition.
Selecting Java/Bedrock explicitly does not convert a server to the other edition.
Start hosting waits for the local server to report readiness before tunneling.
Each concurrent local Java server needs its own TCP port. Each Bedrock server
needs unique local IPv4 and IPv6 UDP ports. Profiles on the same VPS need unique
public ports for their protocol. Running conflicts are rejected before launch.
Change local/public ports on Settings while that profile is stopped.

After adding profiles or changing public ports, click Configure VPS. Nova's
Ubuntu 24.04 setup includes all saved profiles' Java and Bedrock public ports
for that VPS/SSH user. It preserves separate managed SSH-user blocks, enables
remote forwarding and opens game ports if UFW is active. Root or passwordless
sudo is required. Allow those same ports in your VPS provider's firewall too.
Java join addresses include :port when using a non-default public port.
For Bedrock, enter the displayed host and public UDP port separately in the game.
Bedrock forwards UDP through SSH/TCP; packet loss can increase latency.

SERVER SETTINGS / FILES
Open Files > Server settings to edit the loaded server.properties values.
Stop that profile's server before saving or changing mods/plugins. Other hosts
can remain running. Unsaved settings stay marked and protected from refresh.
External edits produce a save conflict instead of overwriting newer content.
Connection/authentication settings remain locked to this profile's tunnel ports.
The configuration editor supports text/JSON/TOML validation and safe paths.
Add/enable/disable/remove mod or plugin JARs in the corresponding tab.
Import ZIP can scan Downloads or fetch a direct HTTPS server ZIP link.
Arbitrary imported packs may require their supplied launcher; built-in installers
create Nova-compatible launch metadata automatically.

PLAYER OPTIONS
Select the desired profile before using Players. Click an online player or type
a name. Moderation/operator actions ask for confirmation. Java supports kick,
ban/pardon, op/deop and whitelist add/remove/on/off. Bedrock supports kick,
op/deop and allowlist add/remove/on/off; native ban/pardon is not available.
Bedrock/modded commands may require their own permission or cheats settings.
The list depends on standard English console messages. Custom/localized server
output may require checking the Live console. Command responses appear there.

INSTALLERS / CURSEFORGE
Vanilla, Paper, Spigot, Forge, CurseForge server packs and native Bedrock Windows
servers are supported. Refresh versions loads the chosen engine's releases;
Bedrock supports the current official stable Windows release. Java RAM is per
profile; Bedrock does not use Java RAM settings.
CurseForge browsing requires an approved API key. Enter it once in Modpacks;
Nova saves it encrypted with Windows DPAPI for your Windows account. Forget key
removes the remembered key. Passwords and private-key passphrases are not saved.
Browse popular/recent/most-downloaded packs with an optional MC version filter.
Relevant ranks names within the current page. Inspect release mods and artwork,
then choose a release with Server: Yes before installation. Client manifests
can differ from server packs. API/author download restrictions are respected.

DOMAINS / DEFAULTS
No VPS or public domain is preconfigured. Enter your own VPS details in Settings.
A VPS is optional for local hosting. Nova's VPS setup targets Ubuntu 24.04.
Defaults: Java TCP 25565, Bedrock UDP 19132; extra profiles use distinct ports.
At IONOS, point the domain's A record at the VPS IPv4 address. TTL 1 hour is fine.
With Cloudflare use DNS only. Changing Nova's address field does not update DNS.
No router port forwarding is required for the VPS tunnel setup.

BACKUPS / TRAY / UNINSTALL
Backups are manual only. Click Manual backup while the selected host is stopped.
Installing/switching replaces all files in that profile's selected folder after
confirmation, including old worlds/mods/configuration. Failed installs retain
transaction rollback protection; no persistent automatic backups are made.
X minimizes to the system tray and keeps all hosts running. Right-click its
icon for Open Nova / Exit Nova. Without a tray, Nova minimizes to the taskbar.
Exit saves and stops ALL profiles, waits up to 45 seconds, then ends remaining
Nova-owned process trees. Unrelated Java/Python processes are left alone.
Uninstall through Windows Installed apps. Known app files/shortcuts are removed;
server folders, backups and preferences are preserved, including profile data.

VALIDATION / TROUBLESHOOTING
QML pages are rendered with Qt's software backend. Regression checks cover
real text entry across refreshes, save conflicts, automatic post-install refresh,
profile persistence/isolation, two concurrent test server processes, independent
commands/stops, global exit cleanup, Java/Bedrock tunnel selection and custom
ports. Actual sshd validation covers multi-port/per-user configuration, legacy
migration and idempotent edits. Installer payloads are compared byte for byte.
Windows installation/tray behavior, native Minecraft player output and live VPS
play still need testing on your PC. Logs: %LOCALAPPDATA%\MCServerSwitcher\app.log.
Qt/PySide6 licenses: https://doc.qt.io/qtforpython-6/licenses.html
