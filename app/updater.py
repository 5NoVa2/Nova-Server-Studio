"""Explicit GitHub release updates; verified download, install only after exit."""
import hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from process_manager import check_cancelled

VERSION='1.01.1'
PRIVATE_BUILD=False
REPO='5NoVa2/Saturn-Server-Launcher'
API=f'https://api.github.com/repos/{REPO}/releases?per_page=100'


def version_key(tag):
    match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?',tag or '')
    if not match:return None
    return (*map(int,match.group(1,2,3)),1 if match[4] is None else 0,int(match[4] or 0))


def asset_url(url,tag,name):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.netloc!='github.com' or parsed.query or parsed.fragment or parsed.path!=f'/{REPO}/releases/download/{tag}/{name}':
        raise ValueError('Release asset is not from the official Saturn repository.')
    return url


def select_release(rows,current=VERSION):
    if not isinstance(rows,list):raise ValueError('GitHub returned an invalid release list.')
    choices=[]
    for row in rows:
        if not isinstance(row,dict) or row.get('draft'):continue
        key=version_key(row.get('tag_name'))
        if key is None or key<=version_key(current):continue
        assets={a.get('name'):a for a in row.get('assets',[]) if isinstance(a,dict)}
        if not {'SaturnSetup.exe','SHA256SUMS.txt'}<=assets.keys():continue
        tag=row['tag_name']
        choices.append((key,dict(version=tag,notes=str(row.get('body') or '')[:20000],
            installer=asset_url(assets['SaturnSetup.exe']['browser_download_url'],tag,'SaturnSetup.exe'),
            checksums=asset_url(assets['SHA256SUMS.txt']['browser_download_url'],tag,'SHA256SUMS.txt'))))
    return max(choices,key=lambda x:x[0])[1] if choices else None


def fetch_bytes(url,limit):
    check_cancelled()
    with urlopen(Request(url,headers={'User-Agent':'NovaServerStudio/'+VERSION,'Accept':'application/vnd.github+json' if url==API else 'application/octet-stream'}),timeout=45) as response:
        data=response.read(limit+1)
    if len(data)>limit:raise ValueError('Update metadata exceeds size limit.')
    check_cancelled();return data


def check_updates():return select_release(json.loads(fetch_bytes(API,4*1024**2)))


def installer_checksum(data):
    matches=[]
    for line in data.decode('utf-8').splitlines():
        match=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?SaturnSetup\.exe',line.strip())
        if match:matches.append(match[1].lower())
    if len(matches)!=1:raise ValueError('Release must contain exactly one SHA-256 checksum for SaturnSetup.exe.')
    return matches[0]


def download_update(release,cache):
    tag=release['version'];asset_url(release['installer'],tag,'SaturnSetup.exe');asset_url(release['checksums'],tag,'SHA256SUMS.txt')
    expected=installer_checksum(fetch_bytes(release['checksums'],65536))
    parent=Path(cache)/'updates';parent.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(prefix='nova-',dir=parent));dest=folder/'SaturnSetup.exe'
    try:
        digest=hashlib.sha256();size=0
        with urlopen(Request(release['installer'],headers={'User-Agent':'NovaServerStudio/'+VERSION}),timeout=90) as response,dest.open('wb') as output:
            while True:
                check_cancelled();chunk=response.read(1024*1024)
                if not chunk:break
                size+=len(chunk)
                if size>100*1024**2:raise ValueError('Installer exceeds the 100 MB update limit.')
                digest.update(chunk);output.write(chunk)
        if digest.hexdigest()!=expected:raise ValueError('Update checksum mismatch. Installer was not launched.')
        if dest.read_bytes()[:2]!=b'MZ':raise ValueError('Downloaded asset is not a Windows installer.')
        return str(dest),expected
    except Exception:
        dest.unlink(missing_ok=True);folder.rmdir();raise


def launch_after_exit(path,expected,pid=None):
    if os.name!='nt':raise ValueError('Automatic installation is supported on Windows only.')
    path=Path(path).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Installer changed. Download it again.')
    quoted=str(path).replace("'","''");pid=int(pid or os.getpid())
    # This helper is deliberately outside Saturn's owned server-process registry.
    # Wait for Saturn to exit, recheck the bytes, then open the standard installer.
    script=f"$ErrorActionPreference='Stop'; $p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ if (-not $p.WaitForExit(60000)) {{ exit 1 }} }}; if ((Get-FileHash -LiteralPath '{quoted}' -Algorithm SHA256).Hash.ToLower() -ne '{expected}') {{ exit 2 }}; Start-Process -FilePath '{quoted}'"
    powershell=Path(os.environ['SystemRoot'])/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    return subprocess.Popen([str(powershell),'-NoProfile','-NonInteractive','-WindowStyle','Hidden','-Command',script],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
