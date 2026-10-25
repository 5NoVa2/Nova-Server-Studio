"""Restrict agent credentials to the current account and Windows SYSTEM."""
import os
import subprocess
from pathlib import Path


def protect_agent_directory(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    if os.name!='nt':
        directory.chmod(0o700)
        for child in directory.iterdir():
            if child.is_file():child.chmod(0o600)
        return
    # Construct fresh ACLs: removing inheritance alone leaves old explicit grants.
    quoted=str(directory.resolve()).replace("'","''")
    script=r"""$ErrorActionPreference='Stop'
$user=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
$system=New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18')
$path='PATH_LITERAL'
$acl=New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true,$false)
foreach ($sid in @($user,$system)) {
 $rule=New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
 $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $path -AclObject $acl
Get-ChildItem -LiteralPath $path -File | ForEach-Object {
 $fileAcl=New-Object System.Security.AccessControl.FileSecurity
 $fileAcl.SetAccessRuleProtection($true,$false)
 foreach ($sid in @($user,$system)) {
  $fileAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')))
 }
 Set-Acl -LiteralPath $_.FullName -AclObject $fileAcl
}
""".replace('PATH_LITERAL',quoted)
    powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    result=subprocess.run([str(powershell),'-NoProfile','-NonInteractive','-Command',script],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Could not protect playit credentials. Agent was not started.')
