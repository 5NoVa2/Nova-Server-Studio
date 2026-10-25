# Privacy policy

Saturn Server Launcher stores server profiles, settings, worlds, logs, and backups
locally. It does not include a developer-operated analytics or telemetry service.

Network requests occur as part of features the user chooses:

- First launch can download the Qt interface dependencies from PyPI. SSH setup
  downloads its dependencies from PyPI when needed.
- Server installation downloads manifests, server files, and Java runtimes from
  the selected engine's upstream services, including Mojang/Microsoft, Paper,
  Spigot, Forge, and Eclipse Adoptium. Custom download links contact that host.
- CurseForge browsing/downloads contact CurseForge with the user's API key.
- Update checks and downloads contact GitHub.
- VPS features connect to the host the user specifies using SSH.
- Optional playit hosting runs the official playit agent, contacts playit services,
  and reads assigned tunnel addresses using the user's agent credentials.
- Players' game connections are processed by the selected server software and,
  when enabled, the selected tunnel provider.

These services receive network information such as an IP address and requested
resources; authenticated features also send the credentials required by the
selected service. Their own terms and privacy policies apply:

- [GitHub](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)
- [PyPI](https://policies.python.org/pypi.org/Privacy-Notice/)
- [Microsoft/Minecraft](https://privacy.microsoft.com/privacystatement)
- [CurseForge/Overwolf](https://www.overwolf.com/legal/privacy/)
- [playit.gg](https://playit.gg/privacy-policy)
- [Eclipse Foundation/Adoptium](https://www.eclipse.org/legal/privacy/)

Other server engine providers, the user's VPS provider, and independently installed
mods/plugins may process data under their own policies. Review those providers
before using them. Saturn does not sandbox third-party game code.

The remembered CurseForge API key uses Windows account encryption. The playit
agent needs a local credential file, protected by account-specific file permissions
in the security-hardening changes. Other software running as the same user can
still access user data. Do not post credentials or private server logs publicly.

Uninstallation retains profiles, credentials, downloaded runtimes, and worlds so
users can reinstall without losing data. Users can remove retained data separately
once their servers are stopped and anything needed has been backed up.
