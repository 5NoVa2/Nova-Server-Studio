"""One owned, portable playit agent; credentials never enter game folders/logs."""
import hashlib,json,os,re,subprocess,threading
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,HTTPRedirectHandler,build_opener
from connection_settings import host,port
from process_manager import managed_popen,start_worker

WINDOWS=os.name=='nt'
VERSION='0.17.1'
ASSET='playit-windows-x86_64-signed.exe'
URL=f'https://github.com/playit-cloud/playit-agent/releases/download/v{VERSION}/{ASSET}'
SHA256='9b00d6ff7d37d1052e5ae097e1348e11deae8617cd7a8ba39d1777f2006316a3'
CLAIM=re.compile(r'https://playit\.gg/claim/[a-fA-F0-9]{10}(?![a-zA-Z0-9/])')
ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
RUN_DATA_URL='https://api.playit.gg/v1/agents/rundata'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def assigned_tunnels(secret_path):
    # The portable agent logs only the FIRST line of each screen in --stdout
    # mode. Read its assigned tunnels through the same official read-only API.
    # Never expose credentials, response bodies or request exceptions in logs.
    with Path(secret_path).open(encoding='utf-8') as file:config=file.read(65537)
    if len(config)>65536:raise ValueError('Invalid agent configuration')
    match=re.search(r'^\s*secret_key\s*=\s*[\"\']([a-fA-F0-9]+)[\"\']\s*$',config,re.M)
    secret=match.group(1) if match else config.strip()
    if not re.fullmatch(r'(?:[a-fA-F0-9]{2})+',secret):raise ValueError('Agent authorization pending')
    request=Request(RUN_DATA_URL,data=b'{}',headers={'Authorization':'Agent-Key '+secret,'Content-Type':'application/json'},method='POST')
    with build_opener(NoRedirect()).open(request,timeout=10) as response:raw=response.read(1024*1024+1)
    if len(raw)>1024*1024:raise ValueError('Invalid tunnel response')
    result=json.loads(raw)
    if result.get('status')!='success':raise ValueError('Tunnel lookup unavailable')
    tunnels=result['data']['tunnels']
    if not isinstance(tunnels,list):raise ValueError('Invalid tunnel response')
    routes={};ambiguous=set()
    for tunnel in tunnels:
        try:
            if tunnel.get('disabled_reason') is not None or tunnel.get('tunnel_type')=='https':continue
            fields={field['name']:field['value'] for field in tunnel['agent_config']['fields']}
            public=tunnel['display_address'];public_endpoint=endpoint(public)
            local_port=port(fields.get('local_port') or (public_endpoint[1] if public_endpoint else ''))
            local_ip=fields.get('local_ip','127.0.0.1')
            if local_ip=='::1':local_ip='[::1]'
            row=mapping(f'{public} => {local_ip}:{local_port}')
            if row:
                if row[0] in routes:ambiguous.add(row[0])
                routes[row[0]]=row[1]
        except (ValueError,TypeError,KeyError,AttributeError):continue
    return {key:value for key,value in routes.items() if key not in ambiguous}

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
        self.claim='';self.connected=False;self.prepared=verified(paths(self.cache)[1]);self.status='Not started';self.lock=threading.RLock();self.generation=0;self.lookup_stop=threading.Event()
    def poll(self):return self.process.poll() if self.process is not None else 0
    def snapshot(self):
        with self.lock:return dict(playitRunning=self.poll() is None,playitReady=self.prepared,playitStatus=self.status,playitClaimUrl=self.claim,playitMappings={str(k):{'host':v[0],'port':v[1]} for k,v in self.mappings.items()})
    def start(self):
        with self.lock:
            if self.poll() is None:return
            root,exe,secret=paths(self.cache)
            if not verified(exe):raise ValueError('Choose Prepare playit first to download and verify the official agent.')
            from private_files import protect_agent_directory
            protect_agent_directory(secret.parent)
            env=dict(os.environ)
            for key in ('PLAYIT_SECRET','PLAYIT_SECRET_PATH','API_BASE','PLAYIT_LOG'):env.pop(key,None)
            env['PLAYIT_LOG']='info'
            self.generation+=1;generation=self.generation;self.leases={};self.claim='';self.mappings={};self.connected=False
            self.lookup_stop.set();self.lookup_stop=threading.Event();lookup_stop=self.lookup_stop
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
        def refresh():
            while not lookup_stop.is_set():
                self.refresh_addresses(generation)
                if lookup_stop.wait(3):return
        start_worker(read);start_worker(refresh)
    def refresh_addresses(self,generation):
        with self.lock:
            if generation!=self.generation or self.poll() is not None:return
        try:routes=assigned_tunnels(paths(self.cache)[2])
        except Exception:
            # Exceptions may contain request/credential data: deliberately omit.
            routes={}
        with self.lock:
            if generation!=self.generation or self.poll() is not None:return
            self.mappings=routes;self.notify()
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
            self.lookup_stop.set();self.generation+=1;proc=self.process;self.process=None;self.leases={};self.connected=False;self.mappings={};self.claim='';self.status='Stopped'
            if proc is not None and proc.poll() is None:proc.terminate()
            self.notify()
    def address(self,local_port):
        with self.lock:return self.mappings.get(local_port)
    def tunnel_status(self,local_port):
        if self.poll() is not None:return 'Disconnected'
        if self.claim:return 'Needs playit approval'
        return 'Connected' if self.connected and self.address(local_port) else 'Agent running · configure tunnel'
