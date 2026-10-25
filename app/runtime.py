from process_manager import check_cancelled
import hashlib
import json
import os
import platform
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
CACHE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.cache')))/'MCServerSwitcher'
MANIFEST = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
USER_AGENT = 'NovaServerStudio/1.0.0-beta.4'

def get_json(url, headers=None):
    check_cancelled()
    with urlopen(Request(url,headers={'User-Agent':USER_AGENT, **(headers or {})}),timeout=60) as r:
        data=json.load(r)
        check_cancelled()
        return data


def download(url,path,algorithm=None,checksum=None,limit=2*1024**3,headers=None):
    check_cancelled()
    path = Path(path)
    digest = hashlib.new(algorithm) if algorithm else None
    with urlopen(Request(url,headers={'User-Agent':USER_AGENT, **(headers or {})}),timeout=90) as r, path.open('wb') as out:
        total=0
        while True:
            check_cancelled()
            data=r.read(1024*1024)
            if not data: break
            total+=len(data)
            if total>limit: raise ValueError('Download exceeds the size limit.')
            out.write(data)
            if digest: digest.update(data)
    if digest and digest.hexdigest().lower()!=checksum.lower():
        path.unlink(missing_ok=True)
        raise ValueError('Download checksum did not match; retry setup.')


def get_java(major,log,image="jre"):
    if os.name!='nt' or platform.machine().lower() not in ('amd64','x86_64'):
        raise ValueError('Automatic Java setup currently supports Windows x64 PCs.')
    runtime = CACHE/'runtime'/(str(major) if image=='jre' else str(major)+'-'+image)
    exes = list(runtime.glob('*/bin/java.exe'))
    if exes: return exes[0]
    log(f'Downloading portable Java {major} from Eclipse Adoptium...')
    assets=get_json(f'https://api.adoptium.net/v3/assets/latest/{major}/hotspot?architecture=x64&image_type={image}&os=windows&vendor=eclipse')
    if not assets: raise ValueError(f'No Windows Java {major} runtime available.')
    pkg=assets[0]['binary']['package']
    runtime.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime.parent) as tmp:
        tmp=Path(tmp); archive=tmp/'java.zip'; extract=tmp/'runtime';extract.mkdir()
        download(pkg['link'],archive,'sha256',pkg['checksum'])
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>2*1024**3: raise ValueError('Java archive too large.')
            for i in z.infolist():
                name=i.filename.replace('\\','/')
                if name.startswith('/') or any(p=='..' or ':' in p for p in name.split('/')):
                    raise ValueError('Unsafe Java archive path.')
            z.extractall(extract)
        exes=list(extract.glob('*/bin/java.exe'))
        if len(exes)!=1: raise ValueError('Java archive has an unexpected layout.')
        if runtime.exists(): shutil.rmtree(runtime)
        extract.rename(runtime)
    return next(runtime.glob('*/bin/java.exe'))

