# Store preview build results — 2026-10-25

Candidate source commit: 429bcae265fbeafbb4034b12042d1698876963d4
Windows build: https://github.com/5NoVa2/Nova-Server-Studio/actions/runs/40213266965
Artifact ID: 12606108775 (GitHub artifact retention is 14 days).

- 71 local checks passed.
- Windows Server 2022 GitHub runner / Python 3.12 x64 build succeeded.
- PyInstaller bundled Python, Qt/QML, SSH and dependent libraries.
- Frozen app smoke check loaded QML and Paramiko 4.0.0 in Store mode.
- Windows MakeAppx validated and created the preview MSIX.
- Downloaded artifact SHA256: 53aa3341d4a2e0b4292d2fb86debd1e2a00cd30b660df4140723238e218170ec
- MSIX SHA256: 07d25d2baa7da7868b01373d18747d436515141f0fab7ba4c8a70c175ab50f29
- Package ZIP integrity checked; 4071 entries including bundled Saturn.exe and Store channel marker.

Development identity: SaturnServerLauncher.Preview / CN=SaturnDevelopment.
This is UNSIGNED and NOT a Store-submittable identity. It is not a public app release.

The screenshots show the candidate source UI in Store mode, using an explicitly
named Sample survival profile and no live server. They are not proof of installed
MSIX behavior. Recheck screenshots after the final publisher identity build.

Remaining: verified developer account and reserved product identity, installed
MSIX testing on clean Windows, WACK, actual server/tray/tunnel tests, privacy/support
URL review, dependency-license audit, age-rating/export questionnaire and Store
certification. No terms were accepted and no Microsoft Store submission was made.
