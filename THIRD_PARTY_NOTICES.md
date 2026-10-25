# Third-party notices

Saturn's MIT license covers Saturn's original application and build source only.
It does not replace the licenses/terms of any dependency or downloaded server.

- **NSIS**: the installer contains unmodified NSIS runtime/plugin components.
  Upstream: https://nsis.sourceforge.io/ and
  https://nsis.sourceforge.io/Docs/AppendixI.html . The applicable upstream
  copyright/license text supplied with the build is included in
  `app/licenses/NSIS-copyright.txt`. This includes the zlib/libpng license,
  component-specific notices and the LZMA licensing exception. NSIS source is
  available from https://sourceforge.net/projects/nsis/files/ and its source
  repository linked by the upstream project. Saturn's generated installer source
  is also included in the installed application.
- **Python**: supplied by the user, not included in the installer.
  https://docs.python.org/3/license.html
- **Qt / PySide6 / Shiboken**: obtained separately by first-run pip installation
  or requirements installation, not bundled into SaturnSetup.exe. These retain
  their upstream LGPL/GPL/commercial licensing options and notices. Users may
  inspect or replace the separately installed libraries.
  https://doc.qt.io/qtforpython-6/licenses.html
- **Paramiko and its dependencies**: downloaded separately for SSH support.
  https://www.paramiko.org/ and the installed distributions' license files.
- **Pillow / pystray**: optional downloads used by the legacy Tk frontend,
  not bundled. Their installed distributions contain the applicable licenses.
- **Minecraft / Bedrock / Paper / Spigot BuildTools / Forge / NeoForge / Fabric
  and CurseForge packs/mods**: downloaded only when requested by the user.
  They are not included in the Saturn installer or source archive and are not
  sublicensed under Saturn's MIT license. Their EULAs, author permissions,
  upstream licenses and API terms still apply.

No Mojang/Microsoft logos, Minecraft binaries, modpacks, private SSH keys,
shared CurseForge API keys or user server worlds are included in this release.

playit.gg optional agent: https://github.com/playit-cloud/playit-agent
Upstream BSD-2-Clause licensing applies. Downloaded separately from the official release, not bundled in Saturn. This integration pins supported portable 0.17.1 to avoid installing a Windows service; its SHA-256 is verified before use. Third-party account/service terms apply independently. Saturn is not affiliated with playit.gg.
