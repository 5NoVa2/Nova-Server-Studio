; Nova per-user installer. Build: makensis NovaSetup.nsi
Unicode True
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
!ifndef PAYLOAD_DIR
!define PAYLOAD_DIR "../app"
!endif
Name "Nova Server Studio"
OutFile "../dist/NovaSetup.exe"
InstallDir "$LOCALAPPDATA\Programs\Nova Server Studio"
InstallDirRegKey HKCU "Software\NovaServerStudio" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "Created by Nova"
VIProductVersion "1.0.0.2"
VIAddVersionKey "ProductName" "Nova Server Studio"
VIAddVersionKey "FileDescription" "Nova Server Studio Public Beta Setup"
VIAddVersionKey "FileVersion" "1.0.0-beta.2"
VIAddVersionKey "ProductVersion" "1.0.0-beta.2"
VIAddVersionKey "LegalCopyright" "Created by Nova"
Icon "${PAYLOAD_DIR}/Nova.ico"
UninstallIcon "${PAYLOAD_DIR}/Nova.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to Nova Server Studio"
!define MUI_WELCOMEPAGE_TEXT "Install Nova for your Windows account.$\r$\n$\r$\nSetup creates desktop and Start menu shortcuts and an uninstall entry.$\r$\n$\r$\nNova uses your existing 64-bit Python 3.10 or newer, including pip, Tcl/Tk and the Python launcher. First launch downloads Qt if needed.$\r$\n$\r$\nExit all running Nova copies from the tray before continuing. Your server files and preferences are kept."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "../LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Open Nova Server Studio"
!define MUI_FINISHPAGE_RUN_FUNCTION StartNova
!define MUI_FINISHPAGE_TEXT "Nova has been installed.$\r$\n$\r$\nUse the desktop shortcut to launch it. Software rendering is enabled by default.$\r$\n$\r$\nFirst launch may download Qt. Existing server settings and the remembered CurseForge key are reused."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
 SetShellVarContext current
 SetRegView 64
 ${IfNot} ${RunningX64}
  MessageBox MB_OK|MB_ICONSTOP "Nova requires 64-bit Windows."
  Abort
 ${EndIf}
 ${IfNot} ${AtLeastWin10}
  MessageBox MB_OK|MB_ICONSTOP "Nova requires Windows 10 or newer."
  Abort
 ${EndIf}
 checkRunning:
 FindWindow $0 "" "Nova | Minecraft Server Studio"
 ${If} $0 != 0
  MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Nova is running. Right-click its tray icon and choose Exit Nova, then click Retry." IDRETRY checkRunning
  Abort
 ${EndIf}
 nsExec::ExecToStack `py -3 -c "import sys,struct,tkinter,pip;sys.exit(0 if sys.version_info >= (3,10) and struct.calcsize('P') == 8 else 1)"`
 Pop $0
 Pop $1
 ${If} $0 != 0
  MessageBox MB_OK|MB_ICONSTOP "Nova needs 64-bit Python 3.10 or newer with pip, Tcl/Tk and the Python launcher. Install Python, then run NovaSetup again."
  ExecShell "open" "https://www.python.org/downloads/windows/"
  Abort
 ${EndIf}
FunctionEnd

Function StartNova
 SetOutPath "$INSTDIR"
 ExecShell "open" "$WINDIR\System32\wscript.exe" '$\"$INSTDIR\Launch.vbs$\"'
FunctionEnd

Section "Nova Server Studio" SEC_MAIN
 SetShellVarContext current
 SetRegView 64
 SetOverwrite on
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/Install-Desktop-Icon.vbs"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/LICENSE.txt"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/Launch.bat"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/Launch.pyw"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/Launch.vbs"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/Nova.ico"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/README.txt"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/THIRD_PARTY_NOTICES.txt"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/app.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/backups.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/bedrock.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/bubble_ui.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/connection_settings.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/control.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/curse_browser.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/curse_catalog.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/engines.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/host_ports.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/hosts.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/inline_dialogs.py"
SetOutPath "$INSTDIR\licenses"
File "${PAYLOAD_DIR}/licenses/NSIS-copyright.txt"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/players.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/process_manager.py"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/Main.qml"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/NButton.qml"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/NCombo.qml"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/NField.qml"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/NTab.qml"
SetOutPath "$INSTDIR\qml"
File "${PAYLOAD_DIR}/qml/Panel.qml"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/qt_app.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/qt_runtime.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/runtime.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/secret_store.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/server_files.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/server_locations.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/server_settings_ui.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/settings_store.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/ssh_backend.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/theme.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/tray_support.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/udp_relay.py"
SetOutPath "$INSTDIR"
File "${PAYLOAD_DIR}/vps_setup.sh"
 SetOutPath "$INSTDIR"
 File /oname=Installer-Source.nsi "NovaSetup.nsi"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\Nova Server Studio"
 CreateShortcut "$DESKTOP\Nova Server Studio.lnk" "$WINDIR\System32\wscript.exe" '$\"$INSTDIR\Launch.vbs$\"' "$INSTDIR\Nova.ico"
 CreateShortcut "$SMPROGRAMS\Nova Server Studio\Nova Server Studio.lnk" "$WINDIR\System32\wscript.exe" '$\"$INSTDIR\Launch.vbs$\"' "$INSTDIR\Nova.ico"
 CreateShortcut "$SMPROGRAMS\Nova Server Studio\Uninstall Nova.lnk" "$INSTDIR\Uninstall.exe"
 WriteRegStr HKCU "Software\NovaServerStudio" "InstallDir" "$INSTDIR"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "DisplayName" "Nova Server Studio"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "DisplayVersion" "1.0.0-beta.2"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "Publisher" "Nova"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "DisplayIcon" "$INSTDIR\Nova.ico"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "InstallLocation" "$INSTDIR"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "NoModify" 1
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "NoRepair" 1
SectionEnd

Function un.onInit
 SetShellVarContext current
 SetRegView 64
 checkRunning:
 FindWindow $0 "" "Nova | Minecraft Server Studio"
 ${If} $0 != 0
  MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Exit Nova from its tray icon before uninstalling, then click Retry." IDRETRY checkRunning
  Abort
 ${EndIf}
FunctionEnd

Section "Uninstall"
 SetShellVarContext current
 SetRegView 64
 ; Delete only known application files. Never recursively remove server folders.
Delete "$INSTDIR\Install-Desktop-Icon.vbs"
Delete "$INSTDIR\LICENSE.txt"
Delete "$INSTDIR\Launch.bat"
Delete "$INSTDIR\Launch.pyw"
Delete "$INSTDIR\Launch.vbs"
Delete "$INSTDIR\Nova.ico"
Delete "$INSTDIR\README.txt"
Delete "$INSTDIR\THIRD_PARTY_NOTICES.txt"
Delete "$INSTDIR\app.py"
Delete "$INSTDIR\__pycache__\app.cpython-*.pyc"
Delete "$INSTDIR\backups.py"
Delete "$INSTDIR\__pycache__\backups.cpython-*.pyc"
Delete "$INSTDIR\bedrock.py"
Delete "$INSTDIR\__pycache__\bedrock.cpython-*.pyc"
Delete "$INSTDIR\bubble_ui.py"
Delete "$INSTDIR\__pycache__\bubble_ui.cpython-*.pyc"
Delete "$INSTDIR\connection_settings.py"
Delete "$INSTDIR\__pycache__\connection_settings.cpython-*.pyc"
Delete "$INSTDIR\control.py"
Delete "$INSTDIR\__pycache__\control.cpython-*.pyc"
Delete "$INSTDIR\curse_browser.py"
Delete "$INSTDIR\__pycache__\curse_browser.cpython-*.pyc"
Delete "$INSTDIR\curse_catalog.py"
Delete "$INSTDIR\__pycache__\curse_catalog.cpython-*.pyc"
Delete "$INSTDIR\engines.py"
Delete "$INSTDIR\__pycache__\engines.cpython-*.pyc"
Delete "$INSTDIR\host_ports.py"
Delete "$INSTDIR\__pycache__\host_ports.cpython-*.pyc"
Delete "$INSTDIR\hosts.py"
Delete "$INSTDIR\__pycache__\hosts.cpython-*.pyc"
Delete "$INSTDIR\inline_dialogs.py"
Delete "$INSTDIR\__pycache__\inline_dialogs.cpython-*.pyc"
Delete "$INSTDIR\licenses\NSIS-copyright.txt"
Delete "$INSTDIR\players.py"
Delete "$INSTDIR\__pycache__\players.cpython-*.pyc"
Delete "$INSTDIR\process_manager.py"
Delete "$INSTDIR\__pycache__\process_manager.cpython-*.pyc"
Delete "$INSTDIR\qml\Main.qml"
Delete "$INSTDIR\qml\NButton.qml"
Delete "$INSTDIR\qml\NCombo.qml"
Delete "$INSTDIR\qml\NField.qml"
Delete "$INSTDIR\qml\NTab.qml"
Delete "$INSTDIR\qml\Panel.qml"
Delete "$INSTDIR\qt_app.py"
Delete "$INSTDIR\__pycache__\qt_app.cpython-*.pyc"
Delete "$INSTDIR\qt_runtime.py"
Delete "$INSTDIR\__pycache__\qt_runtime.cpython-*.pyc"
Delete "$INSTDIR\runtime.py"
Delete "$INSTDIR\__pycache__\runtime.cpython-*.pyc"
Delete "$INSTDIR\secret_store.py"
Delete "$INSTDIR\__pycache__\secret_store.cpython-*.pyc"
Delete "$INSTDIR\server_files.py"
Delete "$INSTDIR\__pycache__\server_files.cpython-*.pyc"
Delete "$INSTDIR\server_locations.py"
Delete "$INSTDIR\__pycache__\server_locations.cpython-*.pyc"
Delete "$INSTDIR\server_settings_ui.py"
Delete "$INSTDIR\__pycache__\server_settings_ui.cpython-*.pyc"
Delete "$INSTDIR\settings_store.py"
Delete "$INSTDIR\__pycache__\settings_store.cpython-*.pyc"
Delete "$INSTDIR\ssh_backend.py"
Delete "$INSTDIR\__pycache__\ssh_backend.cpython-*.pyc"
Delete "$INSTDIR\theme.py"
Delete "$INSTDIR\__pycache__\theme.cpython-*.pyc"
Delete "$INSTDIR\tray_support.py"
Delete "$INSTDIR\__pycache__\tray_support.cpython-*.pyc"
Delete "$INSTDIR\udp_relay.py"
Delete "$INSTDIR\__pycache__\udp_relay.cpython-*.pyc"
Delete "$INSTDIR\vps_setup.sh"
RMDir "$INSTDIR\qml"
RMDir "$INSTDIR\licenses"
 RMDir "$INSTDIR\__pycache__"
 Delete "$INSTDIR\Installer-Source.nsi"
 Delete "$INSTDIR\Uninstall.exe"
 Delete "$DESKTOP\Nova Server Studio.lnk"
 Delete "$SMPROGRAMS\Nova Server Studio\Nova Server Studio.lnk"
 Delete "$SMPROGRAMS\Nova Server Studio\Uninstall Nova.lnk"
 RMDir "$SMPROGRAMS\Nova Server Studio"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio"
 DeleteRegKey HKCU "Software\NovaServerStudio"
 RMDir "$INSTDIR"
 ; Preferences, encrypted API key, downloaded runtimes and all server files remain.
SectionEnd
