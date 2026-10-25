"""In-process SSH authentication and reverse forwarding, with no terminal windows."""
from process_manager import managed_popen,check_cancelled
import base64
import hashlib
import importlib
import os
import socket
import subprocess
import sys
import threading
from pathlib import Path
from runtime import CACHE


_dependency_lock=threading.Lock()
_known_hosts_lock=threading.Lock()

def ensure_ssh(log):
    while not _dependency_lock.acquire(timeout=.2):check_cancelled()
    try:
        check_cancelled()
        return _ensure_ssh(log)
    finally:_dependency_lock.release()

def _ensure_ssh(log):
    vendor=CACHE/'ssh-libs-locked-v1'
    if str(vendor) not in sys.path:sys.path.insert(0,str(vendor))
    lockfile=Path(__file__).with_name('ssh-requirements.txt')
    expected=hashlib.sha256(lockfile.read_bytes()).hexdigest()
    marker=vendor/'.requirements-sha256'
    if marker.is_file() and marker.read_text()==expected:
        return importlib.import_module('paramiko')
    log('Installing SSH support locally. First use only; no terminal window is opened...')
    vendor.mkdir(parents=True,exist_ok=True)
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe' and python.with_name('python.exe').exists():
        python=python.with_name('python.exe')
    with managed_popen([str(python),'-m','pip','install','--disable-pip-version-check','--no-input','--upgrade','--target',str(vendor),'--isolated','--index-url','https://pypi.org/simple','--only-binary=:all:','--require-hashes','-r',str(Path(__file__).with_name('ssh-requirements.txt'))],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)) as proc:
        for line in proc.stdout:log(line.rstrip())
        code=proc.wait()
    if code:raise ValueError('SSH support could not be installed. Check the installation log and retry.')
    marker.write_text(expected)
    importlib.invalidate_caches()
    return importlib.import_module('paramiko')


def connect(key,password,passphrase,approve,log,host="",username="root",port=22):
    from connection_settings import Connection
    connection=Connection.parse({'vps_host':host,'ssh_username':username,'ssh_port':port,'join_address':host})
    host=connection.vps_host;username=connection.ssh_username;port=connection.ssh_port
    paramiko=ensure_ssh(log)
    client=paramiko.SSHClient()
    known=CACHE/'ssh-known-hosts';known.parent.mkdir(parents=True,exist_ok=True)
    system=Path.home()/'.ssh'/'known_hosts'
    if system.is_file():client.load_system_host_keys(str(system))
    with _known_hosts_lock:
        if known.is_file():client.load_host_keys(str(known))
    class Trust(paramiko.MissingHostKeyPolicy):
        def missing_host_key(self,ssh,hostname,hostkey):
            digest=base64.b64encode(hashlib.sha256(hostkey.asbytes()).digest()).decode().rstrip('=')
            if not approve(hostname,'SHA256:'+digest):raise ValueError('SSH host was not trusted. Connection canceled.')
            with _known_hosts_lock:
                if known.is_file():ssh.load_host_keys(str(known))
                ssh.get_host_keys().add(hostname,hostkey.get_name(),hostkey)
                ssh.save_host_keys(str(known))
    client.set_missing_host_key_policy(Trust())
    if key:
        key=str(Path(key).expanduser().resolve())
        if not Path(key).is_file():raise ValueError('Private key file does not exist.')
        if Path(key).name in ('known_hosts','authorized_keys') or key.endswith('.pub'):
            raise ValueError('Select the private id_ed25519/id_rsa file, not known_hosts, authorized_keys, or a .pub file.')
    try:
        client.connect(host,port=port,username=username,key_filename=key or None,password=password or None,passphrase=passphrase or None,allow_agent=not bool(key),look_for_keys=not bool(key),timeout=15,auth_timeout=30,banner_timeout=30)
        check_cancelled()
        client.get_transport().set_keepalive(20)
        log('SSH authenticated: '+username+'@'+host+':'+str(port)+'.')
        return client
    except paramiko.AuthenticationException as error:
        client.close();raise ValueError('VPS login rejected. Check the SSH password or select the private key whose public key is installed on the VPS.') from error
    except Exception:
        client.close();raise


def configure(client,script,log,use_sudo=False):
    try:
        channel=client.get_transport().open_session(timeout=20)
        channel.set_combine_stderr(True);channel.exec_command('sudo -n bash -s' if use_sudo else 'bash -s')
        channel.sendall(script.encode('utf-8'));channel.shutdown_write()
        stream=channel.makefile('r')
        for line in stream:
            if isinstance(line,bytes):line=line.decode('utf-8',errors='replace')
            log(line.rstrip())
        code=channel.recv_exit_status();channel.close()
        if code:raise ValueError('VPS setup failed with exit code '+str(code)+'. See the log above.')
        log('VPS configured. Start the server, then start the tunnel.')
    finally:client.close()


class ReverseTunnel:
    def __init__(self,client,log,local_port=25565,remote_port=25565):
        self.client=client;self.transport=client.get_transport();self.log=log
        from connection_settings import port
        self.local_port=port(local_port);self.remote_port=port(remote_port)
        self.stopped=threading.Event();self.lock=threading.Lock();self.connections=set();self.slots=threading.BoundedSemaphore(64)
        try:self.transport.request_port_forward('0.0.0.0',self.remote_port,handler=self.accept)
        except Exception:
            client.close();raise ValueError(f'VPS refused public port {self.remote_port}. Configure the VPS first and stop any old tunnel using that port.')
        self.log(f'Tunnel connected: VPS TCP {self.remote_port} -> this PC 127.0.0.1:{self.local_port}.')
    def poll(self):return 0 if self.stopped.is_set() or not self.transport.is_active() else None
    def accept(self,channel,origin,server):
        if self.stopped.is_set() or not self.slots.acquire(blocking=False):
            channel.close();return
        try:threading.Thread(target=self.bridge,args=(channel,),daemon=True).start()
        except Exception:
            self.slots.release();channel.close();raise
    def bridge(self,channel):
        local=None;pair=None
        try:
            local=socket.create_connection(('127.0.0.1',self.local_port),timeout=10);local.settimeout(120);channel.settimeout(120)
            pair=(channel,local)
            with self.lock:
                if self.stopped.is_set():return
                self.connections.add(pair)
            def pump(source,destination):
                try:
                    while not self.stopped.is_set():
                        data=source.recv(65536)
                        if not data:break
                        destination.sendall(data)
                except (OSError,EOFError):pass
                finally:
                    try:
                        if hasattr(destination,'shutdown_write'):destination.shutdown_write()
                        else:destination.shutdown(socket.SHUT_WR)
                    except (OSError,EOFError):pass
            outbound=threading.Thread(target=pump,args=(channel,local),daemon=True);outbound.start()
            pump(local,channel);outbound.join()
        except (OSError,EOFError) as e:
            if not self.stopped.is_set():self.log('Tunnel connection failed: '+str(e))
        finally:
            self.slots.release()
            channel.close()
            if local:local.close()
            if pair:
                with self.lock:self.connections.discard(pair)
    def terminate(self):
        self.stopped.set();self.client.close()
        with self.lock:pairs=list(self.connections)
        for pair in pairs:
            for endpoint in pair:
                try:
                    if isinstance(endpoint,socket.socket):endpoint.shutdown(socket.SHUT_RDWR)
                    endpoint.close()
                except OSError:pass
