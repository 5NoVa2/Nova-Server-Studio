"""Official Bedrock installer and UDP-over-SSH tunnel for the existing VPS."""
import base64
import json
import re
import select
import socket
import struct
import subprocess
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import runtime as net
from app import install,validate_server_folder

LINKS='https://net-secondary.web.minecraft-services.net/api/v1.0/download/links'
MAGIC=bytes.fromhex('00ffff00fefefefefdfdfdfd12345678')


def latest_download():
    links=net.get_json(LINKS)['result']['links']
    url=next(i['downloadUrl'] for i in links if i['downloadType']=='serverBedrockWindows')
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in ('www.minecraft.net','minecraft.net'):
        raise ValueError('Official Bedrock link has an unexpected host.')
    match=re.search(r'/bedrock-server-([0-9.]+)\.zip$',parsed.path)
    if not match:raise ValueError('Could not identify the official Bedrock release.')
    return match.group(1),url


def setup(target,version,log):
    target=validate_server_folder(target);target.parent.mkdir(parents=True,exist_ok=True)
    current,url=latest_download()
    if version.strip().lower() not in ('latest',current):
        raise ValueError('Only the current official Bedrock stable release is offered. Refresh versions and choose latest or '+current+'.')
    from engines import safe_extract
    with tempfile.TemporaryDirectory(prefix='.nova-bedrock-',dir=target.parent) as td:
        temp=Path(td);archive=temp/'bedrock.zip'
        log('Downloading official Bedrock Dedicated Server '+current+'...')
        net.download(url,archive)
        folder=safe_extract(archive,temp/'server')
        exe=folder/'bedrock_server.exe'
        if not exe.is_file():raise ValueError('Bedrock archive has no Windows server executable.')
        with exe.open('rb') as executable:
            if executable.read(2)!=b'MZ':raise ValueError('Invalid Windows Bedrock executable.')
        props=folder/'server.properties'
        original=props.read_text(encoding='utf-8') if props.exists() else ''
        values={'server-name':'Nova Bedrock','server-port':'19132','server-portv6':'19133','online-mode':'true','enable-lan-visibility':'false'}
        lines=[line for line in original.splitlines() if line.split('=',1)[0].strip() not in values]
        props.write_text('\n'.join(lines+[k+'='+v for k,v in values.items()])+'\n',encoding='utf-8')
        (folder/'eula.txt').write_text('eula=true\n',encoding='utf-8')
        state={'engine':'Bedrock','version':current,'executable':'bedrock_server.exe','port':19132,'protocol':'udp'}
        (folder/'switcher-server.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
        ready=temp/'ready.zip'
        with zipfile.ZipFile(ready,'w',zipfile.ZIP_STORED) as z:
            for p in folder.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(folder))
        install(ready,target)
    log('Bedrock '+current+' installed. Join using port 19132. Java RAM settings do not apply.')
    return state


def probe(host,port=19132,timeout=3):
    address=socket.gethostbyname(host)
    ping=b'\x01'+struct.pack('!q',int(time.time()*1000))+MAGIC+b'NOVAUDP1'
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
        udp.settimeout(timeout);udp.sendto(ping,(address,port));data,source=udp.recvfrom(65507)
    if source!=(address,port) or len(data)<35 or data[0]!=0x1c or data[17:33]!=MAGIC:
        raise ValueError('UDP response did not match a Bedrock status pong.')
    size=struct.unpack('!H',data[33:35])[0]
    return address,data[35:35+size].decode('utf-8',errors='replace')


class BedrockTunnel:
    MAX_FRAME=65513
    def __init__(self,client,log,local_port=19132,remote_port=19132):
        self.client=client;self.transport=client.get_transport();self.log=log
        self.stopped=threading.Event();self.lock=threading.Lock();self.send_lock=threading.Lock();self.sessions={};self.local_port=local_port
        self.channel=self.transport.open_session(timeout=20)
        # Execute our own relay in memory; no persistent VPS service is installed.
        source=(Path(__file__).parent/'udp_relay.py').read_bytes()
        encoded=base64.b64encode(source).decode()
        command="python3 -u -c \"import base64;exec(base64.b64decode('"+encoded+"'))\" "+str(int(remote_port))
        self.channel.exec_command(command);self.channel.settimeout(15)
        try:
            ready=self.read_exact(len(b'NOVA_UDP_READY\n'))
            if ready!=b'NOVA_UDP_READY\n':raise ValueError('Unexpected relay startup message.')
        except Exception as error:
            details=''
            if self.channel.recv_stderr_ready():details=self.channel.recv_stderr(4096).decode('utf-8',errors='replace')
            self.channel.close();client.close()
            raise ValueError('Bedrock UDP relay could not bind the VPS port. Stop any old relay and ensure Python 3 is installed. '+details) from error
        self.channel.settimeout(None)
        threading.Thread(target=self.read_packets,daemon=True).start()
        threading.Thread(target=self.send_responses,daemon=True).start()
        log(f'Bedrock UDP tunnel connected: VPS {remote_port}/UDP -> this PC {local_port}/UDP.')
        log('UDP is encapsulated in SSH/TCP; test gameplay for latency under packet loss.')
    def read_exact(self,size):
        data=bytearray()
        while len(data)<size:
            part=self.channel.recv(size-len(data))
            if not part:raise EOFError('UDP relay closed')
            data.extend(part)
        return bytes(data)
    def poll(self):
        return 0 if self.stopped.is_set() or self.channel.closed or not self.transport.is_active() or self.channel.exit_status_ready() else None
    def read_packets(self):
        try:
            while not self.stopped.is_set():
                length=struct.unpack('!I',self.read_exact(4))[0]
                if not 6<=length<=self.MAX_FRAME:raise ValueError('Invalid UDP frame size.')
                frame=self.read_exact(length);identity=frame[:6]
                with self.lock:
                    existing=self.sessions.get(identity)
                    if existing is None:
                        if len(self.sessions)>=256:continue
                        udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                        udp.connect(('127.0.0.1',self.local_port));udp.setblocking(False)
                        self.sessions[identity]=(udp,time.monotonic())
                    else:udp=existing[0]
                    self.sessions[identity]=(udp,time.monotonic())
                try:udp.send(frame[6:])
                except OSError:pass
        except (OSError,EOFError,ValueError) as error:
            if not self.stopped.is_set():self.log('Bedrock relay stopped: '+str(error))
        finally:self.terminate()
    def send_responses(self):
        try:
            while not self.stopped.wait(.01):
                with self.lock:
                    now=time.monotonic()
                    for identity,(udp,last) in list(self.sessions.items()):
                        if now-last>120:udp.close();del self.sessions[identity]
                    mapping={udp:identity for identity,(udp,last) in self.sessions.items()}
                if not mapping:
                    self.stopped.wait(.02);continue
                try:readable,_,_=select.select(list(mapping),[],[],.02)
                except (OSError,ValueError):continue
                for udp in readable:
                    try:data=udp.recv(65507)
                    except OSError:continue
                    identity=mapping[udp]
                    frame=identity+data
                    with self.send_lock:self.channel.sendall(struct.pack('!I',len(frame))+frame)
                    with self.lock:
                        if identity in self.sessions:self.sessions[identity]=(udp,time.monotonic())
        except (OSError,EOFError) as error:
            if not self.stopped.is_set():self.log('Bedrock UDP response relay failed: '+str(error))
        finally:self.terminate()
    def terminate(self):
        self.stopped.set();self.channel.close();self.client.close()
        with self.lock:
            for udp,last in self.sessions.values():udp.close()
            self.sessions.clear()
