# Saturn Server Launcher 1.0.0-beta.19 — SSH guide preview

- One first-time VPS & SSH setup section with nine numbered steps.
- Copyable commands labelled for Ubuntu or Windows, expected results and fixes after failures.
- SSH key setup, identity verification, Saturn connection setup, local/public TCP and UDP listener checks, firewalls and DNS diagnosis.
- Commands copy to the clipboard only; Saturn does not execute help commands.

# Saturn Server Launcher 1.0.0-beta.18

Created by Nova. Free under MIT.

- Saturn branding throughout install/uninstall prompts, app messages and release downloads.
- GitHub repository renamed Saturn-Server-Launcher.
- Help section with 14 searchable, expandable troubleshooting topics covering VPS/SSH, ports, connection refused, DNS, Cloudflare and app issues.
- Join-address editor stays in Settings → Domain & display; DNS instructions begin “At your domain panel…”.
- Saved domains refresh the displayed join address without changing DNS at your provider.

Exit Saturn from the tray before installing SaturnSetup.exe over your existing installation. Profiles, worlds and preferences are preserved. Older builds need this manual installer once because release assets now use Saturn names. Future updates use the new repository and installer name.

The installer is unsigned; Windows may show an unknown-publisher warning. Requires 64-bit Windows 10+ and Python 3.10+ with pip, Tcl/Tk and the Python launcher.
