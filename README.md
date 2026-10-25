# Nova Server Studio

Free, open-source Minecraft server management for Windows. Created by **Nova**.

**First public beta: 1.0.0-beta.6.** Local hosting, multiple independent server
profiles, and optional reverse SSH hosting through a VPS—all in one window.

## Features

- Vanilla, Paper, Spigot, Forge, CurseForge server packs and native Bedrock.
- Multiple simultaneous hosts with separate folders, ports, logs and settings.
- One main servers folder; new profiles create named subfolders automatically.
- Java TCP and Bedrock UDP tunnel selection and custom game ports.
- Server properties editor, configuration files, mod/plugin management.
- Console-based player list, kick, operator and allowlist controls; Java ban/pardon.
- Manual backups, system tray hosting, full screen and reduced motion.
- CurseForge pack search, release details, artwork and manifest mod lists.
- Optional remembered CurseForge API key encrypted for your Windows account.

## Install

1. Install **64-bit Python 3.10 or newer** from [python.org](https://www.python.org/downloads/windows/), including pip, Tcl/Tk and the Python launcher.
2. Download `NovaSetup.exe` from this repository's **Releases** tab, once a release is published.
3. Run setup, then open **Nova Server Studio** from your desktop.
4. First launch downloads Qt if needed. Internet access is required for downloads.

The installer is currently unsigned. This is a beta release; test your setup
before using it for a long-running public server.

## Create a server

1. In **Settings**, choose **Main servers folder** once.
2. Type a profile name in the top bar and click **+ Add**.
3. On **Server**, choose software/version, read and accept the Minecraft EULA,
   then click **Install / switch**. The server folder is created automatically.
4. Use **Start local** for local play. Connect from the same PC using `localhost`
   and that profile's **local** game port.

Local hosting works without a VPS. No VPS, domain, password or API key is
preconfigured in this public build. Existing preferences on an upgrading PC
are retained.

**Installing/switching replaces all files in the selected server folder after
confirmation. Backups are manual.** Stop the selected server before changing
files or making a consistent backup. Click **Manual backup** to keep a copy.

## Optional public hosting through a VPS

Supply your own Ubuntu **24.04** VPS and SSH credentials in Settings. Click
**Configure VPS**, then **Start hosting**. New host fingerprints require trust
confirmation; verify them with your VPS provider before accepting.

Each simultaneous Java server needs a unique local TCP port. Each Bedrock
server needs unique local IPv4/IPv6 UDP ports. Profiles sharing a VPS need
unique public ports for their protocol. Nova assigns distinct defaults.

After adding profiles or changing public ports, run **Configure VPS** again.
It needs root or passwordless sudo and changes SSH forwarding permissions and
active UFW game-port rules. Allow the same ports in provider firewalls too.
Java join addresses need `:public-port` when using a non-default port.
Bedrock clients enter the host and public UDP port separately.

A domain is optional. If using one, point its A record at your VPS IPv4 address.
No home-router port forwarding is required for this reverse-tunnel setup.
Bedrock UDP is carried over SSH/TCP; packet loss can increase latency.
Nova itself is free; VPS providers and other services may charge separately.

## CurseForge

Use your own approved CurseForge API key in **Modpacks**. Nova does not provide
a shared key. Published server packs and author/API download permissions are
required. Client mod lists can differ from server-pack contents.
**Forget key** removes the remembered key. SSH passwords/passphrases remain in
memory; private key files stay on your PC.

## Tray and multiple servers

Switching profiles keeps other hosts running. **Stop hosting** affects the
selected profile; **Stop all** stops every host. Closing the window minimizes
to the tray. Right-click the tray icon and choose **Exit Nova** to save and
stop all servers. Remaining Nova-owned process trees are ended after the
shutdown timeout; unrelated Java/Python processes are left alone.

Uninstall through Windows Installed apps. Server worlds, backups, profile
preferences and cached runtimes are preserved.

## Build from source

```powershell
python -m pip install -r requirements.txt
python app/Launch.pyw
```

To build the Windows installer, install [NSIS 3](https://nsis.sourceforge.io/),
then run:

```powershell
python installer/build_installer.py
makensis installer/NovaSetup.nsi
```

The installer is written to `dist/NovaSetup.exe`. The source includes the
installer generator and its generated script. Build in a clean workspace;
never add local preferences, API keys, SSH keys, logs or server worlds.

Tests use isolated temporary folders and include a public-build smoke check:

```powershell
python -m unittest discover -s tests -v
```

## Beta limitations and support

- Windows 10/11 x64 is the target. Native Windows runtime and live remote play
  need broader community testing; source-level/software-rendering checks are
  not a guarantee on every PC or network.
- Player lists parse standard English console messages. Custom/localized
  servers may report players differently. Bedrock has no native ban/pardon.
- Arbitrary imported server ZIPs may need their supplied launcher. Built-in
  installers create Nova launch metadata.
- Logs: `%LOCALAPPDATA%\MCServerSwitcher\app.log`. Remove IPs, usernames,
  private paths and other personal data before sharing diagnostics publicly.
- Report reproducible issues through this repository's Issues tab. Never post
  passwords, private keys or API keys.

## License

Nova's code is licensed under [MIT](LICENSE). Dependencies, installer components
and downloaded game/server files retain their own licenses and terms; see
[third-party notices](THIRD_PARTY_NOTICES.md).

Not an official Minecraft product. Not approved by or associated with Mojang
or Microsoft. Minecraft is a trademark of its respective owners.

See RELEASE_NOTES.md for the beta.2 save, performance, version-selector and backup restore changes.

## VPS port ranges

In Settings, enter a Java TCP range such as `25565-25575` and optionally a
Bedrock UDP range such as `19132-19142`. Comma-separated ports/ranges also work.
Save preferences, then run Configure VPS. This updates SSH forwarding permissions
and an active UFW firewall. Open the same ranges in any provider firewall.

Each server still uses one public game port. New profiles inherit the ranges and
choose an unused public port. Existing assigned profile ports stay included.
Blank ranges preserve the existing per-profile behavior. Range permissions are
combined across profiles with the same VPS/SSH user; change inherited ranges in
those profiles too if shrinking the permitted set. Old UFW allowances remain.

## App updates

Settings > Nova updates > Check for updates reads public releases from this
repository, including betas. Download update verifies the installer against the
release SHA256SUMS.txt. Stop all servers and tunnels, then choose Install update
and confirm. Nova saves preferences/edits and closes; a hidden Windows helper waits
for Nova to exit, rechecks the installer hash, and opens standard setup. Install
over the existing location to retain profiles, worlds, backups and remembered keys.
No updates install automatically. This verifies release-file integrity; the
installer remains unsigned. Internet access to GitHub and its asset CDN is needed.

## Silver orbital interface

The dashboard has a selected-server hero, server cards with live status/player
counts and shortcuts. Click a card to select that profile in the large dashboard panel. Quick controls stay on the dashboard; Server setup opens the full Server tab.
New CurseForge selections remember their artwork; existing selections use Nova's
orbital mark until selected again. Panels and controls use a black/silver finish
and lightweight transitions compatible with the software renderer.

The 2.55-second startup scene can be skipped or disabled in Settings. Reduced
motion skips it, and restoring Nova from the tray does not replay it. Appearance
preferences synchronize across existing profiles and are inherited by new ones.
