# Security hardening

Reverse SSH forwarding accepts at most 64 simultaneous connections per tunnel.
Each socket has a 120-second inactivity timeout. This bounds launcher resources;
it does not replace upstream denial-of-service protection.

The playit agent needs a readable local secret configuration. Before launch,
Saturn replaces the account-directory and existing file ACLs with access for the
current Windows account and SYSTEM only. New files inherit that private ACL.
This cannot protect against malware running as the same account or administrators.
Windows ACL behavior still requires validation on a real Windows machine.

SSH first-use installation uses isolated pip, the official PyPI index, binary
wheels only, and a version/hash lock including transitive dependencies. The new
cache directory prevents reuse of the old unpinned SSH dependency installation.
To upgrade, resolve supported Windows x64 wheels, independently review versions,
regenerate app/ssh-requirements.txt, and test supported Python versions.

## Release signing required

Automatic installer launch is disabled until TRUSTED_PUBLISHER_THUMBPRINTS in
app/updater.py contains the Authenticode certificate thumbprint(s) of the publisher.
Obtain the certificate and verify its identity outside the GitHub release channel;
do not fetch the trusted thumbprint from release metadata. Keep signing credentials
outside the repository and restrict release workflow permissions.

Sign SaturnSetup.exe with that certificate before generating SHA256SUMS.txt.
The handoff verifies the checksum and Windows Authenticode trust and requires the
signer to match the pinned publisher before execution. Unsigned or differently
signed installers are refused. Certificate rotation needs a release trusted by
existing clients that adds the next certificate before retiring the old one.

Existing 1.0.3 clients do not gain these protections until they install this change.
No signing credential or certificate was created as part of this patch. An attacker
who controls the initial install or the local account can still replace the app.
