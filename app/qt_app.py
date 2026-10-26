"""Saturn Qt Quick frontend. Backend operations run on managed workers."""
import json, os, socket, subprocess, sys, threading, time, tempfile
from pathlib import Path
from qt_runtime import configure_rendering
configure_rendering()  # Must precede Qt imports and QApplication construction.
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer, QUrl, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QFileDialog
from PySide6.QtQml import QQmlApplicationEngine
from runtime import CACHE
from settings_store import SettingsStore
from connection_settings import Connection, setup_script, preferences
from process_manager import managed_popen, start_worker
from port_ranges import parse_ranges

BASE=Path(__file__).resolve().parent
class Bridge(QObject):
    changed=Signal()
    apiKeyChanged=Signal()
    credentialsChanged=Signal()
    posted=Signal(object)
    def __init__(self, app, profile_id="main", owner=None):
        super().__init__(); self.app=app; self.window=None;self.owner=owner;self.profile_id=profile_id
        self.store=SettingsStore(CACHE/'settings.json' if profile_id=='main' else CACHE/'profiles'/profile_id/'settings.json');self.store.data.setdefault('reduced',False)
        self.s=dict(self.store.data, busy=False, activity='Ready', error='', logs='', server='Stopped', tunnel='Disconnected', uptime='—', versions=['latest'], packs=[], releases=[], mods=[], project={}, releaseIndex=0, pageIndex=0, browserRows=[],browserPath='',browserRoot='',files=[], backups=[], addons=[], editor='', file='', dirty=False, properties={}, dialog='', dialogTitle='', exiting=False, reduced=bool(self.store.data.get('reduced',False)))
        self.s.update(players=[],agreed=False,propertyDirty=False,filesLoaded=False,installedEngine='',joinDisplay=self.s['join_address'])
        from server_stats import ServerStats
        self.stats=ServerStats();self.s.update(cpuLoad=None,ramBytes=None)
        from help_content import TOPICS
        self.s['helpTopics']=TOPICS
        self.log_lock=threading.Lock();self.log_pending=[]
        self.properties_original={};self.last_files_scan=0;self.last_player_poll=0;self.loaded_folder=None;self.folder_editing=False
        from players import PlayerTracker
        self.player_tracker=PlayerTracker()
        self._friend_process=None;self._friend_sent=set();self._friend_retry_at=0
        self.secrets={'password':'','passphrase':'','apiKey':os.environ.get('CURSEFORGE_API_KEY','')}
        from secret_store import ApiKeyStore
        self.api_store=ApiKeyStore(CACHE/'curseforge-key.dpapi')
        self.api_warning=''
        try:
            remembered=self.api_store.load()
            if remembered:self.secrets['apiKey']=remembered
        except Exception:
            self.api_warning='Could not unlock the saved CurseForge key. Re-enter it to save it for this Windows account.'
        self.world_saved=threading.Event()
        self.server=None; self.tunnel=None; self.ready=threading.Event(); self.pending=False; self.running_engine='Vanilla'; self.started=0; self.generation=0
        self.confirmation=None; self.editor_meta=None; self.editor_files=None; self.properties_doc=None; self.tray=None
        self.posted.connect(self.deliver,Qt.ConnectionType.QueuedConnection)
        self.api_save_timer=QTimer(self);self.api_save_timer.setSingleShot(True)
        self.api_save_timer.timeout.connect(self.saveApiKey)
        self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(250)
        if self.store.warning:self.log(self.store.warning)
        if self.api_warning:self.log(self.api_warning)
        QTimer.singleShot(0,self.refresh_files)
    @Property('QVariantMap',notify=changed)
    def state(self):return self.s
    @Property(str,notify=apiKeyChanged)
    def apiKey(self):return self.secrets['apiKey']
    @Property(str,notify=changed)
    def serversRoot(self):return str(Path.home()/'MinecraftServers')
    @Property(str,notify=credentialsChanged)
    def sshPassword(self):return self.secrets['password']
    @Property(str,notify=credentialsChanged)
    def sshPassphrase(self):return self.secrets['passphrase']
    @Slot()
    def saveApiKey(self):
        self.api_save_timer.stop()
        try:
            self.api_store.save(self.secrets['apiKey'])
            self.log('CurseForge API key saved with Windows account encryption.' if self.secrets['apiKey'] else 'Saved CurseForge API key removed.')
        except Exception as e:self.error('Could not save CurseForge key: '+str(e))
    @Slot()
    def forgetApiKey(self):
        self.api_save_timer.stop()
        try:
            self.api_store.save('');self.secrets['apiKey']='';self.apiKeyChanged.emit();self.log('Saved CurseForge API key removed.')
        except Exception as e:self.error('Could not remove CurseForge key: '+str(e))
    @Slot(object)
    def deliver(self,fn):fn()
    def publish(self,**values):
        if any(self.s.get(k)!=v for k,v in values.items()):
            self.s.update(values);self.changed.emit()
    def log(self,message):
        if 'saved the game' in str(message).lower() or 'saved the world' in str(message).lower():self.world_saved.set()
        with self.log_lock:self.log_pending.append(str(message))
    def flush_logs(self):
        with self.log_lock:
            messages=self.log_pending;self.log_pending=[]
        if not messages:return
        names=self.s['players']
        if self.active(self.server):
            for message in messages:names=self.player_tracker.consume(message)
        self.publish(logs=(self.s['logs']+'\n'.join(messages)+'\n')[-180000:],players=names)
    def error(self,error):self.publish(error=str(error),activity='Needs attention');self.log('ERROR: '+str(error))
    def active(self,proc):return proc is not None and proc.poll() is None
    @Slot(str,'QVariant')
    def update(self,key,value):
        if self.s['exiting']:return
        if key in ('friends','auto_whitelist_friends'):
            self.error('Use the Friends tab to change saved friends.');return
        if key in self.secrets:
            self.secrets[key]=str(value)
            if key=='apiKey':self.api_save_timer.start(800)
            return
        if key=='editor':self.publish(editor=str(value),dirty=str(value)!=getattr(self,'original_text',''));return
        if key in ('folder','engine','java_version','use_vps','use_playit','direct_java_port','direct_bedrock_port','tunnel_type','local_java_port','remote_java_port','local_bedrock_port','remote_bedrock_port','bedrock_ipv6_port') and (self.s['busy'] or self.active(self.server) or self.active(self.tunnel)):
            self.error('Stop hosting and finish current work before changing server type, folder or ports.');return
        if key in ('use_vps','use_playit') and not isinstance(value,bool):
            self.error('Use VPS tunnel must be on or off.');return
        if key=='java_version' and value not in ('Auto','8','11','17','21','25'):
            self.error('Choose a listed Java version.');return
        if key=='folder':
            self.folder_editing=False
            if not str(value).strip():self.error('Choose a server folder.');return
            if self.loaded_folder and str(value)!=self.loaded_folder and (self.s['dirty'] or self.s['propertyDirty']):
                previous=self.loaded_folder
                def change(yes):
                    if yes:
                        self.publish(dirty=False,propertyDirty=False);self.update('folder',value)
                    else:self.publish(folder=previous)
                self.confirm('Discard unsaved changes?', 'Changing this server folder discards unsaved file and settings edits.',change);return
        if key=='use_vps' and value:self.s['use_playit']=False
        if key=='use_playit' and value:self.s['use_vps']=False
        if key in self.store.data or key in ('reduced','releaseIndex'):
            self.publish(**{key:value})
            if key in self.store.data:self.save()
            if key=='folder':self.refresh_files()
            if key in ('use_vps','use_playit'):self.publish(joinDisplay=self.join_display())
    @Slot(str,result=bool)
    def setJoinAddress(self,value):
        if self.s.get('use_playit'):
            self.error('The playit join address comes from your active tunnel. Configure its local target in playit.gg.');return False
        if self.s['exiting']:return False
        try:
            from connection_settings import host
            normalized=host(value) if value.strip() else ''
        except (ValueError,UnicodeError) as error:self.error(error);return False
        key='join_address' if self.s.get('use_vps',True) else 'direct_join_address'
        previous=self.s[key];self.s[key]=normalized
        if not self.save():
            self.publish(**{key:previous});return False
        self.publish(joinDisplay=self.join_display(),error='')
        self.changed.emit()
        return True
    @Slot(str,str)
    def draft(self,key,value):
        if key in ('friends','auto_whitelist_friends'):return
        if key in self.store.data and not self.s['exiting']:
            if key in ('folder','engine','java_version','use_vps','use_playit','direct_java_port','direct_bedrock_port','tunnel_type','local_java_port','remote_java_port','local_bedrock_port','remote_bedrock_port','bedrock_ipv6_port') and (self.s['busy'] or self.active(self.server) or self.active(self.tunnel)):return
            if key=='folder':self.folder_editing=True
            self.s[key]=value
    def save(self):
        try:
            data={k:self.s[k] for k in self.store.data};data.update(preferences(data))
            from port_ranges import RANGE_KEYS,normalize
            for key in RANGE_KEYS:data[key]=normalize(data[key])
            from connection_settings import port
            for key in ('local_java_port','remote_java_port','local_bedrock_port','remote_bedrock_port','bedrock_ipv6_port','direct_java_port','direct_bedrock_port'):data[key]=port(data[key])
            address=str(data.get('direct_join_address','')).strip()
            if address:
                from connection_settings import host
                data['direct_join_address']=host(address)
            self.store.save(data);return True
        except Exception as e:self.error(e);return False
    def task(self,label,fn,done=None):
        if self.s['busy'] or self.s['exiting']:return
        self.publish(busy=True,error='',activity=label)
        def work():
            try:
                result=fn()
                def complete():
                    self.publish(busy=False,activity='Ready')
                    if self.s['exiting'] and hasattr(result,'terminate'):result.terminate()
                    if not self.s['exiting'] and done:
                        try:done(result)
                        except Exception as e:self.error(e)
                self.posted.emit(complete)
            except Exception as e:
                text=str(e)
                self.posted.emit(lambda:self.failed(text))
        start_worker(work)
    def failed(self,text):self.publish(busy=False);self.error(text)
    def confirm(self,title,text,fn):
        if self.confirmation is not None:raise ValueError('Answer the current confirmation first.')
        self.confirmation=fn;self.publish(dialogTitle=title,dialog=text)
    @Slot(bool)
    def answer(self,yes):
        fn=self.confirmation;self.confirmation=None;self.publish(dialog='')
        if fn:
            try:fn(yes)
            except Exception as e:self.error(e)
    def approve(self,host,fingerprint):
        event=threading.Event();result=[False]
        def ask():
            def respond(yes):result[0]=yes;event.set()
            try:self.confirm('Trust VPS host key?',host+'\nSHA256 fingerprint: '+fingerprint+'\nVerify this fingerprint with your VPS before trusting it.',respond)
            except Exception:event.set()
        self.posted.emit(ask)
        while not event.wait(.2):
            if self.s['exiting']:return False
        return result[0]
    def stopped(self):
        if self.owner:self.owner.assert_editable(self)
        if self.active(self.server) or self.active(self.tunnel) or self.pending:raise ValueError('Stop hosting before changing server files or making a backup.')
    @Slot(str)
    def browse(self,key):
        if key=='folder':value=QFileDialog.getExistingDirectory(None,'Server folder',self.s['folder'])
        else:value=QFileDialog.getOpenFileName(None,'Select '+key,'','All files (*)')[0]
        if value:
            if key in ('folder','key'):self.update(key,value)
            else:self.publish(**{key:value})
    @Slot(str)
    def action(self,name):
        try:
            if name=='dismiss':self.publish(error='');return
            if name=='save':self.save();return
            if name=='save_all':self.save_all();return
            if name=='copy':
                if self.s.get('use_playit') and not self.playit_address():
                    raise ValueError('Start the playit agent and configure a matching tunnel before copying its public address.')
                if not self.s.get('use_playit') and not self.s.get('use_vps',True) and not self.s.get('direct_join_address'):
                    raise ValueError('Enter your public IP or domain in Settings → Domain & display before copying the public join address.')
                address=self.join_host() if self.tunnel_kind()=='Bedrock' else self.join_display()
                self.app.clipboard().setText(address)
                self.log('Join address copied.'+(' Bedrock port: '+str(self.join_port()) if self.tunnel_kind()=='Bedrock' else ''));return
            if name=='ensure_versions':
                if getattr(self,'versions_engine',None)==self.s['engine'] or self.s['busy']:return
                name='versions'
            if name=='versions':
                from engines import available_versions
                kind=self.s['engine']
                def loaded(rows):
                    self.versions_engine=kind;self.publish(versions=list(dict.fromkeys(['latest']+rows)))
                self.task('Fetching versions…',lambda:available_versions(kind),loaded);return
            if name=='install':
                self.stopped()
                if not self.s.get('agreed'):raise ValueError('Read and accept the Minecraft EULA before installation.')
                from engines import setup_engine
                kind=self.s['engine'];target=self.s['folder'];version=self.s['version'];loader=self.s['loader'];ram=int(self.s['ram']);selection=self.s['cf_pack'];key=self.secrets['apiKey']
                self.confirm('Replace every server file?',target+'\n\nThis deletes the old world, mods and configuration. Backups are manual. Stop any server launched outside Saturn first.',lambda yes:self.task('Installing '+kind+'…',lambda:setup_engine(kind,target,version,loader,ram,self.log,selection,key),self.installed) if yes else None);return
            if name=='backup':
                self.stopped();from app import manual_backup
                self.save_all();target=self.s['folder']
                def backed_up(result):self.log('Backup saved: '+str(result));self.refresh_backups()
                self.task('Making manual backup…',lambda:manual_backup(target),backed_up);return
            if name=='zip':
                self.stopped();from app import install
                archive=self.s.get('archive','');url=self.s.get('archiveUrl','').strip();target=self.s['folder']
                if url and not url.startswith('https://'):raise ValueError('Use a direct HTTPS ZIP link.')
                if not url and not archive:raise ValueError('Select a ZIP or paste its direct download link.')
                def run():
                    from runtime import download
                    with tempfile.TemporaryDirectory() as temp:
                        source=archive
                        if url:
                            source=Path(temp)/'server.zip';download(url,source,limit=10*1024**3)
                        install(source,target)
                    self.log('Server ZIP imported. Follow the pack launcher instructions if it has no Saturn launch metadata.')
                self.confirm('Replace every server file?',target+'\nAll old files will be replaced by the selected ZIP. No automatic backup.',lambda yes:self.task('Importing server ZIP…',run,self.installed) if yes else None);return
            if name=='downloads':
                paths=sorted((Path.home()/'Downloads').glob('*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)
                self.publish(downloads=[str(p) for p in paths]);return
            if name=='prepare_java':
                self.stopped()
                version=self.s.get('java_version','Auto')
                if version=='Auto':raise ValueError('Choose a Java version first.')
                from runtime import get_java
                self.task('Preparing Java '+version+'…',lambda:get_java(int(version),self.log),lambda path:self.log('Java ready: '+str(path)));return
            if name in ('start','hosting'):
                if self.s['busy'] or self.s['exiting']:return
                self.start_server()
                if self.s.get('use_playit'):
                    if name=='hosting' and self.active(self.server):self.pending=True;self.deadline=time.monotonic()+300
                    return
                if not self.s.get('use_vps',True):
                    self.pending=False
                    self.log('Direct hosting started. Forward the public game port on your router to this PC’s LAN IP and local game port. No VPS tunnel is used.');return
                if name=='hosting' and not self.s['vps_host']:
                    self.log('Local hosting started. Configure a VPS, or uncheck Use VPS tunnel for LAN / router port forwarding.');return
                if name=='hosting' and self.active(self.server):self.pending=True;self.deadline=time.monotonic()+300
                return
            if name=='tunnel':self.connect_tunnel();return
            if name=='stop':self.stop();return
            if name=='configure':
                if not self.s.get('use_vps',True):raise ValueError('Use VPS tunnel is off. Configure your router for direct hosting instead.')
                if self.active(self.tunnel):raise ValueError('Stop the tunnel before configuring your VPS.')
                c=Connection.parse(self.s);creds=self.credentials()
                from host_ports import vps_script
                ports=self.owner.vps_ports(c) if self.owner else ([self.s['remote_java_port']]+parse_ranges(self.s['java_port_ranges']),[self.s['remote_bedrock_port']]+parse_ranges(self.s['bedrock_port_ranges']))
                script=vps_script((BASE/'vps_setup.sh').read_text(),c.ssh_username,*ports)
                def configure():
                    from ssh_backend import connect,configure
                    client=connect(*creds,self.approve,self.log,host=c.vps_host,username=c.ssh_username,port=c.ssh_port)
                    configure(client,script,self.log,use_sudo=c.ssh_username!='root')
                self.confirm('Configure VPS?',f'Apply Saturn SSH forwarding and game firewall settings on {c.ssh_username}@{c.vps_host}:{c.ssh_port}?',lambda yes:self.task('Configuring VPS…',configure) if yes else None);return
            if name=='test':
                c=Connection.parse(self.s);bedrock=self.tunnel_kind()=='Bedrock';public=int(self.s['remote_bedrock_port'] if bedrock else self.s['remote_java_port']);local=int(self.s['local_bedrock_port'] if bedrock else self.s['local_java_port'])
                def test():
                    for host in dict.fromkeys(['127.0.0.1',c.vps_host,c.join_address]):
                        try:
                            if bedrock:
                                from bedrock import probe
                                self.log(host+': '+str(probe(host,local if host=='127.0.0.1' else public)))
                            else:
                                with socket.create_connection((host,local if host=='127.0.0.1' else public),timeout=6):pass
                                self.log(host+': TCP '+str(local if host=='127.0.0.1' else public)+' reachable')
                        except Exception as e:self.log(host+': '+str(e))
                self.task('Testing connection…',test);return
            if name=='files':
                if self.s['propertyDirty']:
                    self.confirm('Discard unsaved settings?','Reloading replaces unsaved server settings.',lambda yes:self.load_files() if yes else None)
                else:self.load_files()
                return
            if name=='backups':self.refresh_backups();return
            if name=='ensure_files':self.refresh_files();return
            if name=='write':self.write_file();return
            if name=='properties':self.save_properties();return
            if name=='search':self.search();return
            if name=='mods':self.load_mods();return
            if name=='older':
                from engines import CurseAPI
                project=self.s['project'];key=self.secrets['apiKey'];offset=getattr(self,'release_offset',50)
                def done(rows):
                    self.release_offset=offset+len(rows)
                    self.publish(releases=self.s['releases']+[r for r in rows if not r.get('isServerPack')])
                self.task('Loading older releases…',lambda:CurseAPI(key).files(project['id'],offset)['data'],done);return
            if name=='pick':self.pick();return
            if name=='clear':self.publish(logs='');return
            if name=='tray':self.minimize();return
            if name=='exit':self.exit();return
        except Exception as e:self.error(e)
    @Slot(bool)
    def agree(self,value):self.publish(agreed=value)
    @Slot(str,str)
    def setPath(self,key,value):
        if key in ('archive','archiveUrl'):self.publish(**{key:value})
    def credentials(self):return (self.s['key'],self.secrets['password'],self.secrets['passphrase'])
    def start_server(self):
        if self.active(self.server):return
        if self.s['dirty'] or self.s['propertyDirty']:self.save_all()
        if self.owner:self.owner.preflight(self)
        self.apply_ports()
        folder=Path(self.s['folder']).expanduser().resolve();state=json.loads((folder/'switcher-server.json').read_text())
        if 'eula=true' not in (folder/'eula.txt').read_text().splitlines():raise ValueError('Minecraft EULA is not accepted.')
        engine=state.get('engine','Vanilla')
        if engine=='Bedrock':command=[str(folder/'bedrock_server.exe')]
        else:
            java=Path(state['java']).resolve();ram=int(self.s['ram'])
            selected=self.s.get('java_version','Auto')
            if selected!='Auto':
                matches=list((CACHE/'runtime'/selected).glob('*/bin/java.exe'))
                if len(matches)!=1:raise ValueError('Prepare Java '+selected+' in Settings → Environment before starting this server.')
                java=matches[0].resolve()
            if CACHE.resolve() not in java.parents or java.name.lower()!='java.exe':raise ValueError('Unexpected Java path. Reinstall the selected server.')
            if not 2<=ram<=16:raise ValueError('RAM must be 2–16 GB.')
            args=state.get('args',['-jar','server.jar','nogui'])
            if not isinstance(args,list) or not all(isinstance(a,str) for a in args):raise ValueError('Invalid launch metadata.')
            command=[str(java),'-Xms1G',f'-Xmx{ram}G',*args]
        self.ready=threading.Event();self.player_tracker.names.clear();self.player_tracker.expect_names=False;self.running_engine=engine;self.started=time.monotonic()
        self.server=managed_popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        proc=self.server;ready=self.ready
        def read():
            for line in proc.stdout:
                if 'Done (' in line or 'Server started' in line:ready.set()
                self.log(line.rstrip())
            proc.wait();self.log('Server exited: '+str(proc.returncode))
        threading.Thread(target=read,daemon=True).start()
    @Slot(str)
    def command(self,text):
        try:
            if not self.active(self.server):raise ValueError('Start the server first.')
            if any(c in text for c in '\r\n\x00'):raise ValueError('Enter one command at a time.')
            self.server.stdin.write(text.lstrip('/')+'\n');self.server.stdin.flush();return True
        except Exception as e:self.error(e);return False
    def connect_tunnel(self):
        if self.s.get('use_playit'):
            if self.s['busy'] or self.active(self.tunnel):return
            if not self.active(self.server):raise ValueError('Start the server first.')
            if not self.owner:raise ValueError('playit needs the multi-server launcher.')
            local=int(self.s['local_bedrock_port'] if self.tunnel_kind()=='Bedrock' else self.s['local_java_port'])
            self.tunnel=self.owner.playit.acquire(self.profile_id,local)
            self.log('playit agent started. Approve it and create the game tunnel in Settings → Hosting connection.');return
        if not self.s.get('use_vps',True):raise ValueError('Use VPS tunnel is off for this profile.')
        if self.s['busy'] or self.active(self.tunnel):return
        if not self.active(self.server):raise ValueError('Start the server first.')
        c=Connection.parse(self.s);creds=self.credentials();bedrock=self.tunnel_kind()=='Bedrock';generation=self.generation
        if bedrock!=(self.running_engine=='Bedrock'):raise ValueError('The selected tunnel type must match this profile’s installed server. Use another profile for the other edition.')
        if self.owner:self.owner.preflight(self,for_tunnel=True)
        local=int(self.s['local_bedrock_port'] if bedrock else self.s['local_java_port']);remote=int(self.s['remote_bedrock_port'] if bedrock else self.s['remote_java_port'])
        def run():
            from ssh_backend import connect,ReverseTunnel
            client=connect(*creds,self.approve,self.log,host=c.vps_host,username=c.ssh_username,port=c.ssh_port)
            try:
                if bedrock:
                    from bedrock import BedrockTunnel
                    return BedrockTunnel(client,self.log,local_port=local,remote_port=remote)
                return ReverseTunnel(client,self.log,local_port=local,remote_port=remote)
            except Exception:client.close();raise
        def connected(tunnel):
            if generation!=self.generation or not self.active(self.server):tunnel.terminate();return
            self.tunnel=tunnel;self.log('Tunnel connected.')
        self.task('Connecting to VPS…',run,connected)
    def stop(self):
        self.pending=False;self.generation+=1
        if self.active(self.tunnel):self.tunnel.terminate()
        if self.active(self.server):self.command('stop');self.log('Saving world and stopping…')
    def tick(self):
        self.flush_logs()
        running=self.active(self.server);tunnel=self.active(self.tunnel)
        self._sync_friends()
        self.publish(**self.stats.sample(self.server))
        elapsed=int(time.monotonic()-self.started) if running else 0
        self.publish(joinDisplay=self.join_display(),server=('Ready' if self.ready.is_set() else 'Starting') if running else 'Stopped',tunnel=(self.owner.playit.tunnel_status(int(self.s['local_bedrock_port'] if self.tunnel_kind()=='Bedrock' else self.s['local_java_port'])) if tunnel and self.s.get('use_playit') and self.owner else ('Connected' if tunnel else 'Disconnected')),uptime='%02d:%02d:%02d'%(elapsed//3600,elapsed//60%60,elapsed%60) if running else '—')
        if not running and self.s['players']:self.publish(players=[])
        if running and self.ready.is_set() and time.monotonic()-self.last_player_poll>15:
            self.last_player_poll=time.monotonic();self.command('list')
        if not self.s['busy'] and time.monotonic()-self.last_files_scan>2:
            self.last_files_scan=time.monotonic();self.refresh_files()
        if not running and tunnel:self.tunnel.terminate()
        if self.pending and not self.s['busy']:
            if not running:self.pending=False
            elif self.ready.is_set():self.pending=False;self.action('tunnel')
            elif time.monotonic()>self.deadline:self.pending=False;self.error('Readiness was not detected. Review the console before connecting the tunnel.')
    def tunnel_kind(self):
        choice=self.s.get('tunnel_type','Auto') if self.s.get('use_vps',True) and not self.s.get('use_playit') else 'Auto'
        if choice!='Auto':return choice
        engine=self.running_engine if self.active(self.server) else self.s.get('installedEngine') or self.s['engine']
        return 'Bedrock' if engine=='Bedrock' else 'Java'
    def playit_address(self):
        if not self.owner:return None
        local=int(self.s['local_bedrock_port'] if self.tunnel_kind()=='Bedrock' else self.s['local_java_port'])
        return self.owner.playit.address(local) if self.owner.playit.connected else None
    def join_host(self):
        if self.s.get('use_playit'):
            address=self.playit_address();return address[0] if address else ''
        if not self.s.get('use_vps',True):return self.s.get('direct_join_address','')
        return self.s['join_address'] or self.s['vps_host'] or 'localhost'
    def join_port(self):
        if self.s.get('use_playit'):
            address=self.playit_address()
            if not address:raise ValueError('Configure a matching playit game tunnel.')
            if address[1] is None and self.tunnel_kind()=='Bedrock':raise ValueError('The Bedrock public port was not reported by playit.')
            return address[1] or 25565
        kind='bedrock_port' if self.tunnel_kind()=='Bedrock' else 'java_port'
        prefix='direct_' if not self.s.get('use_vps',True) else ('remote_' if self.s['vps_host'] else 'local_')
        return int(self.s[prefix+kind])
    def join_display(self):
        bedrock=self.tunnel_kind()=='Bedrock';address=self.join_host()
        if not address:return 'Configure playit tunnel in Settings' if self.s.get('use_playit') else 'Set direct join address in Settings'
        try:port=self.join_port()
        except (ValueError,TypeError):return address+' (enter a valid game port)'
        if bedrock:return address+' : '+str(port)+' (Bedrock UDP)'
        if ':' in address:address='['+address+']'
        return address if port==25565 else address+':'+str(port)
    def apply_ports(self):
        from server_files import Properties,atomic_write,fingerprint
        from connection_settings import port
        path=Path(self.s['folder']).expanduser().resolve()/'switcher-server.json'
        original=path.read_bytes();state=json.loads(original)
        keys=('local_java_port','local_bedrock_port','bedrock_ipv6_port')
        network={k:port(self.s[k]) for k in keys}
        network['use_vps']=bool(self.s.get('use_vps',True) or self.s.get('use_playit'))
        if network['local_bedrock_port']==network['bedrock_ipv6_port']:raise ValueError('Bedrock IPv4 and IPv6 ports must be different.')
        if state.get('nova_ports')!=network:
            state['nova_ports']=network
            atomic_write(path,json.dumps(state,indent=2).encode(),fingerprint(original))
        Properties(path.parent/'server.properties').save({})
    def installed(self,result=None):
        self.editor_meta=None;self.editor_files=None;self.properties_doc=None
        self.publish(editor='',file='',dirty=False,propertyDirty=False)
        if (Path(self.s['folder'])/'switcher-server.json').exists():self.apply_ports()
        self.load_files();self.save();self.refresh_backups()
    def refresh_files(self):
        if self.s['busy'] or self.folder_editing:return
        try:
            if not (Path(self.s['folder'])/'server.properties').is_file():
                if self.loaded_folder!=self.s['folder']:
                    self.loaded_folder=self.s['folder'];self.properties_doc=None;self.editor_meta=None;self.editor_files=None
                    self.publish(browserRows=[],browserPath='',browserRoot='',files=[],addons=[],properties={},editor='',file='',dirty=False,propertyDirty=False,filesLoaded=False,installedEngine='')
                return
            if self.loaded_folder!=self.s['folder']:
                self.editor_meta=None;self.editor_files=None
                self.publish(editor='',file='',dirty=False,propertyDirty=False)
            self.load_files(preserve=True)
        except (OSError,ValueError) as error:
            # Missing/transient files during a server rebuild are retried next tick.
            if self.loaded_folder!=self.s['folder']:self.log('Waiting for server files: '+str(error))
    def load_files(self,preserve=False):
        from server_files import ServerFiles,Properties
        files=ServerFiles(self.s['folder']);self.loaded_folder=self.s['folder']
        if self.s['browserRoot']!=str(files.root):
            from file_browser import FileBrowser
            self.publish(browserRows=FileBrowser(files.root).listing(),browserPath='',browserRoot=str(files.root))
        values=dict(files=files.config_files(),addons=[{'kind':k,'name':n} for k in ('mods','plugins') for n in files.addons(k)],filesLoaded=True,installedEngine=files.state.get('engine',self.s['engine']))
        if not preserve or not self.s['propertyDirty']:
            self.properties_doc=Properties(files.root/'server.properties');self.properties_original=dict(self.properties_doc.values)
            values.update(properties=self.properties_doc.values,propertyDirty=False)
        self.publish(**values)
        if not self.s['dirty']:
            name=self.s['file'] or ('server.properties' if 'server.properties' in values['files'] else '')
            if name in values['files']:self._open_file(name)
    @Slot(str)
    def browseFiles(self,relative):
        try:
            from file_browser import FileBrowser
            target=self.s['folder'];browser=FileBrowser(target)
            self.task('Loading folder…',lambda:browser.listing(relative),lambda rows:self.publish(browserRows=rows,browserPath=relative,browserRoot=str(browser.root)) if self.s['folder']==target else None)
        except Exception as error:self.error(error)
    @Slot(str)
    def open_file(self,name):
        try:
            if self.s['dirty']:
                self.confirm('Discard unsaved edits?','The current file has unsaved changes.',lambda yes:self._open_file(name) if yes else None)
            else:self._open_file(name)
        except Exception as e:self.error(e)
    def _open_file(self,name):
        from file_browser import FileBrowser
        files=FileBrowser(self.s['folder']);text,checksum,encoding=files.read_text(name)
        self.editor_meta=(checksum,encoding);self.editor_files=files;self.original_text=text
        self.publish(file=name,editor=text,dirty=False)
    def write_file(self):
        self.stopped()
        if self.s['busy']:raise ValueError('Wait for current work to finish.')
        if not self.editor_meta:raise ValueError('Open a configuration file first.')
        if self.editor_files.root!=Path(self.s['folder']).expanduser().resolve():raise ValueError('Server folder changed. Reload the file first.')
        name=self.s['file'];self.editor_files.write_text(name,self.s['editor'],*self.editor_meta);self._open_file(name);self.log('Saved '+name)
    @Slot(str,str)
    def property_value(self,key,value):
        props=dict(self.s['properties']);props[key]=value;self.publish(properties=props,propertyDirty=props!=self.properties_original)
    def save_properties(self):
        self.stopped()
        if self.s['busy']:raise ValueError('Wait for current work to finish.')
        if not self.properties_doc:raise ValueError('Reload files first.')
        if self.properties_doc.path.parent!=Path(self.s['folder']).expanduser().resolve():raise ValueError('Reload the server folder first.')
        self.save_all();self.log('Server settings saved.')
    def save_all(self):
        self.stopped()
        if self.s['busy']:raise ValueError('Wait for current work to finish.')
        from server_files import Properties,fingerprint
        dirty=self.s['dirty'];prop_dirty=self.s['propertyDirty']
        updates={k:v for k,v in self.s['properties'].items() if self.properties_original.get(k)!=v} if prop_dirty else {}
        if prop_dirty:
            if not self.properties_doc or self.properties_doc.path.parent!=Path(self.s['folder']).expanduser().resolve():
                raise ValueError('Reload the server folder first.')
            current=self.properties_doc.path.read_bytes() if self.properties_doc.path.exists() else None
            if fingerprint(current)!=fingerprint(self.properties_doc.original):raise ValueError('Server settings changed on disk. Reload before saving.')
        if dirty and self.s['file']=='server.properties' and prop_dirty:
            # Merge independent edits made in the raw editor and settings form.
            edited=Properties(self.properties_doc.path);edited.text=self.s['editor'];edited.values={}
            for raw,line in edited.iter_records():
                pair=edited.parse(line)
                if pair:edited.values[pair[0]]=pair[1]
            for key,value in updates.items():
                raw_value=edited.values.get(key)
                if raw_value!=self.properties_original.get(key) and raw_value!=value:
                    raise ValueError('Conflicting edits for '+key+'. Use the same value in the editor and Server settings.')
        if dirty:self.write_file()
        if prop_dirty:
            doc=Properties(self.properties_doc.path) if dirty and self.s['file']=='server.properties' else self.properties_doc
            doc.save(updates)
        if not self.save():raise ValueError('Could not save preferences.')
        self.publish(propertyDirty=False)
        self.load_files(preserve=True)
        if dirty or prop_dirty:self.log('All file and server settings changes saved.')
    def refresh_backups(self):
        from backups import list_backups
        self.publish(backups=list_backups(self.s['folder']))
    @Slot(str)
    def restoreBackup(self,path):
        try:
            self.stopped()
            if self.s['busy']:raise ValueError('Wait for current work to finish.')
            from backups import list_backups,restore_backup
            target=self.s['folder']
            if path not in {row['path'] for row in list_backups(target)}:raise ValueError('Choose a listed backup.')
            def restore(yes):
                if not yes:return
                self.stopped()
                if self.s['folder']!=target:raise ValueError('Server profile changed. Select the backup again.')
                self.task('Restoring backup…',lambda:restore_backup(target,path),self.installed)
            self.confirm('Restore this backup?',Path(path).name+'\n\nThis replaces the current world, mods and settings, including unsaved edits. The selected backup stays available. No automatic backup is made.',restore)
        except Exception as e:self.error(e)
    @Slot(str,str,str)
    def addon(self,operation,kind,name):
        try:
            self.stopped()
            if self.s['busy']:raise ValueError('Wait for current work to finish.')
            from server_files import ServerFiles
            files=ServerFiles(self.s['folder'])
            def perform():
                self.save_all()
                def run():return getattr(files,operation)(kind,name)
                self.task('Updating add-on…',run,lambda result:self.load_files(preserve=True))
            if operation=='remove':self.confirm('Remove add-on?',name,lambda yes:perform() if yes else None)
            elif operation in ('toggle','add'):perform()
        except Exception as e:self.error(e)
    @Slot(str,str,str,int)
    def query(self,text,sort,version,offset):
        self.query_values=(text,sort,version,offset);self.search()
    def friend_edition(self):
        engine=self.running_engine if self.active(self.server) else self.s.get('installedEngine') or self.s['engine']
        return 'Bedrock' if engine=='Bedrock' else 'Java'
    def friend_rows(self):
        from friends import friend_key
        edition=self.friend_edition();running=self.active(self.server)
        rows=[]
        for entry in self.s['friends']:
            if entry['edition']!=edition:status='Waiting for a '+entry['edition']+' server'
            elif running and self._friend_process is self.server and friend_key(entry) in self._friend_sent:status='Command sent this run'
            elif not self.s['auto_whitelist_friends']:status='Auto-add is off'
            elif not running or not self.ready.is_set():status='Queued until this server is ready'
            else:status='Queued'
            rows.append(dict(entry,status=status))
        return rows
    def _save_friends(self,rows,automatic):
        previous=self.s['friends'];old_auto=self.s['auto_whitelist_friends']
        self.s.update(friends=rows,auto_whitelist_friends=automatic)
        if not self.save():
            self.s.update(friends=previous,auto_whitelist_friends=old_auto);self.changed.emit();return False
        self.changed.emit();return True
    @Slot(str,str,result=bool)
    def addFriend(self,name,edition):
        if self.s['exiting']:return False
        try:
            from friends import friend_entry,friend_key,MAX_FRIENDS
            entry=friend_entry(name,edition)
            if any(friend_key(row)==friend_key(entry) for row in self.s['friends']):
                raise ValueError('That friend is already saved for this edition.')
            if len(self.s['friends'])>=MAX_FRIENDS:raise ValueError('A profile can save up to 100 friends.')
            if not self._save_friends([*self.s['friends'],entry],self.s['auto_whitelist_friends']):return False
            self._sync_friends();return True
        except (ValueError,TypeError) as error:self.error(error);return False
    @Slot(str,str)
    def forgetFriend(self,name,edition):
        if self.s['exiting']:return
        from friends import friend_key
        key=(edition,name.casefold())
        rows=[row for row in self.s['friends'] if friend_key(row)!=key]
        if self._save_friends(rows,self.s['auto_whitelist_friends']):
            self._friend_sent.discard(key)
            self.log('Friend forgotten. Existing server whitelist entries are unchanged.')
    @Slot(bool)
    def autoWhitelistFriends(self,enabled):
        if self.s['exiting']:return
        if self._save_friends(list(self.s['friends']),enabled):self._sync_friends()
    @Slot()
    def syncFriendsNow(self):
        if self.s['exiting']:return
        if not self.active(self.server) or not self.ready.is_set():
            self.error('Start this server and wait until it is ready before syncing friends.');return
        self._sync_friends(force=True)
    def _sync_friends(self,force=False):
        from friends import friend_key
        from players import player_command
        if self._friend_process is not self.server:
            self._friend_process=self.server;self._friend_sent=set();self._friend_retry_at=0
        if self.s['exiting'] or self.s['busy'] or not self.active(self.server) or not self.ready.is_set():return 0
        if not force and (not self.s['auto_whitelist_friends'] or time.monotonic()<self._friend_retry_at):return 0
        edition=self.friend_edition()
        entries=[row for row in self.s['friends'] if row['edition']==edition]
        if force:
            for entry in entries:self._friend_sent.discard(friend_key(entry))
        sent=0
        for entry in entries:
            key=friend_key(entry)
            if key in self._friend_sent:continue
            if not self.command(player_command('allow',entry['name'],edition=='Bedrock')):
                self._friend_retry_at=time.monotonic()+15;break
            self._friend_sent.add(key);sent+=1
            if not force and sent>=5:break
        if sent:self.changed.emit()
        return sent
    @Slot(str,str)
    def playerAction(self,operation,name):
        try:
            from players import player_command
            text=player_command(operation,name,self.running_engine=='Bedrock')
            if not self.active(self.server):raise ValueError('Start this profile’s server first.')
            if operation in ('kick','ban','op','deop'):
                self.confirm('Apply player action?',operation+' '+name+' on this server?',lambda yes:self.command(text) if yes else None)
            else:self.command(text)
        except Exception as e:self.error(e)
    def search(self):
        from engines import CurseAPI
        from curse_catalog import SORTS,relevant
        text,sort,version,offset=getattr(self,'query_values',('','Popular','',0));key=self.secrets['apiKey']
        def run():
            rows=CurseAPI(key).search(text,offset,SORTS.get(sort,2),version)['data']
            return relevant(rows,text) if sort=='Relevant' else rows
        self.task('Searching CurseForge…',run,lambda rows:self.publish(packs=rows,pageIndex=offset))
    @Slot(int,int)
    def project(self,index,offset):
        try:
            from engines import CurseAPI
            project=self.s['packs'][index];key=self.secrets['apiKey']
            def done(rows):
                self.release_offset=offset+len(rows)
                releases=[r for r in rows if not r.get('isServerPack')]
                self.publish(project=project,releases=releases,releaseIndex=next((i for i,r in enumerate(releases) if r.get('serverPackFileId')),0),mods=[])
            self.task('Loading releases…',lambda:CurseAPI(key).files(project['id'],offset)['data'],done)
        except Exception as e:self.error(e)
    def load_mods(self):
        from engines import CurseAPI
        from curse_catalog import release_mods
        project=self.s['project'];release=self.s['releases'][self.s['releaseIndex']];key=self.secrets['apiKey']
        self.task('Reading release manifest…',lambda:release_mods(CurseAPI(key),project['id'],release['id']),lambda rows:self.publish(mods=rows))
    def pick(self):
        project=self.s['project'];release=self.s['releases'][self.s['releaseIndex']]
        if not release.get('serverPackFileId'):raise ValueError('Choose a release with Server: Yes.')
        selection=dict(artwork=(project.get('logo') or {}).get('thumbnailUrl',''),project_id=project['id'],file_id=release['id'],name=project['name'],release=release.get('displayName') or release.get('fileName') or ('Release '+str(release['id'])))
        self.publish(cf_pack=selection,engine='CurseForge');self.save();self.log('Selected '+selection['name']+' / '+selection['release'])
    def setup_tray(self):
        icon=QIcon(str(BASE/'Saturn.ico'));self.app.setWindowIcon(icon);self.tray=QSystemTrayIcon(icon,self.app);self.tray.setToolTip('Saturn Server Launcher')
        self.menu=QMenu();self.menu.addAction('Open Saturn',self.restore);self.menu.addSeparator();self.menu.addAction('Exit Saturn • stop hosting',self.exit)
        self.tray.setContextMenu(self.menu);self.tray.activated.connect(lambda reason:self.restore() if reason in (QSystemTrayIcon.ActivationReason.Trigger,QSystemTrayIcon.ActivationReason.DoubleClick) else None);self.tray.show()
    def restore(self):self.window.showNormal();self.window.raise_();self.window.requestActivate()
    def minimize(self):
        self.save()
        if self.tray and QSystemTrayIcon.isSystemTrayAvailable():self.window.hide()
        else:self.window.showMinimized();self.log('No system tray is available. Minimized to taskbar; hosting continues.')
    def exit(self):
        if self.s['exiting']:return
        if self.s['dirty'] or self.s['propertyDirty']:
            self.confirm('Discard unsaved edits and exit?','Your server will save and stop. Unsaved editor changes will be discarded.',lambda yes:self._exit() if yes else None)
        else:self._exit()
    def _exit(self):
        if not self.save():return
        if self.api_save_timer.isActive():self.saveApiKey()
        self.restore();self.publish(exiting=True,activity='Saving world and closing…');self.stop()
        from process_manager import cancelled,stop_all,wait_workers
        cancelled.set()
        def finish():
            deadline=time.monotonic()+45
            while self.active(self.server) and time.monotonic()<deadline:time.sleep(.1)
            stop_all()
            while not wait_workers(1):pass
            self.posted.emit(self.app.quit)
        threading.Thread(target=finish,daemon=True).start()

def main():
    os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
    app=QApplication(sys.argv);app.setApplicationName('Saturn Server Launcher');app.setQuitOnLastWindowClosed(False)
    from hosts import HostManager
    bridge=HostManager(app,Bridge);engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',bridge)
    engine.load(QUrl.fromLocalFile(str(BASE/'qml'/'Main.qml')))
    if not engine.rootObjects():raise RuntimeError('Saturn QML could not load. See app.log.')
    bridge.window=engine.rootObjects()[0];bridge.setup_tray()
    # Explicitly restore after the event loop starts, including shell launches.
    def show_startup():
        bridge.restore()
        print('Saturn main window restored; visible='+str(bridge.window.isVisible()),flush=True)
    QTimer.singleShot(0,show_startup)
    result=app.exec()
    if bridge.tray:bridge.tray.hide()
    # Dispose QML while its context object still exists.
    import shiboken6
    shiboken6.delete(engine)
    return result
if __name__=='__main__':sys.exit(main())
