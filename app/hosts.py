"""Independent running server profiles, with one shared Nova window."""
import json,os,tempfile,threading,time,uuid
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot,Qt
from PySide6.QtWidgets import QSystemTrayIcon,QFileDialog
from connection_settings import Connection

class HostManager(QObject):
    changed=Signal();apiKeyChanged=Signal();credentialsChanged=Signal();storageChanged=Signal();posted=Signal(object)
    def __init__(self,app,bridge_class):
        super().__init__();self.app=app;self.bridge_class=bridge_class;self.window=None;self.tray=None;self.exiting=False
        # Derive the cache from the backend so tests can isolate all state.
        import sys
        self.cache=Path(sys.modules[bridge_class.__module__].CACHE)
        self.path=self.cache/'profiles.json';self.entries=[{'id':'main','name':'My server'}];self.current=0;self.warning='';self.servers_root=Path.home()/'MinecraftServers'
        try:
            data=json.loads(self.path.read_text());rows=data['profiles']
            if not isinstance(rows,list) or not rows:raise ValueError('Empty profile registry')
            ids=set()
            for row in rows:
                identifier=row['id']
                if not isinstance(identifier,str) or not identifier.isalnum() or identifier in ids:raise ValueError('Invalid profile identifier')
                if not isinstance(row['name'],str) or not row['name'].strip():raise ValueError('Invalid profile name')
                ids.add(identifier)
            storage=data.get('servers_root')
            if isinstance(storage,str) and storage.strip():self.servers_root=Path(storage).expanduser().resolve()
            self.entries=rows;self.current=next((i for i,p in enumerate(rows) if p['id']==data.get('selected')),0)
        except FileNotFoundError:pass
        except (OSError,ValueError,KeyError,TypeError):
            self.warning='Could not read server profiles. Defaults loaded.'
            try:
                if self.path.exists():
                    backup=self.path.with_name('profiles.corrupt-'+uuid.uuid4().hex[:8]+'.json');self.path.rename(backup)
                    self.warning+=' The unreadable registry was preserved at '+str(backup)
            except OSError:pass
        self.sessions={}
        for entry in self.entries:
            session=bridge_class(app,entry['id'],self);self.sessions[entry['id']]=session
            session.changed.connect(self.changed.emit)
            session.apiKeyChanged.connect(self.apiKeyChanged.emit)
        self.posted.connect(lambda fn:fn(),Qt.ConnectionType.QueuedConnection)
        if self.warning:self.active.log(self.warning)
    @property
    def active(self):return self.sessions[self.entries[self.current]['id']]
    @property
    def s(self):return self.active.s
    @Property('QVariantMap',notify=changed)
    def state(self):
        values=dict(self.active.s);values['serversRoot']=str(self.servers_root)
        values.update(profileIndex=self.current,profileName=self.entries[self.current]['name'],profileItems=[dict(entry,status=(self.sessions[entry['id']].s['server']+' / '+('Needs approval' if self.sessions[entry['id']].s['dialog'] else self.sessions[entry['id']].s['tunnel'])),tunnel=self.sessions[entry['id']].s['tunnel']) for entry in self.entries],hostingCount=sum(session.active(session.server) for session in self.sessions.values()))
        values['busy']=self.active.s['busy'] or self.exiting;values['exiting']=self.exiting
        if self.exiting:values['activity']='Saving all worlds and closing…'
        return values
    @Property(str,notify=apiKeyChanged)
    def apiKey(self):return self.active.apiKey
    @Property(str,notify=credentialsChanged)
    def sshPassword(self):return self.active.secrets['password']
    @Property(str,notify=credentialsChanged)
    def sshPassphrase(self):return self.active.secrets['passphrase']
    def registry_save(self):
        self.cache.mkdir(parents=True,exist_ok=True);name=None
        try:
            with tempfile.NamedTemporaryFile('w',dir=self.cache,prefix='.profiles-',delete=False) as file:
                name=file.name;json.dump({'profiles':self.entries,'selected':self.entries[self.current]['id'],'servers_root':str(self.servers_root)},file,indent=2);file.flush();os.fsync(file.fileno())
            os.replace(name,self.path)
        finally:
            if name:Path(name).unlink(missing_ok=True)
    @Property(str,notify=storageChanged)
    def serversRoot(self):return str(self.servers_root)
    @Slot(str)
    def setServersRoot(self,value):
        old=self.servers_root
        try:
            if self.exiting:return
            if not value.strip():raise ValueError('Choose a main folder for new servers.')
            root=Path(value).expanduser().resolve()
            if root.exists() and not root.is_dir():raise ValueError('Server storage must be a folder.')
            if (root/'server.properties').exists():raise ValueError('Choose a parent folder, not an existing server folder.')
            for session in self.sessions.values():
                server=Path(session.s['folder']).expanduser().resolve()
                if root==server or server in root.parents:raise ValueError('The main folder cannot be inside an existing server. Choose its parent or a separate folder.')
            self.servers_root=root;self.registry_save();self.storageChanged.emit();self.changed.emit()
            self.active.log('New servers will be created under '+str(root))
        except Exception as e:
            self.servers_root=old;self.storageChanged.emit();self.active.error(e)
    @Slot()
    def chooseServersRoot(self):
        selected=QFileDialog.getExistingDirectory(None,'Choose the main folder for all new servers',str(self.servers_root))
        if selected:self.setServersRoot(selected)
    def editable_selection(self):
        if self.exiting or self.active.s['busy'] or self.active.s['dialog']:raise ValueError('Finish the current operation or confirmation before switching profiles.')
        if not self.active.save():raise ValueError('Save valid profile settings before switching.')
    @Slot(int)
    def selectProfile(self,index):
        try:
            if index==self.current:return
            self.editable_selection()
            if not 0<=index<len(self.entries):return
            self.current=index;self.registry_save();self.apiKeyChanged.emit();self.credentialsChanged.emit();self.changed.emit();self.active.refresh_files()
        except Exception as e:self.active.error(e)
    @Slot(str)
    def addProfile(self,name):
        try:
            self.editable_selection();name=name.strip()
            if not name:raise ValueError('Enter a server profile name.')
            identifier=uuid.uuid4().hex
            used_java={int(s.s['local_java_port']) for s in self.sessions.values()}|{int(s.s['remote_java_port']) for s in self.sessions.values()}
            used_bedrock={int(s.s[k]) for s in self.sessions.values() for k in ('local_bedrock_port','remote_bedrock_port','bedrock_ipv6_port')}
            java=next(p for p in range(25565,65536) if p not in used_java)
            bedrock=next(p for p in range(19132,65535,2) if p not in used_bedrock and p+1 not in used_bedrock)
            from server_locations import new_server_folder
            for existing in self.sessions.values():
                path=Path(existing.s['folder']).expanduser().resolve()
                if self.servers_root==path or path in self.servers_root.parents:raise ValueError('Choose a main servers folder outside existing server folders in Settings.')
            destination=new_server_folder(self.servers_root,name,[s.s['folder'] for s in self.sessions.values()])
            session=self.bridge_class(self.app,identifier,self)
            for key in ('vps_host','ssh_username','ssh_port','join_address','key'):session.s[key]=self.active.s[key]
            session.s.update(folder=str(destination),local_java_port=java,remote_java_port=java,local_bedrock_port=bedrock,remote_bedrock_port=bedrock,bedrock_ipv6_port=bedrock+1)
            session.secrets['apiKey']=self.apiKey
            if not session.save():
                session.timer.stop()
                try:destination.rmdir()
                except OSError:pass
                raise ValueError('Could not save the new server profile. Check folder permissions and disk space.')
            session.changed.connect(self.changed.emit);session.apiKeyChanged.connect(self.apiKeyChanged.emit)
            previous=self.current
            self.sessions[identifier]=session;self.entries.append({'id':identifier,'name':name});self.current=len(self.entries)-1
            try:self.registry_save()
            except Exception:
                self.current=previous;self.entries.pop();self.sessions.pop(identifier);session.timer.stop();session.api_save_timer.stop()
                try:destination.rmdir()
                except OSError:pass
                raise
            self.apiKeyChanged.emit();self.credentialsChanged.emit();self.changed.emit()
        except Exception as e:self.active.error(e)
    @Slot(str)
    def renameProfile(self,name):
        try:
            if not name.strip():raise ValueError('Enter a profile name.')
            self.entries[self.current]['name']=name.strip();self.registry_save();self.changed.emit()
        except Exception as e:self.active.error(e)
    @Slot()
    def removeProfile(self):
        try:
            self.editable_selection();session=self.active;session.stopped()
            if len(self.entries)==1:raise ValueError('Keep at least one server profile.')
            def remove(yes):
                if not yes:return
                identifier=self.entries[self.current]['id'];session.timer.stop();session.api_save_timer.stop()
                self.entries.pop(self.current);self.current=min(self.current,len(self.entries)-1);self.registry_save();self.sessions.pop(identifier)
                self.apiKeyChanged.emit();self.credentialsChanged.emit();self.changed.emit()
            session.confirm('Remove server profile?','This removes the profile from Nova. Its server folder, worlds and backups remain.',remove)
        except Exception as e:self.active.error(e)
    def preflight(self,session,for_tunnel=False):
        from connection_settings import port
        folder=Path(session.s['folder']).expanduser().resolve()
        try:engine=json.loads((folder/'switcher-server.json').read_text()).get('engine','Vanilla')
        except (OSError,ValueError):engine=session.s['engine']
        bedrock=engine=='Bedrock';protocol='UDP' if bedrock else 'TCP'
        local={port(session.s['local_bedrock_port']),port(session.s['bedrock_ipv6_port'])} if bedrock else {port(session.s['local_java_port'])}
        remote=port(session.s['remote_bedrock_port'] if bedrock else session.s['remote_java_port'])
        connection=Connection.parse(session.s) if for_tunnel else None
        for other in self.sessions.values():
            if other is session:continue
            running=other.active(other.server);tunneling=other.active(other.tunnel) or (other.s['busy'] and running)
            if running:
                otherfolder=Path(other.s['folder']).expanduser().resolve()
                if folder==otherfolder or folder in otherfolder.parents or otherfolder in folder.parents:raise ValueError('Another running profile uses this server folder. Choose a separate folder.')
                if bedrock==(other.running_engine=='Bedrock'):
                    occupied={port(other.s['local_bedrock_port']),port(other.s['bedrock_ipv6_port'])} if bedrock else {port(other.s['local_java_port'])}
                    if local & occupied:raise ValueError('Local '+protocol+' port conflicts with another running profile. Choose unique ports in Settings.')
            if for_tunnel and tunneling and (other.running_engine=='Bedrock')==bedrock:
                remote_other=port(other.s['remote_bedrock_port'] if bedrock else other.s['remote_java_port'])
                if Connection.parse(other.s).vps_host==connection.vps_host and remote_other==remote:raise ValueError('That VPS game port is already used by another profile.')
    def assert_editable(self,session):
        folder=Path(session.s['folder']).expanduser().resolve()
        for other in self.sessions.values():
            if other is session or not (other.active(other.server) or other.s['busy']):continue
            otherfolder=Path(other.s['folder']).expanduser().resolve()
            if folder==otherfolder or folder in otherfolder.parents or otherfolder in folder.parents:raise ValueError('Another active profile is using this folder. Stop it before changing files.')
    def vps_ports(self,connection):
        peers=[s for s in self.sessions.values() if s.s['vps_host'] and Connection.parse(s.s).vps_host==connection.vps_host and s.s['ssh_username']==connection.ssh_username]
        return [s.s['remote_java_port'] for s in peers],[s.s['remote_bedrock_port'] for s in peers]
    @Slot(str)
    def restoreBackup(self,path):self.active.restoreBackup(path)
    @Slot(str)
    def action(self,name):
        if name=='exit':self.exit();return
        if name=='tray':self.minimize();return
        if name=='stop_all':self.stopAll();return
        self.active.action(name)
    @Slot(str,'QVariant')
    def update(self,key,value):
        if key=='apiKey':
            for session in self.sessions.values():session.secrets['apiKey']=str(value)
        self.active.update(key,value)
    @Slot(str,str)
    def draft(self,key,value):self.active.draft(key,value)
    @Slot()
    def saveApiKey(self):self.active.saveApiKey()
    @Slot()
    def forgetApiKey(self):
        self.active.forgetApiKey()
        for session in self.sessions.values():session.secrets['apiKey']='';session.api_save_timer.stop()
        self.apiKeyChanged.emit()
    @Slot(bool)
    def agree(self,value):self.active.agree(value)
    @Slot(bool)
    def answer(self,yes):self.active.answer(yes)
    @Slot(str)
    def browse(self,key):self.active.browse(key)
    @Slot(str)
    def command(self,text):self.active.command(text)
    @Slot(str,str)
    def setPath(self,key,value):self.active.setPath(key,value)
    @Slot(str)
    def open_file(self,name):self.active.open_file(name)
    @Slot(str,str)
    def property_value(self,key,value):self.active.property_value(key,value)
    @Slot(str,str,str)
    def addon(self,operation,kind,name):self.active.addon(operation,kind,name)
    @Slot(str,str,str,int)
    def query(self,text,sort,version,offset):self.active.query(text,sort,version,offset)
    @Slot(int,int)
    def project(self,index,offset):self.active.project(index,offset)
    @Slot(str,str)
    def playerAction(self,operation,name):self.active.playerAction(operation,name)
    @Slot()
    def stopAll(self):
        for session in self.sessions.values():session.stop()
    def setup_tray(self):self.bridge_class.setup_tray(self)
    def restore(self):self.window.showNormal();self.window.raise_();self.window.requestActivate()
    def minimize(self):
        for session in self.sessions.values():session.save()
        if self.tray and QSystemTrayIcon.isSystemTrayAvailable():self.window.hide()
        else:self.window.showMinimized()
    def exit(self):
        if self.exiting:return
        dirty=[entry['name'] for entry in self.entries if self.sessions[entry['id']].s['dirty'] or self.sessions[entry['id']].s['propertyDirty']]
        if dirty:self.active.confirm('Discard unsaved changes and exit?',', '.join(dirty)+' have unsaved edits. All servers will save and stop.',lambda yes:self._exit() if yes else None)
        else:self._exit()
    def _exit(self):
        if not all(s.save() for s in self.sessions.values()):return
        for session in self.sessions.values():
            if session.api_save_timer.isActive():session.saveApiKey()
        self.exiting=True;self.restore();self.stopAll()
        for session in self.sessions.values():session.publish(exiting=True,activity='Saving all worlds and closing…')
        from process_manager import cancelled,stop_all,wait_workers
        cancelled.set()
        def finish():
            deadline=time.monotonic()+45
            while any(s.active(s.server) for s in self.sessions.values()) and time.monotonic()<deadline:time.sleep(.1)
            stop_all()
            while not wait_workers(1):pass
            self.posted.emit(self.app.quit)
        threading.Thread(target=finish,daemon=True).start()
