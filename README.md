# Saturn Server Launcher

Free, open-source Minecraft server management for Windows. **Created by Nova.**
Current public release: **1.0.3**.

Run Minecraft on your own Windows PC. Optionally connect it through your own
VPS so friends can join without router port forwarding, using the VPS address
or your domain. The PC runs Minecraft; the VPS forwards network traffic.
You provide the VPS separately. Your PC and internet must stay on, and the
network must allow the outbound tunnel. This does not guarantee anonymity.

## What's new

- Saturn branding, Dashboard / Server / Files / Tasks / Players / Settings navigation.
- Server modpack section and Prepare a world → Browse modpacks popup.
- Single-click folder/file browser with in-app editing and Save All.
- Saved Start, Stop, Save world, Backup and custom console-command schedules.
- Collapsible Settings sections and per-profile Java selection/preparation.
- Per-server CPU load and resident RAM on Windows, sampled every two seconds.
- Particle startup scene, soft pings and tonal transitions; master mute and volume.
- Public update checks restored, plus an isolated installer build with NSIS CRC validation.

## Install or upgrade

1. Install **64-bit Python 3.10+** with pip, Tcl/Tk and the Python launcher.
2. Download **SaturnSetup.exe** from Releases. Older builds need this manual installer once; future updates use Saturn filenames.
3. Exit Saturn from the tray, then run the installer over the existing location.
4. First launch downloads Qt if needed. Existing profiles, server folders,
   encrypted API keys and preferences are retained.

This release is unsigned. Native Windows audio, live CurseForge downloads,
multiplayer and long-running hosting still need wider testing.

## Create and host a server

Choose Main servers folder in Settings. Add a named profile; Saturn creates a
subfolder automatically. On Server, select the engine and Minecraft version,
accept the EULA, and choose Install / switch. Installation replaces the selected
server folder after confirmation; create a backup before replacing a world.

Supported engines: Vanilla, Paper, Spigot, Forge, CurseForge server packs and
native Bedrock. CurseForge browsing requires your own approved API key. Not all
modpack releases include dedicated server files. Some downloads are subject to
publisher restrictions and upstream terms.

Start local works without a VPS. Connect using localhost and the profile's local
port from the same PC, or its LAN address from another device on the same LAN.
Each simultaneous server needs its own folder and ports. New profiles allocate
unused ports; Settings supports additional VPS port ranges.

For public hosting, enter your own Ubuntu VPS host, SSH account/key and public
join address in Settings. Configure VPS sets up forwarding and active UFW rules;
root or passwordless sudo is required. Provider firewalls must allow the public
game ports. Java uses reverse SSH TCP; Bedrock uses the app's UDP relay carried
through SSH/TCP. The latter can add latency. Point an A record at your VPS and
use DNS-only mode if applicable. A domain is optional.

Passwords/passphrases stay in memory. Private key files stay on your PC.
The optional saved CurseForge key uses Windows account encryption. No shared
API keys, credentials, VPS, domain or game content are included.

## Files, players and backups

Files provides single-click folder navigation, a text editor, server properties,
mods/plugins and backup restoration. Save All / Ctrl+S saves pending edits with
conflict checks. Text files are size-limited; binary files cannot be edited.

Console-based player tracking supports kick, op/deop and allowlist operations;
Java also supports ban/pardon. Some server/modded output formats may differ.

Backups are explicit actions or saved tasks. A scheduled/running-server backup
cleanly stops, copies the server folder, then restarts and reconnects its tunnel.
A stopped server stays stopped. Backup or restart failures pause the queue and
may leave the server stopped. Backups are not automatically pruned.
Restoring a backup requires a stopped server and confirmation.

## Tasks

Schedule Start, Stop, Save world, Backup or a custom Minecraft console command.
Dropdowns select the action, frequency, hour, minute and AM/PM. Frequencies are
once, daily, weekdays, weekly, every two weeks and monthly. The first run is the
next matching local time. Monthly tasks preserve the original day, using the
last day of shorter months. Schedules persist; the immediate task queue is
session-only. Saturn and the PC must be running. Missed runs are skipped.
Errors pause the queue; Stop all cancels queued work and pauses schedules.
Custom commands run in the game console, never an OS shell.

Java Save world sends save-all flush and waits for the standard English save
message. Bedrock Save world uses a clean restart. Check server compatibility.
Sleep-on-join is not implemented.

## Environment, interface and updates

Settings sections toggle open. Environment selects Auto or managed Java
8/11/17/21/25 per profile. Auto uses the runtime selected during installation;
prepare a manual choice before starting. Choose a Java version compatible with
your Minecraft/mod loader. Bedrock does not use Java.

Dashboard and Server show Windows server-process CPU load and resident RAM.
CPU is normalized against total PC capacity. Samples refresh every two seconds;
the first CPU value requires two readings. Unavailable/stopped metrics show a dash.

Settings → Domain & display has a global Enable sounds switch and sound volume,
separate startup sound control, startup scene preference, preview and Reduce motion.
The intro is skippable. Closing minimizes to the tray; Exit Saturn saves and stops
owned hosting processes. F11 toggles fullscreen.

Settings → Saturn updates checks public GitHub releases, including betas.
Downloads use SHA-256 verification. Installation is explicit and requires stopped
servers/tunnels. Private previews have public updating disabled; install this public
build manually to move from a private preview. No silent automatic installation.

## Source and installer build

Python dependencies are listed in requirements.txt. Run app/Launch.vbs on Windows
for windowless launch, or app/Launch.pyw. Source uses Python, PySide6 Qt/QML and
Paramiko. Original startup/UI sounds can be regenerated with the standard-library
scripts under tools/.

Build with NSIS installed:

```sh
python installer/build_verified_installer.py
```

Use --makensis to specify the compiler. The helper rejects concurrent builds,
compiles into an isolated path, verifies NSIS length and CRC, then atomically
promotes dist/SaturnSetup.exe. Build scripts never include profiles, worlds,
credentials, downloaded runtimes or development logs in the installer.

Run checks with:

```sh
python -m unittest discover -s tests -q
```

Free under MIT. See THIRD_PARTY_NOTICES.md for external libraries and game services.

## Help and join address

Help provides searchable, expandable troubleshooting for VPS/SSH, tunnels, DNS, ports and common app issues. Edit the active profile’s join address in Settings → Domain & display, then Save join address. The same preference is shared with VPS connection settings. This updates the address Saturn shows/copies; it does not edit DNS at your provider. DNS guidance is provider-neutral.

## Direct hosting without a VPS

Uncheck **Use VPS tunnel** on Server or Settings → Hosting connection while stopped. Start hosting runs Minecraft without SSH. Java binds to network interfaces in direct mode; tunnel mode keeps Java on loopback. Use the PC LAN address for LAN joins. For internet joins, manually forward router TCP (Java) or UDP (Bedrock) to the profile’s local game port and allow the program/port in Windows Firewall. Set a separate direct public IP/domain and router public port in Domain & display. Existing VPS settings are preserved. No router or firewall rules are changed automatically. See Help → Host without a VPS for troubleshooting, CGNAT and double NAT.

## playit.gg hosting

Select **Use playit.gg tunnel** for a third hosting option. Prepare downloads the official supported portable 0.17.1 Windows x64 agent and verifies its pinned SHA-256 from the upstream release. No service is installed and no third-party binary is bundled. One owned agent is shared across profiles; account approval and game-tunnel creation happen in your browser. Set each local target to the exact 127.0.0.1 port shown by Saturn. Public addresses refresh in the background from the official `/v1/agents/rundata` endpoint using the existing native agent credential. Saturn matches each enabled loopback route to the selected profile’s local port; Java SRV hostnames stay intact. The portable agent’s stdout omits route details, so address discovery does not depend on its console output. Failed lookups clear stale addresses and retry automatically. Credentials and API responses are never copied into logs or settings. Java stays on loopback in playit mode.

Minecraft Java currently has a free tunnel option. Free Bedrock requires RakNet where supported; NetherNet currently requires Premium. Third-party limits and availability apply. See https://playit.gg/ and https://playit.gg/support/minecraft-bedrock-nethernet/. No live user account or game connection is simulated in tests.

Stop shared agent affects all playit profiles; stopping the last leased profile, Stop all, or Exit stops it. A setup-only agent remains until stopped. Native playit credentials live under MCServerSwitcher/playit/account in local application data and are excluded from worlds, app logs, sources and installer payloads. The UI never forwards raw agent output or private guest-login URLs.

## Friends preview

Open **Players → Friends** to save exact Java usernames or Bedrock gamertags for the selected profile. Auto-add is on by default for saved friends: additions made while stopped wait until that server is ready. Commands are re-applied after each server restart, with Java and Bedrock lists kept separate. **Sync now / retry** resends matching entries on demand, including when automatic sync is off.

Saturn sends normal Minecraft whitelist/allowlist commands; it never grants operator access or automatically switches the server into whitelist-only mode. “Command sent” is not confirmation that Minecraft accepted a name: check the game console. **Forget** only removes a saved friend. Existing server whitelist entries remain until explicitly removed in player management.
