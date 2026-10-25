"""Server configuration and add-on file operations, with conflict detection."""
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from app import validate_server_folder

LOCKED={'server-ip':'127.0.0.1','server-port':'25565','online-mode':'true','enable-rcon':'false','enable-query':'false'}
BEDROCK_LOCKED={'server-port':'19132','server-portv6':'19133','online-mode':'true','enable-lan-visibility':'false'}
EXTENSIONS={'.json','.toml','.yml','.yaml','.properties','.txt','.cfg','.conf','.ini','.xml','.snbt','.mcmeta'}
ROOT_FILES={'server.properties','spigot.yml','bukkit.yml','paper.yml','permissions.yml','commands.yml','whitelist.json','ops.json','banned-players.json','banned-ips.json','allowlist.json','permissions.json'}


def fingerprint(data):return hashlib.sha256(data).hexdigest() if data is not None else None


def atomic_write(path,data,expected):
    path=Path(path)
    current=path.read_bytes() if path.exists() else None
    if fingerprint(current)!=expected:raise ValueError('File changed since it was opened. Reload it before saving.')
    path.parent.mkdir(parents=True,exist_ok=True)
    name=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.nova-save-',delete=False) as f:
            name=f.name;f.write(data);f.flush();os.fsync(f.fileno())
        if path.exists():shutil.copymode(path,name)
        current=path.read_bytes() if path.exists() else None
        if fingerprint(current)!=expected:raise ValueError('File changed while saving. Reload it before saving.')
        os.replace(name,path)
    finally:
        if name:Path(name).unlink(missing_ok=True)


def unescape(value):
    def replacement(match):
        token=match.group(1)
        if token.startswith('u'):
            try:return chr(int(token[1:],16))
            except ValueError:return token
        return {'t':'\t','r':'\r','n':'\n','f':'\f'}.get(token,token)
    result=re.sub(r'\\(u[0-9a-fA-F]{4}|.)',replacement,value)
    try:return result.encode('utf-16-le','surrogatepass').decode('utf-16-le')
    except UnicodeError:return result


def escape(value):
    result=''
    for i,char in enumerate(str(value)):
        if char in '\\:=#!' or (char==' ' and i==0):result+='\\'+char
        elif char in '\n\r\t\f':result+='\\'+{'\n':'n','\r':'r','\t':'t','\f':'f'}[char]
        elif ord(char)<32 or ord(char)>126:
            units=char.encode('utf-16-be')
            result+=''.join('\\u'+units[j:j+2].hex() for j in range(0,len(units),2))
        else:result+=char
    return result


def records(text):
    pending=[];logical=''
    for line in text.splitlines(keepends=True):
        stripped=line.rstrip('\r\n')
        if not pending and stripped.lstrip(' \t\f').startswith(('#','!')):
            yield line,stripped;continue
        logical+=stripped.lstrip(' \t\f') if pending else stripped
        pending.append(line)
        trailing=len(logical)-len(logical.rstrip('\\'))
        if trailing%2:logical=logical[:-1];continue
        yield ''.join(pending),logical
        pending=[];logical=''
    if pending:yield ''.join(pending),logical


def parse_record(line):
    line=line.lstrip(' \t\f')
    if not line or line[0] in '#!':return None
    escaped=False;end=len(line)
    for i,c in enumerate(line):
        if escaped:escaped=False;continue
        if c=='\\':escaped=True;continue
        if c in '=:\t \f':end=i;break
    pos=end
    while pos<len(line) and line[pos] in ' \t\f':pos+=1
    if pos<len(line) and line[pos] in '=:':pos+=1
    while pos<len(line) and line[pos] in ' \t\f':pos+=1
    return unescape(line[:end]),unescape(line[pos:])


class Properties:
    def __init__(self,path):
        self.path=Path(path)
        try:self.bedrock=json.loads((self.path.parent/'switcher-server.json').read_text()).get('engine')=='Bedrock'
        except (OSError,ValueError):self.bedrock=False
        try:
            state=json.loads((self.path.parent/'switcher-server.json').read_text());self.network=state.get('nova_ports',{})
        except (OSError,ValueError):self.network={}
        self.original=self.path.read_bytes() if self.path.exists() else None
        self.encoding='utf-8'
        try:self.text=(self.original or b'').decode('utf-8')
        except UnicodeDecodeError:self.encoding='latin-1';self.text=(self.original or b'').decode('latin-1')
        self.values={}
        for raw,line in self.iter_records():
            parsed=self.parse(line)
            if parsed:self.values[parsed[0]]=parsed[1]
    def iter_records(self):
        if not self.bedrock:return records(self.text)
        return ((line,line.rstrip('\r\n')) for line in self.text.splitlines(keepends=True))
    def parse(self,line):
        if not self.bedrock:return parse_record(line)
        if not line.strip() or line.lstrip().startswith('#'):return None
        key,sep,value=line.partition('=')
        return (key.strip(),value) if sep else None
    def pair(self,key,value):
        if not self.bedrock:return escape(key)+'='+escape(value)+'\n'
        if any(c in key+value for c in '\r\n'):raise ValueError('Bedrock property values must fit on one line.')
        return key+'='+value+'\n'
    def save(self,updates):
        updates={str(k):str(v) for k,v in updates.items()};
        locked=dict(BEDROCK_LOCKED if self.bedrock else LOCKED)
        from connection_settings import port
        if self.bedrock:
            locked['server-port']=str(port(self.network.get('local_bedrock_port',19132)))
            locked['server-portv6']=str(port(self.network.get('bedrock_ipv6_port',19133)))
        else:locked['server-port']=str(port(self.network.get('local_java_port',25565)))
        updates.update(locked)
        output=[];seen=set()
        for raw,line in self.iter_records():
            parsed=self.parse(line)
            if parsed and parsed[0] in updates:
                key=parsed[0]
                if key not in seen:output.append(self.pair(key,updates[key]));seen.add(key)
            else:output.append(raw)
        if output and not output[-1].endswith(('\n','\r')):output.append('\n')
        for key,value in updates.items():
            if key not in seen:output.append(self.pair(key,value))
        atomic_write(self.path,''.join(output).encode(self.encoding),fingerprint(self.original))
        self.__init__(self.path)


class ServerFiles:
    def __init__(self,folder):
        self.root=validate_server_folder(folder)
        if not self.root.is_dir():raise ValueError('Choose an installed server folder first.')
        try:self.state=json.loads((self.root/'switcher-server.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):self.state={}
    def path(self,relative):
        source=self.root/relative
        path=source.resolve()
        if path==self.root or self.root not in path.parents:raise ValueError('Path is outside the server folder.')
        for item in [source,*source.parents]:
            if item==self.root:break
            if item.is_symlink() or (item.exists() and getattr(item.stat(follow_symlinks=False),'st_file_attributes',0)&1024):
                raise ValueError('Symbolic links and junctions cannot be edited.')
        return path
    def config_files(self):
        # Only core server files; never traverse mod/plugin/world config trees.
        names=set(ROOT_FILES)
        names.update({'config/paper-global.yml','config/paper-world-defaults.yml'})
        paths=[]
        for name in names:
            try:path=self.path(name)
            except ValueError:continue
            if path.is_file():paths.append(name)
        return sorted(paths)
    def read_config(self,relative):
        path=self.path(relative)
        if relative not in self.config_files():raise ValueError('Choose a listed server configuration file.')
        if path.stat().st_size>2*1024**2:raise ValueError('Editor limit is 2 MB. Use an external editor for this file.')
        raw=path.read_bytes()
        try:text=raw.decode('utf-8');encoding='utf-8'
        except UnicodeDecodeError:text=raw.decode('latin-1');encoding='latin-1'
        return text,fingerprint(raw),encoding
    def write_config(self,relative,text,expected,encoding='utf-8'):
        path=self.path(relative)
        if relative not in self.config_files():raise ValueError('Choose a listed server configuration file.')
        if path.suffix.lower()=='.json':json.loads(text)
        if path.suffix.lower()=='.toml':
            try:import tomllib
            except ImportError:pass
            else:tomllib.loads(text)
        if relative=='server.properties':
            doc=Properties(path)
            if fingerprint(doc.original)!=expected:raise ValueError('File changed. Reload before saving.')
            # Parse the edited text, then reapply the tunnel's connection settings.
            edited=Properties(path);edited.text=text
            edited.original=doc.original;edited.encoding=encoding;edited.save({})
            return fingerprint(path.read_bytes())
        data=text.encode(encoding)
        if len(data)>2*1024**2:raise ValueError('Editor limit is 2 MB.')
        atomic_write(path,data,expected)
        return fingerprint(data)
    def addons(self,kind):
        if kind not in ('mods','plugins'):raise ValueError('Invalid add-on type.')
        folder=self.path(kind)
        if not folder.exists():return []
        return sorted([p.name for p in folder.iterdir() if p.is_file() and p.name.endswith(('.jar','.jar.disabled'))],key=str.lower)
    def add(self,kind,source,overwrite=False):
        source=Path(source)
        engine=self.state.get('engine','Vanilla')
        if kind=='plugins' and engine not in ('Paper','Spigot'):raise ValueError('Plugins require Paper or Spigot.')
        if kind=='mods' and engine not in ('Forge','CurseForge'):raise ValueError('Mods require a modded server such as Forge or a CurseForge pack.')
        if source.suffix.lower()!='.jar':raise ValueError('Select a .jar file.')
        if source.stat().st_size>512*1024**2:raise ValueError('JAR import limit is 512 MB.')
        with zipfile.ZipFile(source) as z:
            names=set(z.namelist())
            plugin='plugin.yml' in names or 'paper-plugin.yml' in names
            if kind=='plugins' and not plugin:raise ValueError('JAR has no plugin.yml or paper-plugin.yml.')
            if kind=='mods' and plugin:raise ValueError('This looks like a Bukkit/Paper plugin. Choose a matching mod JAR.')
        dest=self.path(kind+'/'+source.name)
        if source.resolve()==dest:return dest
        if dest.exists() and not overwrite:raise FileExistsError('A file with this name already exists.')
        # Read and copy atomically; no persistent automatic backup is created.
        atomic_write(dest,source.read_bytes(),fingerprint(dest.read_bytes()) if dest.exists() else None)
        return dest
    def toggle(self,kind,name):
        if name not in self.addons(kind):raise ValueError('Select a listed add-on.')
        source=self.path(kind+'/'+name)
        dest=source.with_name(name[:-9] if name.endswith('.disabled') else name+'.disabled')
        if dest.exists():raise FileExistsError('Enabled/disabled counterpart already exists.')
        source.rename(dest);return dest.name
    def remove(self,kind,name):
        if name not in self.addons(kind):raise ValueError('Select a listed add-on.')
        self.path(kind+'/'+name).unlink()
