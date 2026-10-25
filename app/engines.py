"""Official server installers; prepare fully before replacing the old folder."""
from process_manager import managed_popen,check_cancelled,copy_file
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler
import runtime as net
from app import install, validate_server_folder

KINDS=('Vanilla','Paper','Spigot','Forge','CurseForge','Bedrock')


def available_versions(kind):
    if kind=='Bedrock':
        from bedrock import latest_download
        return [latest_download()[0]]
    if kind=='Paper':
        groups=net.get_json('https://fill.papermc.io/v3/projects/paper')['versions']
        return [v for group in groups.values() for v in group]
    if kind=='Forge':
        # Promotions only include recommended builds, omitting many versions.
        from urllib.request import urlopen
        import xml.etree.ElementTree as ET
        with urlopen('https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml',timeout=60) as response:
            data=response.read(8*1024**2)
        versions=set(v.text.split('-',1)[0] for v in ET.fromstring(data).findall('./versioning/versions/version') if v.text and re.fullmatch(r'\d+(?:\.\d+)+',v.text.split('-',1)[0]))
        return sorted(versions,key=lambda v:tuple(int(x) for x in v.split('.')),reverse=True)
    versions=net.get_json(net.MANIFEST)['versions']
    return [v['id'] for v in versions if kind=='Vanilla' or v['type']=='release']


def metadata(version):
    manifest=net.get_json(net.MANIFEST)
    if version.strip().lower()=='latest':version=manifest['latest']['release']
    entry=next((v for v in manifest['versions'] if v['id']==version),None)
    if not entry:raise ValueError('Choose a listed Minecraft version or latest.')
    return version,net.get_json(entry['url'])


def safe_extract(archive,dest):
    dest=Path(dest).resolve();dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist())>30*1024**3:raise ValueError('Pack expands beyond 30 GB.')
        for i in z.infolist():
            name=i.filename.replace('\\','/')
            parts=name.split('/')
            if name.startswith('/') or stat.S_ISLNK(i.external_attr>>16) or any(p=='..' or ':' in p or p.endswith((' ','.')) for p in parts if p):
                raise ValueError('Unsafe archive entry: '+i.filename)
            out=dest.joinpath(*parts).resolve()
            if out!=dest and dest not in out.parents:raise ValueError('Unsafe archive path.')
        for member in z.infolist():
            check_cancelled();z.extract(member,dest)
    entries=list(dest.iterdir())
    while len(entries)==1 and entries[0].is_dir():
        dest=entries[0];entries=list(dest.iterdir())
    return dest


def run_java(java,args,cwd,log):
    env=os.environ.copy();env['JAVA_HOME']=str(Path(java).parent.parent)
    env['PATH']=str(Path(java).parent)+os.pathsep+env.get('PATH','')
    log('Running official installer/build tool. This may take several minutes...')
    with managed_popen([str(java),*args],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)) as proc:
        for line in proc.stdout:log(line.rstrip())
        code=proc.wait()
    if code:raise ValueError('Installer/build tool exited with code '+str(code)+'. Existing server was not replaced.')


def loader_args(folder,loader,mc,java,log):
    if loader.startswith('forge-'):
        build=loader[len('forge-'):]
        # Old releases can carry a Minecraft version prefix and/or suffix.
        full=build if build.startswith(mc+'-') else mc+'-'+build
        if not re.fullmatch(r'[A-Za-z0-9._-]+',full):raise ValueError('Invalid Forge version.')
        url=f'https://maven.minecraftforge.net/net/minecraftforge/forge/{full}/forge-{full}-installer.jar'
        jar=folder/'nova-forge-installer.jar';net.download(url,jar)
        run_java(java,['-jar',jar.name,'--installServer'],folder,log)
        modern=folder/'libraries'/'net'/'minecraftforge'/'forge'/full/'win_args.txt'
        if modern.exists():return ['@'+modern.relative_to(folder).as_posix(),'nogui']
        jars=[p for p in folder.glob('forge-*.jar') if 'installer' not in p.name]
        if len(jars)!=1:raise ValueError('Forge install finished without a recognized server launcher.')
        return ['-jar',jars[0].name,'nogui']
    if loader.startswith('neoforge-'):
        build=loader[len('neoforge-'):]
        if not re.fullmatch(r'[A-Za-z0-9._-]+',build):raise ValueError('Invalid NeoForge version.')
        jar=folder/'nova-neoforge-installer.jar'
        net.download(f'https://maven.neoforged.net/releases/net/neoforged/neoforge/{build}/neoforge-{build}-installer.jar',jar)
        run_java(java,['-jar',jar.name,'--installServer'],folder,log)
        path=folder/'libraries'/'net'/'neoforged'/'neoforge'/build/'win_args.txt'
        if not path.exists():raise ValueError('NeoForge launcher not found after installation.')
        return ['@'+path.relative_to(folder).as_posix(),'nogui']
    if loader.startswith('fabric-'):
        build=loader[len('fabric-'):]
        installer=next(i['version'] for i in net.get_json('https://meta.fabricmc.net/v2/versions/installer') if i.get('stable'))
        net.download(f'https://meta.fabricmc.net/v2/versions/loader/{mc}/{build}/{installer}/server/jar',folder/'server.jar')
        return ['-jar','server.jar','nogui']
    raise ValueError('Unsupported pack loader: '+loader+'. Supported: Forge, NeoForge, Fabric.')


class CurseAPI:
    def __init__(self,key):
        if not key.strip():raise ValueError('Enter a CurseForge API key to browse and download packs. You can also use Downloads / ZIP without API browsing.')
        self.key=key.strip()
    def get(self,path):
        try:return net.get_json('https://api.curseforge.com/v1/'+path,headers={'x-api-key':self.key})
        except HTTPError as e:
            if e.code in (401,403):raise ValueError('CurseForge rejected the API key or this download is restricted.') from None
            raise
    def search(self,query,index=0,sort=2,game_version=''):
        params={'gameId':432,'classId':4471,'searchFilter':query,'sortField':sort,'sortOrder':'desc','pageSize':20,'index':index}
        if game_version:params['gameVersion']=game_version
        return self.get('mods/search?'+urlencode(params))
    def mods(self,ids):
        check_cancelled()
        request=Request('https://api.curseforge.com/v1/mods',data=json.dumps({'modIds':[int(i) for i in ids]}).encode(),headers={'User-Agent':net.USER_AGENT,'x-api-key':self.key,'Content-Type':'application/json'},method='POST')
        with net.urlopen(request,timeout=60) as response:result=json.load(response)
        check_cancelled()
        return result['data']
    def files(self,project,index=0):return self.get(f'mods/{int(project)}/files?pageSize=50&index={int(index)}')
    def file(self,project,file):return self.get(f'mods/{int(project)}/files/{int(file)}')['data']
    def download(self,project,file,path):
        meta=self.file(project,file)
        url=meta.get('downloadUrl') or self.get(f'mods/{int(project)}/files/{int(file)}/download-url')['data']
        if not url:raise ValueError('Author has disabled API downloads. Download the server pack through its CurseForge page instead.')
        host=urlparse(url).hostname or ''
        if urlparse(url).scheme!='https' or not host.endswith('.forgecdn.net'):
            raise ValueError('CurseForge returned an unrecognized download host; use the pack website.')
        # Never forward the API key to another domain on CDN redirects.
        class Redirect(HTTPRedirectHandler):
            def redirect_request(self,req,fp,code,msg,headers,newurl):
                result=super().redirect_request(req,fp,code,msg,headers,newurl)
                newhost=urlparse(newurl).hostname or ''
                if urlparse(newurl).scheme!='https':raise ValueError('Refusing an insecure CDN redirect.')
                if not newhost.endswith('.forgecdn.net'):
                    result.remove_header('X-api-key')
                return result
        hashes={h['algo']:h['value'] for h in meta.get('hashes',[])}
        import hashlib
        algo='sha1' if 1 in hashes else 'md5' if 2 in hashes else None
        if not algo:raise ValueError('No checksum provided for this CurseForge file.')
        digest=hashlib.new(algo);count=0
        request=Request(url,headers={'User-Agent':net.USER_AGENT,'x-api-key':self.key})
        with build_opener(Redirect()).open(request,timeout=90) as response,Path(path).open('wb') as output:
            while True:
                check_cancelled()
                chunk=response.read(1024*1024)
                if not chunk:break
                count+=len(chunk)
                if count>10*1024**3:raise ValueError('Pack exceeds 10 GB.')
                output.write(chunk);digest.update(chunk)
        if digest.hexdigest().lower()!=hashes[1 if algo=='sha1' else 2].lower():
            Path(path).unlink(missing_ok=True);raise ValueError('CurseForge pack checksum mismatch.')
        return meta


def prepare_curse(folder,selection,api,ram,log):
    project=int(selection['project_id']);file=int(selection['file_id'])
    meta=api.file(project,file);serverid=meta.get('serverPackFileId')
    if not serverid:raise ValueError('This release has no published server pack. Choose a release with Server pack: Yes.')
    log('Downloading CurseForge release manifest and published server pack...')
    client=folder.parent/'client.zip';api.download(project,file,client)
    with zipfile.ZipFile(client) as z:
        if 'manifest.json' not in z.namelist():raise ValueError('Release ZIP has no CurseForge manifest. Use Downloads / ZIP for this pack.')
        if z.getinfo('manifest.json').file_size>2*1024**2:raise ValueError('Manifest too large.')
        manifest=json.loads(z.read('manifest.json'))
    mc=manifest['minecraft']['version']
    loader=next((i['id'] for i in manifest['minecraft']['modLoaders'] if i.get('primary')),None)
    if not loader:raise ValueError('Pack has no primary loader in its manifest.')
    mc,vm=metadata(mc);java=net.get_java(vm.get('javaVersion',{}).get('majorVersion',8),log)
    server=folder.parent/'serverpack.zip';api.download(project,serverid,server)
    extracted=safe_extract(server,folder.parent/'unpacked')
    shutil.copytree(extracted,folder,dirs_exist_ok=True,copy_function=copy_file)
    # Some published server packs are manifest exports rather than bundled mods.
    pack_manifest=folder/'manifest.json'
    if pack_manifest.exists():
        exported=json.loads(pack_manifest.read_text(encoding='utf-8'))
        files=exported.get('files',[])
        mods=folder/'mods';mods.mkdir(exist_ok=True)
        for index,item in enumerate(files):
            modmeta=api.file(item['projectID'],item['fileID'])
            filename=modmeta['fileName']
            if Path(filename).name!=filename or '\\' in filename or ':' in filename:raise ValueError('Unsafe mod filename.')
            log(f'Downloading server mod {index+1}/{len(files)}: {filename}')
            api.download(item['projectID'],item['fileID'],mods/filename)
        overrides=folder/exported.get('overrides','overrides')
        if folder.resolve() not in overrides.resolve().parents:raise ValueError('Unsafe overrides path.')
        if overrides.is_dir():shutil.copytree(overrides,folder,dirs_exist_ok=True,copy_function=copy_file)
    if not (folder/'mods').is_dir() or not any((folder/'mods').glob('*.jar')):
        raise ValueError('Server pack needs its own bootstrap installer and has no ready mods folder. Existing server left untouched. Use its published setup instructions through Downloads / ZIP.')
    args=loader_args(folder,loader,mc,java,log)
    return mc,java,args,{'pack':selection['name'],'loader':loader}


def setup_engine(kind,target,version,loader,ram,log,selection=None,key=''):
    if kind not in KINDS:raise ValueError('Unknown server type.')
    if kind=='Bedrock':
        from bedrock import setup
        return setup(target,version,log)
    target=validate_server_folder(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.nova-install-',dir=target.parent) as td:
        temp=Path(td);folder=temp/'server';folder.mkdir()
        extra={}
        if kind=='CurseForge':
            if not selection:raise ValueError('Browse CurseForge and choose a pack release first.')
            version,java,args,extra=prepare_curse(folder,selection,CurseAPI(key),ram,log)
        else:
            if kind=='Paper' and version.strip().lower()=='latest':
                versions=net.get_json('https://fill.papermc.io/v3/projects/paper')['versions']
                choices=[v for values in versions.values() for v in values]
                version=None
                for candidate in choices:
                    builds=net.get_json(f'https://fill.papermc.io/v3/projects/paper/versions/{candidate}/builds')
                    if any(i.get('channel')=='STABLE' for i in builds):version=candidate;break
                if version is None:raise ValueError('No stable Paper builds available.')
            version,vm=metadata(version)
            major=vm.get('javaVersion',{}).get('majorVersion',8)
            # Spigot compilation requires a JDK, not just a Java runtime.
            java=net.get_java(major,log,image='jdk' if kind=='Spigot' else 'jre')
            args=['-jar','server.jar','nogui']
            if kind=='Vanilla':
                jar=vm.get('downloads',{}).get('server')
                if not jar:raise ValueError('Mojang does not provide a dedicated server download for this historical version. Choose another version.')
                net.download(jar['url'],folder/'server.jar','sha1',jar['sha1'])
            elif kind=='Paper':
                builds=net.get_json(f'https://fill.papermc.io/v3/projects/paper/versions/{version}/builds')
                stable=next((b for b in builds if b.get('channel')=='STABLE'),None)
                if not stable:raise ValueError('No stable Paper build for '+version+'. Select another version.')
                jar=stable['downloads']['server:default'];checksum=jar.get('checksums',{}).get('sha256')
                if not checksum:raise ValueError('Paper API did not return a SHA-256 checksum.')
                net.download(jar['url'],folder/'server.jar','sha256',checksum);extra['build']=stable['id']
            elif kind=='Spigot':
                log('Downloading official Spigot BuildTools. Building may take a while.')
                net.download('https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar',folder/'BuildTools.jar')
                run_java(java,['-jar','BuildTools.jar','--rev',version,'--compile','SPIGOT'],folder,log)
                jars=list(folder.glob('spigot-*.jar'))
                if len(jars)!=1:raise ValueError('BuildTools did not produce a unique Spigot server JAR.')
                # Build workspaces are not required at runtime.
                shutil.copy2(jars[0],temp/'finished.jar')
                shutil.rmtree(folder);folder.mkdir();shutil.move(temp/'finished.jar',folder/'server.jar')
            elif kind=='Forge':
                if not loader.strip() or loader.strip().lower() in ('latest','recommended'):
                    promos=net.get_json('https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json')['promos']
                    build=promos.get(version+'-recommended') or promos.get(version+'-latest')
                    if not build:raise ValueError('No Forge release for '+version+'. Choose an explicit Minecraft version, such as 1.20.1.')
                else:build=loader.strip()
                args=loader_args(folder,'forge-'+build,version,java,log);extra['loader']='forge-'+build
        (folder/'eula.txt').write_text('eula=true\n',encoding='utf-8')
        # Preserve pack properties but enforce the tunnel endpoint and online auth.
        props=folder/'server.properties'
        original=props.read_text(encoding='utf-8',errors='replace') if props.exists() else ''
        overrides={'server-ip':'127.0.0.1','server-port':'25565','online-mode':'true','enable-query':'false','enable-rcon':'false'}
        lines=[line for line in original.splitlines() if line.split('=',1)[0].strip() not in overrides]
        props.write_text('\n'.join(lines+[k+'='+v for k,v in overrides.items()])+'\n',encoding='utf-8')
        state={'version':version,'java':str(java),'ram':int(ram),'engine':kind,'args':args,**extra}
        (folder/'switcher-server.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
        command=[str(java),'-Xms1G',f'-Xmx{ram}G',*args]
        (folder/'Start-Server.bat').write_text('@echo off\ncd /d "%~dp0"\n'+subprocess.list2cmdline(command)+'\npause\n',encoding='utf-8')
        archive=temp/'ready.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
            for path in folder.rglob('*'):
                if path.is_file():z.write(path,path.relative_to(folder))
        log('Installation prepared. Replacing the server folder without automatic backup...')
        install(archive,target)
    log(f'{kind} {version} installed. Use Start server, then Start tunnel.')
    return state
