"""One owned, portable playit agent; credentials never enter game folders/logs."""
import hashlib,os,re,subprocess,threading
from pathlib import Path
from urllib.parse import urlparse
from connection_settings import host,port
from process_manager import managed_popen,start_worker

WINDOWS=os.name=='nt'
VERSION='0.17.1'
ASSET='playit-windows-x86_64-signed.exe'
URL=f'https://github.com/playit-cloud/playit-agent/releases/download/v{VERSION}/{ASSET}'
SHA256='9b00d6ff7d37d1052e5ae097e1348e11deae8617cd7a8ba39d1777f2006316a3'
CLAIM=re.compile(r'https://playit\.gg/claim/[a-fA-F0-9]{10}(?![a-zA-Z0-9/])')
ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def endpoint(value):
    value=value.strip()
    if value.startswith('['):
        address,sep,number=value[1:].partition(']:')
    else:address,sep,number=value.rpartition(':')
    if not sep:return None
    try:return host(address),port(number)
    except (ValueError,UnicodeError):return None

def mapping(line):
    public,sep,local=line.partition(' => ')
    if not sep or local.startswith('(disabled'):return None
    target=endpoint(local);source=endpoint(public)
    if source is None and ':' not in public:
        try:source=(host(public),None)
        except (ValueError,UnicodeError):return None
    if not source or not target or target[0] not in ('127.0.0.1','localhost','::1'):return None
    return target[1],source

def claim_url(value):
    match=CLAIM.fullmatch(value)
    return value if match else ''

def paths(cache):
    root=Path(cache)/'playit';return root,root/'agent'/VERSION/'playit.exe',root/'account'/'playit.toml'

def verified(executable):
    try:return hashlib.sha256(Path(executable).read_bytes()).hexdigest()==SHA256
    except OSError:return False

_prepare_lock=threading.Lock()

def prepare(cache,log):
    with _prepare_lock:return _prepare(cache,log)

def _prepare(cache,log):
    if not WINDOWS:raise ValueError('The managed playit agent currently supports Windows x64.')
    root,exe,secret=paths(cache)
    if verified(exe):return str(exe)
    from runtime import download
    exe.parent.mkdir(parents=True,exist_ok=True)
    part=exe.with_suffix('.download')
    try:
        log('Downloading the official portable playit.gg agent…')
        download(URL,part,'sha256',SHA256,limit=20*1024**2)
        if part.read_bytes()[:2]!=b'MZ':raise ValueError('playit download is not a Windows executable.')
        os.replace(part,exe)
    finally:part.unlink(missing_ok=True)
    log('playit agent verified and ready.');return str(exe)

class PlayitLease:
    def __init__(self,manager,profile):self.manager=manager;self.profile=profile;self.released=False;self.generation=manager.generation
    def poll(self):return 0 if self.released or self.generation!=self.manager.generation else self.manager.poll()
    def terminate(self):
        if self.released:return
        self.released=True
        if self.generation==self.manager.generation:self.manager.release(self.profile)

class PlayitManager:
    def __init__(self,cache,notify):
        self.cache=Path(cache);self.notify=notify;self.process=None;self.leases={};self.mappings={}
        self.claim='';self.connected=False;self.prepared=verified(paths(self.cache)[1]);self.status='Not started';self.lock=threading.RLock();self.generation=0
    def poll(self):return self.process.poll() if self.process is not None else 0
    def snapshot(self):
        with self.lock:return dict(playitRunning=self.poll() is None,playitReady=self.prepared,playitStatus=self.status,playitClaimUrl=self.claim,playitMappings={str(k):{'host':v[0],'port':v[1]} for k,v in self.mappings.items()})
    def start(self):
        with self.lock:
            if self.poll() is None:return
            root,exe,secret=paths(self.cache)
            if not verified(exe):raise ValueError('Choose Prepare playit first to download and verify the official agent.')
            secret.parent.mkdir(parents=True,exist_ok=True)
            if os.name!='nt':secret.parent.chmod(0o700)
            env=dict(os.environ)
            for key in ('PLAYIT_SECRET','PLAYIT_SECRET_PATH','API_BASE','PLAYIT_LOG'):env.pop(key,None)
            env['PLAYIT_LOG']='info'
            self.generation+=1;generation=self.generation;self.leases={};self.claim='';self.mappings={};self.connected=False
            self.process=managed_popen([str(exe),'--secret_path',str(secret),'--stdout','start'],cwd=secret.parent,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            proc=self.process;self.status='Starting agent / waiting for authorization';self.notify()
        def read():
            try:
                for raw in proc.stdout:
                    with self.lock:
                        if generation!=self.generation:return
                        self.consume(raw[:16384])
                with self.lock:
                    if generation==self.generation:
                        self.connected=False;self.claim='';self.mappings={};self.status='Agent stopped. Check setup or re-claim if access was revoked.';self.notify()
            finally:
                if proc.stdout:proc.stdout.close()
        start_worker(read)
    def consume(self,raw):
        # Never forward raw output: it can contain guest-login tokens or secrets.
        line=ANSI.sub('',raw).strip();match=CLAIM.search(line)
        if match:
            self.claim=match.group();self.status='Approve this agent in your browser';self.notify();return
        if any(word in line.lower() for word in ('failed','disconnected','reconnecting')):
            self.connected=False;self.mappings={};self.status='Agent connection issue. Check network access or restart setup.'
        if 'tunnel running' in line:
            self.connected=True;self.claim='';self.status='Agent online. Configure each game tunnel in playit.gg.'
        if line=='TUNNELS':self.mappings={}
        row=mapping(line)
        if row:self.mappings[row[0]]=row[1]
        if 'invalid secret' in line.lower() or 'program rejected' in line.lower():self.status='Authorization failed. Stop agent and re-claim it in playit.gg.'
        self.notify()
    def acquire(self,profile,local_port):
        with self.lock:
            for other,other_port in self.leases.items():
                if other!=profile and other_port==local_port:raise ValueError('Use a different local game port for each playit profile so Saturn can identify its public address.')
            self.start();self.leases[profile]=local_port
            return PlayitLease(self,profile)
    def release(self,profile):
        with self.lock:
            self.leases.pop(profile,None)
            if not self.leases:self.stop()
    def stop(self):
        with self.lock:
            self.generation+=1;proc=self.process;self.process=None;self.leases={};self.connected=False;self.mappings={};self.claim='';self.status='Stopped'
            if proc is not None and proc.poll() is None:proc.terminate()
            self.notify()
    def address(self,local_port):
        with self.lock:return self.mappings.get(local_port)
    def tunnel_status(self,local_port):
        if self.poll() is not None:return 'Disconnected'
        if self.claim:return 'Needs playit approval'
        return 'Connected' if self.connected and self.address(local_port) else 'Agent running · configure tunnel'
