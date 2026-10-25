# Saturn Server Launcher — draft privacy notice

Effective date: to be set when the Store edition is released.
Owner must review this notice and provide a permanent public URL before submission.

Saturn runs on your computer. This build does not include developer-operated
accounts, advertising, analytics or automatic crash-report uploads.

## Information on your computer

Saturn stores server profiles, folders, ports, preferences, task schedules, SSH
known-host fingerprints and application logs locally. Server files can contain
player names, UUIDs, IP addresses, chat and other data produced by the selected
server software. You control your server and should inform players of your practices.

SSH passwords and key passphrases are held in memory for the session. Private keys
are read from a file you choose. An optionally remembered CurseForge API key is
protected using Windows account encryption. Do not share keys or unredacted logs.

## Connections to third parties

At your request Saturn connects to your VPS using the SSH account and credentials
you supply. Player traffic passes through that VPS; its provider can observe network
metadata. Using a VPS join address does not guarantee anonymity.

Server, modpack, artwork, loader and runtime downloads contact upstream services,
including Microsoft/Mojang, PaperMC, Forge, CurseForge, Eclipse Adoptium, GitHub and
content hosts referenced by those services. Requests can disclose your public IP,
request metadata and any service-specific API credential needed for that request.
Those services have their own policies. Minecraft servers and mods can make their
own network requests independently of Saturn.

The Store edition's application updates are handled by Microsoft Store. Microsoft
may collect Store/device data under its own privacy statement.

## Control and deletion

You can forget the saved CurseForge key in Settings, remove profiles, edit schedules,
and choose whether to use VPS hosting. Application settings/logs and game folders
have different locations. Removing a profile does not erase the world. Uninstall
and cache retention for the MSIX edition must be verified before this notice is final;
do not rely on uninstall to erase game folders or backups. Back up worlds first.

If you send an issue or diagnostic file to the project, it becomes information you
choose to share on GitHub. Redact credentials, hostnames/IPs and personal data.
Support: https://github.com/5NoVa2/Nova-Server-Studio/issues
