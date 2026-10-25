Option Explicit
Dim shell, filesystem, folder, command
Set shell = CreateObject("WScript.Shell")
Set filesystem = CreateObject("Scripting.FileSystemObject")
folder = filesystem.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
command = "pyw -3 " & Chr(34) & folder & "\Launch.pyw" & Chr(34)
' pythonw already has no console. SW_HIDE can also hide Qt's first window.
shell.Run command, 1, False
