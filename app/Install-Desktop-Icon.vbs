Option Explicit
Dim shell, files, folder, desktop, shortcut
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
Set shortcut = shell.CreateShortcut(files.BuildPath(desktop, "Saturn Server Launcher.lnk"))
shortcut.TargetPath = files.BuildPath(shell.ExpandEnvironmentStrings("%SystemRoot%"), "System32\wscript.exe")
shortcut.Arguments = Chr(34) & files.BuildPath(folder, "Launch.vbs") & Chr(34)
shortcut.WorkingDirectory = folder
shortcut.Description = "Saturn Server Launcher - Created by Nova"
shortcut.IconLocation = files.BuildPath(folder, "Saturn.ico") & ",0"
shortcut.WindowStyle = 1
shortcut.Save
