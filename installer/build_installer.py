from pathlib import Path
root=Path(__file__).resolve().parent
payload=root.parent/'app'
files=sorted(p for p in payload.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
install=[];remove=[];parents=set()
for p in files:
 rel=p.relative_to(payload);parent=str(rel.parent).replace('/','\\')
 install.append('SetOutPath "$INSTDIR'+('\\'+parent if parent!='.' else '')+'"')
 install.append('File "${PAYLOAD_DIR}/'+rel.as_posix()+'"')
 remove.append('Delete "$INSTDIR\\'+str(rel).replace('/','\\')+'"')
 if p.suffix=='.py':remove.append('Delete "$INSTDIR\\__pycache__\\'+p.stem+'.cpython-*.pyc"')
 if parent!='.':parents.add(parent)
remove.extend('RMDir "$INSTDIR\\'+p+'"' for p in sorted(parents,reverse=True))
script=r'''; Nova per-user installer. Build: makensis NovaSetup.nsi
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
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Nova Server Studio"
VIAddVersionKey "FileDescription" "Nova Server Studio Public Beta Setup"
VIAddVersionKey "FileVersion" "1.0.0"
VIAddVersionKey "ProductVersion" "1.0.0"
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
@PAYLOAD@
 SetOutPath "$INSTDIR"
 File /oname=Installer-Source.nsi "NovaSetup.nsi"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\Nova Server Studio"
 CreateShortcut "$DESKTOP\Nova Server Studio.lnk" "$WINDIR\System32\wscript.exe" '$\"$INSTDIR\Launch.vbs$\"' "$INSTDIR\Nova.ico"
 CreateShortcut "$SMPROGRAMS\Nova Server Studio\Nova Server Studio.lnk" "$WINDIR\System32\wscript.exe" '$\"$INSTDIR\Launch.vbs$\"' "$INSTDIR\Nova.ico"
 CreateShortcut "$SMPROGRAMS\Nova Server Studio\Uninstall Nova.lnk" "$INSTDIR\Uninstall.exe"
 WriteRegStr HKCU "Software\NovaServerStudio" "InstallDir" "$INSTDIR"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "DisplayName" "Nova Server Studio"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaServerStudio" "DisplayVersion" "1.0.0"
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
@DELETE@
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
'''
(root.parent/'dist').mkdir(exist_ok=True)
(root/'NovaSetup.nsi').write_text(script.replace('@PAYLOAD@','\n'.join(install)).replace('@DELETE@','\n'.join(remove)))
print('Generated installer for',len(files),'application files')
