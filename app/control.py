"""Nova single-window Minecraft server manager with in-process SSH."""
from bubble_ui import BubbleButton, BubbleNotebook, BubbleCard, Launcher, BubbleBadge
from process_manager import managed_popen,start_worker
import base64
import hashlib
import json
import os
import platform
import queue
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import uuid
import webbrowser
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app import install, manual_backup, App as PackApp
from settings_store import SettingsStore
from theme import apply_theme, ACCENT
from runtime import get_json, download, get_java
from engines import setup_engine, available_versions, KINDS
from connection_settings import Connection,DEFAULTS as CONNECTION_DEFAULTS,setup_script

BASE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.cache')))/'MCServerSwitcher'
NO_WINDOW = getattr(subprocess,'CREATE_NO_WINDOW',0)
MANIFEST = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'



def setup_vanilla(target,version,ram,log):
    manifest=get_json(MANIFEST)
    version=manifest['latest']['release'] if version.strip().lower()=='latest' else version.strip()
    entry=next((v for v in manifest['versions'] if v['id']==version and v['type']=='release'),None)
    if not entry: raise ValueError('Version not found. Enter latest or an exact stable release version.')
    log('Downloading Minecraft '+version+' metadata...')
    meta=get_json(entry['url'])
    jar=meta.get('downloads',{}).get('server')
    if not jar: raise ValueError('This Minecraft version has no official server download.')
    major=meta.get('javaVersion',{}).get('majorVersion',8)
    java=get_java(major,log)
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp); log('Downloading and verifying the vanilla server...')
        download(jar['url'],temp/'server.jar','sha1',jar['sha1'])
        (temp/'eula.txt').write_text('eula=true\n')
        (temp/'server.properties').write_text('server-ip=127.0.0.1\nserver-port=25565\nonline-mode=true\nenable-query=false\nenable-rcon=false\nmotd=Nova Minecraft server\n')
        state={'version':version,'java':str(java),'ram':int(ram)}
        (temp/'switcher-server.json').write_text(json.dumps(state,indent=2))
        (temp/'Start-Server.bat').write_text('@echo off\ncd /d "%~dp0"\n"'+str(java)+'" -Xms1G -Xmx'+str(ram)+'G -jar server.jar nogui\npause\n')
        archive=temp/'vanilla.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
            for p in temp.iterdir():
                if p!=archive:z.write(p,p.name)
        install(archive,target)
    log('Installed Minecraft '+version+'. No automatic backup was created.')
    return state




class Control:
    def __init__(self,root):
        self.root=root;self.server=None;self.tunnel=None;self.setup_proc=None;self.busy=False;self.closing=False;self.exit_requested=False;self.tray=None;self.hide_when_tray_ready=False;self.shutdown_worker_done=threading.Event()
        self.events=queue.Queue()
        self.ui_requests=queue.Queue();self.curse_panel=None;self.zip_panel=None;self.settings_panel=None
        self.settings=SettingsStore(CACHE/'settings.json')
        self.save_job=None;self.last_save_error=None
        saved=self.settings.data
        self.cf_selected=saved.get('cf_pack') or None
        self.cf_api_key=os.environ.get('CURSEFORGE_API_KEY','')
        self.version_events=queue.Queue();self.version_request=0
        self.fullscreen=False;self.resume_fullscreen=False;self.startup_pending=False;self.session_start=None;self.last_busy=False
        apply_theme(root)
        from inline_dialogs import install as install_dialogs
        install_dialogs(root)
        top=ttk.Frame(root,padding=(22,12));top.pack(fill='x')
        ttk.Label(top,text='NOVA',style='Logo.TLabel').pack(side='left')
        ttk.Label(top,text='SERVER STUDIO / Created by Nova',style='Muted.TLabel').pack(side='left',padx=18)
        BubbleButton(top,text='Exit Nova',style='Danger.TButton',command=self.exit_app).pack(side='right')
        BubbleButton(top,text='Minimize to tray',command=self.minimize_to_tray).pack(side='right',padx=8)
        self.fullscreen_button=BubbleButton(top,text='Full screen  F11',command=self.toggle_fullscreen);self.fullscreen_button.pack(side='right')
        status=ttk.Frame(root,padding=(22,0,22,10));status.pack(fill='x')
        self.server_status=tk.StringVar(value='SERVER  Stopped');self.tunnel_status=tk.StringVar(value='TUNNEL  Disconnected')
        self.server_badge=BubbleBadge(status,textvariable=self.server_status,style='IdleBadge.TLabel');self.server_badge.pack(side='left',padx=(0,8))
        self.tunnel_badge=BubbleBadge(status,textvariable=self.tunnel_status,style='IdleBadge.TLabel');self.tunnel_badge.pack(side='left',padx=(0,14))
        self.uptime=tk.StringVar(value='Uptime  --');ttk.Label(status,textvariable=self.uptime,style='Muted.TLabel').pack(side='left')
        self.activity=tk.StringVar(value='Ready');ttk.Label(status,textvariable=self.activity,style='Muted.TLabel').pack(side='right',padx=10)
        self.progress=ttk.Progressbar(status,mode='indeterminate',length=100);self.progress.pack(side='right')
        actions=ttk.Frame(root,padding=(22,0,22,12));actions.pack(fill='x');self.actions_panel=actions;self.ui_buttons={}
        for key,label,command,style in [('hosting','Start hosting',self.start_hosting,'Primary.TButton'),('server','Start server',self.start_server,'TButton'),('tunnel','Connect tunnel',self.start_tunnel,'TButton'),('stop','Stop hosting',self.stop_hosting,'Danger.TButton'),('backup','Back up server',self.backup,'TButton')]:
            button=BubbleButton(actions,text=label,command=command,style=style);button.pack(side='left',padx=(0,8));self.ui_buttons[key]=button
        self.join_preview=tk.StringVar(value='Join address');self.join_panel=ttk.Label(root,textvariable=self.join_preview,style='Join.TLabel',padding=(22,6));self.join_panel.pack(fill='x')
        self.navigation=BubbleNotebook(root);self.navigation.pack(fill='both',expand=True)
        self.pages={}
        for name in ('Home','Dashboard','Modpacks','Downloads','Server settings'):
            page=ttk.Frame(self.navigation);self.navigation.add(page,text=name);self.pages[name]=page
        self.launcher=Launcher(self.pages['Home'],[('Control center','cube',self.dashboard),('Modpacks','pack',self.browse_curse),('Server settings','settings',self.open_server_settings),('Start hosting','play',self.start_hosting)])
        self.launcher.pack(fill='both',expand=True)
        root.title('Nova | Minecraft Server Studio')
        screen_height=root.winfo_screenheight()
        root.geometry('1060x'+str(min(870,max(680,screen_height-90))))
        root.minsize(940,650)
        viewport=ttk.Frame(self.pages['Dashboard']);viewport.pack(fill='both',expand=True)
        canvas=tk.Canvas(viewport,background='#08090c',highlightthickness=0)
        page_scroll=ttk.Scrollbar(viewport,command=canvas.yview)
        page_scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        canvas.configure(yscrollcommand=page_scroll.set)
        shell=ttk.Frame(canvas,padding=(26,20))
        page=canvas.create_window((0,0),window=shell,anchor='nw')
        shell.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda event:canvas.itemconfigure(page,width=event.width,height=max(event.height,shell.winfo_reqheight())))
        ttk.Label(shell,text='Control center',style='Title.TLabel').pack(anchor='w',pady=(0,5))
        ttk.Label(shell,text='Prepare your server, connect your VPS, and manage your world.',style='Muted.TLabel').pack(anchor='w',pady=(0,18))

        cards=ttk.Frame(shell);cards.pack(fill='x')
        cards.columnconfigure(0,weight=1,uniform='cards');cards.columnconfigure(1,weight=1,uniform='cards')
        left_surface=BubbleCard(cards,padding=22);left_surface.grid(row=0,column=0,sticky='nsew',padx=(0,8));left=left_surface.content
        right_surface=BubbleCard(cards,padding=22);right_surface.grid(row=0,column=1,sticky='nsew',padx=(8,0));right=right_surface.content
        ttk.Label(left,text='01   Local server',style='Section.TLabel').pack(anchor='w')
        ttk.Label(left,text='Choose your server software and game version',style='CardMuted.TLabel').pack(anchor='w',pady=(3,13))
        engine_row=ttk.Frame(left,style='Card.TFrame');engine_row.pack(fill='x',pady=(0,10))
        self.engine=tk.StringVar(value=saved.get('engine','Vanilla'))
        ttk.Combobox(engine_row,textvariable=self.engine,values=KINDS,state='readonly',width=13).pack(side='left')
        BubbleButton(engine_row,text='Browse CurseForge',command=self.browse_curse).pack(side='right')
        self.cf_label=tk.StringVar(value=(self.cf_selected or {}).get('name','No CurseForge pack selected'))
        ttk.Label(left,textvariable=self.cf_label,style='CardMuted.TLabel',wraplength=400).pack(anchor='w',pady=(0,8))
        ttk.Label(left,text='SERVER FOLDER',style='CardMuted.TLabel').pack(anchor='w')
        row=ttk.Frame(left,style='Card.TFrame');row.pack(fill='x',pady=(5,10))
        self.folder=tk.StringVar(value=saved['folder'])
        ttk.Entry(row,textvariable=self.folder).pack(side='left',fill='x',expand=True,padx=(0,7))
        BubbleButton(row,text='Browse',command=self.choose_folder).pack(side='right')
        row=ttk.Frame(left,style='Card.TFrame');row.pack(fill='x',pady=(0,8))
        version_box=ttk.Frame(row,style='Card.TFrame');version_box.pack(side='left',fill='x',expand=True,padx=(0,12))
        ram_box=ttk.Frame(row,style='Card.TFrame');ram_box.pack(side='left')
        self.version=tk.StringVar(value=saved['version']);self.ram=tk.IntVar(value=saved['ram'])
        ttk.Label(version_box,text='GAME VERSION',style='CardMuted.TLabel').pack(anchor='w')
        self.version_combo=ttk.Combobox(version_box,textvariable=self.version,values=['latest'])
        self.version_combo.pack(fill='x',pady=(5,0))
        self.version_combo.bind('<Button-1>',lambda e:self.refresh_versions() if len(self.version_combo.cget('values'))<=1 else None)
        ttk.Label(ram_box,text='JAVA RAM / GB',style='CardMuted.TLabel').pack(anchor='w')
        ttk.Spinbox(ram_box,from_=2,to=16,textvariable=self.ram,width=7).pack(pady=(5,0))
        loader_row=ttk.Frame(left,style='Card.TFrame');loader_row.pack(fill='x',pady=(0,8))
        ttk.Label(loader_row,text='Forge build',style='CardMuted.TLabel').pack(side='left')
        self.loader=tk.StringVar(value=saved.get('loader','recommended'))
        ttk.Entry(loader_row,textvariable=self.loader,width=17).pack(side='left',padx=8)
        BubbleButton(loader_row,text='Refresh versions',command=self.refresh_versions).pack(side='right')
        self.agreed=tk.BooleanVar(value=False)
        ttk.Checkbutton(left,text='I agree to the Minecraft EULA',variable=self.agreed).pack(anchor='w')
        eula_link=ttk.Label(left,text='Read Minecraft EULA',style='CardMuted.TLabel',cursor='hand2')
        eula_link.pack(anchor='w',pady=(1,8))
        eula_link.bind('<Button-1>',lambda event:webbrowser.open('https://www.minecraft.net/eula'))
        self.install_button=BubbleButton(left,text='Install / switch selected server',style='Primary.TButton',command=self.setup)
        self.install_button.pack(fill='x')
        ttk.Label(left,text='Switching replaces all files. Backups are manual.',style='CardMuted.TLabel').pack(anchor='w',pady=(8,0))

        ttk.Label(right,text='02   VPS connection',style='Section.TLabel').pack(anchor='w')
        ttk.Label(right,text='Ubuntu 24.04  /  Reverse SSH tunnel',style='CardMuted.TLabel').pack(anchor='w',pady=(3,13))
        info=ttk.Frame(right,style='Card.TFrame');info.pack(fill='x',pady=(0,12))
        self.vps_host=tk.StringVar(value=saved['vps_host'])
        self.ssh_username=tk.StringVar(value=saved['ssh_username'])
        self.ssh_port=tk.StringVar(value=str(saved['ssh_port']))
        self.join_address=tk.StringVar(value=saved['join_address'])
        ttk.Label(info,text='VPS HOST / IP',style='CardMuted.TLabel').pack(anchor='w')
        ttk.Entry(info,textvariable=self.vps_host).pack(fill='x',pady=(4,8))
        row=ttk.Frame(info,style='Card.TFrame');row.pack(fill='x')
        user_box=ttk.Frame(row,style='Card.TFrame');user_box.pack(side='left',fill='x',expand=True,padx=(0,10))
        port_box=ttk.Frame(row,style='Card.TFrame');port_box.pack(side='left')
        ttk.Label(user_box,text='SSH USERNAME',style='CardMuted.TLabel').pack(anchor='w')
        ttk.Entry(user_box,textvariable=self.ssh_username).pack(fill='x',pady=(4,8))
        ttk.Label(port_box,text='SSH PORT',style='CardMuted.TLabel').pack(anchor='w')
        ttk.Entry(port_box,textvariable=self.ssh_port,width=7).pack(pady=(4,8))
        ttk.Label(info,text='JOIN ADDRESS / DOMAIN OR IP',style='CardMuted.TLabel').pack(anchor='w')
        row=ttk.Frame(info,style='Card.TFrame');row.pack(fill='x',pady=(4,6))
        ttk.Entry(row,textvariable=self.join_address).pack(side='left',fill='x',expand=True,padx=(0,7))
        BubbleButton(row,text='Copy',command=self.copy_join_address).pack(side='right')
        ttk.Label(info,text='Changes apply on next connection. DNS changes are made\nat your DNS provider. Game ports: Java 25565 / Bedrock 19132.',style='CardMuted.TLabel').pack(anchor='w')
        self.credentials_open=False
        self.credentials_button=BubbleButton(right,text='Show login details',command=self.toggle_credentials);self.credentials_button.pack(fill='x',pady=(0,8))
        self.credentials=ttk.Frame(right,style='Card.TFrame')
        ttk.Label(self.credentials,text='SSH PRIVATE KEY / OPTIONAL',style='CardMuted.TLabel').pack(anchor='w')
        row=ttk.Frame(self.credentials,style='Card.TFrame');row.pack(fill='x',pady=(5,5))
        self.key=tk.StringVar(value=saved['key'])
        ttk.Entry(row,textvariable=self.key).pack(side='left',fill='x',expand=True,padx=(0,7))
        BubbleButton(row,text='Select',command=self.choose_key).pack(side='right')
        ttk.Label(self.credentials,text='SSH password / optional',style='CardMuted.TLabel').pack(anchor='w',pady=(6,3))
        self.password=tk.StringVar()
        ttk.Entry(self.credentials,textvariable=self.password,show='*').pack(fill='x')
        ttk.Label(self.credentials,text='Private key passphrase / optional',style='CardMuted.TLabel').pack(anchor='w',pady=(6,3))
        self.passphrase=tk.StringVar()
        ttk.Entry(self.credentials,textvariable=self.passphrase,show='*').pack(fill='x')
        ttk.Label(self.credentials,text='Credentials stay in memory. SSH runs inside Nova.',style='CardMuted.TLabel').pack(anchor='w',pady=(6,12))



        BubbleButton(right,text='Configure VPS',command=self.configure).pack(fill='x',pady=(6,0))
        ttk.Label(right,text='Configuration requires root or passwordless sudo.',style='CardMuted.TLabel').pack(anchor='w',pady=(8,0))

        self.health=tk.StringVar(value='Server: Stopped | Tunnel: Stopped')

        console_surface=BubbleCard(shell,padding=18);console_surface.pack(fill='both',expand=True,pady=(14,0));console=console_surface.content
        console_head=ttk.Frame(console,style='Card.TFrame');console_head.pack(fill='x',pady=(0,8))
        ttk.Label(console_head,text='LIVE CONSOLE',style='CardMuted.TLabel').pack(side='left')
        BubbleButton(console_head,text='Clear log',command=self.clear_log).pack(side='right')
        self.follow_log=tk.BooleanVar(value=True)
        ttk.Checkbutton(console_head,text='Follow output',variable=self.follow_log).pack(side='right',padx=8)
        terminal=ttk.Frame(console,style='Card.TFrame');terminal.pack(fill='both',expand=True)
        self.output=tk.Text(terminal,height=6,wrap='word',state='disabled',background='#0b0d12',foreground='#bbd0e3',insertbackground=ACCENT,font=('Consolas',10),relief='flat',borderwidth=0,padx=12,pady=10)
        scrollbar=ttk.Scrollbar(terminal,command=self.output.yview)
        scrollbar.pack(side='right',fill='y');self.output.pack(side='left',fill='both',expand=True)
        self.output.configure(yscrollcommand=scrollbar.set)
        command_row=ttk.Frame(shell);command_row.pack(fill='x',pady=(10,0))
        ttk.Label(command_row,text='Console command',style='Muted.TLabel').pack(side='left',padx=(0,10))
        self.command=tk.StringVar()
        command_entry=ttk.Entry(command_row,textvariable=self.command)
        command_entry.pack(side='left',fill='x',expand=True,padx=(0,8))
        command_entry.bind('<Return>',lambda event:self.submit_command())
        BubbleButton(command_row,text='Send',command=self.submit_command).pack(side='right')
        footer=ttk.Frame(shell);footer.pack(fill='x',pady=(12,0))
        for label,cmd in [('Test connection',self.test),('DNS help',self.dns),('Downloads / ZIP',self.pack),('Server settings',self.open_server_settings)]:
            BubbleButton(footer,text=label,command=cmd).pack(side='left',padx=(0,8))
        BubbleButton(footer,text='Save settings',command=lambda:self.save_settings(show=True)).pack(side='right')
        ttk.Label(footer,text='Auto-save enabled',style='Muted.TLabel').pack(side='right',padx=12)
        for variable in (self.folder,self.version,self.ram,self.key,self.engine,self.loader,self.vps_host,self.ssh_username,self.ssh_port,self.join_address):
            variable.trace_add('write',self.schedule_save)
        if self.settings.warning:self.log(self.settings.warning)
        self.log('NOVA / Server Studio ready. Settings restored automatically.')
        self.log('Already installed? Start server, then start tunnel. Switching deletes old files without a backup.')
        self.engine.trace_add('write',self.engine_changed)
        self.refresh_versions()
        self.navigation.bind('<<NotebookTabChanged>>',self.tab_changed)
        root.bind('<F11>',lambda event:self.toggle_fullscreen())
        root.bind('<Escape>',lambda event:self.leave_fullscreen())
        root.bind('<Control-s>',lambda event:self.save_shortcut())
        for variable in (self.join_address,self.vps_host,self.engine):variable.trace_add('write',self.update_join_preview)
        self.update_join_preview()
        self.tab_changed()
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.after(150,self.poll)
        root.after(500,self.start_tray)
    def send_command(self,command):
        if not self.active(self.server):
            messagebox.showinfo('Server stopped','Start the server before sending commands.');return False
        command=command.strip().lstrip('/')
        if not command or '\n' in command or '\r' in command:
            messagebox.showerror('Command','Enter one console command on a single line.');return False
        try:
            self.server.stdin.write(command+'\n');self.server.stdin.flush()
            self.log('> '+command);return True
        except OSError as e:
            self.log('Command failed: '+str(e));return False
    def submit_command(self):
        if self.send_command(self.command.get()):self.command.set('')
    def save_shortcut(self):
        if self.navigation.tab(self.navigation.select(),'text')=='Server settings' and self.settings_panel:
            panel=self.settings_panel
            if panel.tabs.tab(panel.tabs.select(),'text')=='Config files':panel.save_config()
            else:panel.save_properties()
        else:self.save_settings(show=True)
        return 'break'
    def toggle_fullscreen(self):
        self.fullscreen=not self.fullscreen;self.root.attributes('-fullscreen',self.fullscreen)
        self.fullscreen_button.configure(text='Leave full screen  Esc' if self.fullscreen else 'Full screen  F11')
        return 'break'
    def leave_fullscreen(self):
        if self.fullscreen:self.toggle_fullscreen()
        return 'break'
    def toggle_credentials(self):
        self.credentials_open=not self.credentials_open
        if self.credentials_open:self.credentials.pack(fill='x',before=self.credentials_button)
        else:self.credentials.pack_forget()
        self.credentials_button.configure(text='Hide login details' if self.credentials_open else 'Show login details')
    def update_join_preview(self,*_):
        address=self.join_address.get().strip() or self.vps_host.get().strip()
        kind=getattr(self,'running_engine',self.engine.get()) if self.active(self.server) else self.engine.get()
        self.join_preview.set('JOIN  '+address+'   /   '+('Bedrock  19132 UDP' if kind=='Bedrock' else 'Java  25565 TCP'))
    def clear_log(self):
        self.output.configure(state='normal');self.output.delete('1.0','end');self.output.configure(state='disabled')
    def start_hosting(self):
        if self.busy or self.exit_requested or self.startup_pending:return
        if self.active(self.server):self.start_tunnel();return
        self.start_server()
        if not self.active(self.server):return
        self.startup_pending=True;self.startup_deadline=time.monotonic()+300
        self.log('Starting hosting: waiting for server readiness...');self.root.after(300,self.finish_hosting_start)
    def finish_hosting_start(self):
        if not self.startup_pending or self.exit_requested:return
        if not self.active(self.server):self.startup_pending=False;self.log('Server stopped before hosting could start.');return
        if self.server_ready.is_set():self.startup_pending=False;self.start_tunnel();return
        if time.monotonic()>self.startup_deadline:
            self.startup_pending=False;self.log('Readiness was not detected. Review the log and use Connect tunnel when ready.');return
        self.root.after(300,self.finish_hosting_start)
    def stop_hosting(self):
        self.startup_pending=False;self.stop_tunnel();self.stop_server()
    def connection(self):
        data={}
        for key in CONNECTION_DEFAULTS:
            variable=getattr(self,key,None)
            data[key]=variable.get() if variable is not None else self.settings.data.get(key,CONNECTION_DEFAULTS[key])
        return Connection.parse(data)
    def copy_join_address(self):
        try:
            value=self.connection().join_address
            self.root.clipboard_clear();self.root.clipboard_append(value)
            self.log('Copied join address: '+value)
        except ValueError as error:messagebox.showerror('Join address',str(error))
    def tab_changed(self,event=None):
        name=self.navigation.tab(self.navigation.select(),'text')
        if name=='Home':
            self.launcher.started=time.monotonic();self.actions_panel.pack_forget();self.join_panel.pack_forget();self.navigation.bar.pack_forget()
        else:
            self.actions_panel.pack(fill='x',before=self.navigation);self.join_panel.pack(fill='x',before=self.navigation)
            self.navigation.bar.pack(fill='x',before=self.navigation.body)
        if name=='Modpacks' and self.curse_panel is None:self.browse_curse()
        elif name=='Downloads' and self.zip_panel is None:self.pack()
        elif name=='Server settings':self.open_server_settings()
    def dashboard(self):self.navigation.select(self.pages['Dashboard'])
    def open_server_settings(self):
        if self.busy:
            self.dashboard();messagebox.showinfo('Working','Wait for the current operation to finish.');return
        try:
            from server_settings_ui import ServerSettings
            folder=Path(self.folder.get()).expanduser().resolve()
            if self.settings_panel is not None and self.settings_panel.files.root!=folder:
                panel=self.settings_panel
                if (panel.property_dirty() or panel.editor_dirty()) and not messagebox.askyesno('Unsaved edits','Discard unsaved settings from the previous folder?'):
                    self.dashboard();return
                panel.window.destroy();self.settings_panel=None
            if self.settings_panel is not None:
                from server_files import ServerFiles
                panel=self.settings_panel
                if not panel.property_dirty() and not panel.editor_dirty():
                    current=ServerFiles(folder)
                    if current.state!=panel.files.state:
                        panel.window.destroy();self.settings_panel=None
            if self.settings_panel is None:
                self.settings_panel=ServerSettings(self.pages['Server settings'],str(folder),lambda:self.active(self.server),self.send_command,self.stop_server,self.log,embedded=True,on_close=self.dashboard)
            if self.navigation.select()!=str(self.pages['Server settings']):self.navigation.select(self.pages['Server settings'])
        except Exception as e:self.dashboard();messagebox.showerror('Server settings',str(e))
    def post_ui(self,function):
        self.ui_requests.put((function,threading.Event(),{}))
    def ui_call(self,function):
        done=threading.Event();result={}
        self.ui_requests.put((function,done,result))
        while not done.wait(.2):
            if self.closing or self.exit_requested:raise ValueError('App is closing.')
        if 'error' in result:raise result['error']
        return result.get('value')
    def approve_host(self,host,fingerprint):
        if self.exit_requested:return False
        self.post_ui(self.restore_window)
        return self.ui_call(lambda:messagebox.askyesno('Verify VPS identity',host+'\n\n'+fingerprint+'\n\nCompare this SSH fingerprint with your VPS provider console. Trust this host and remember its key?'))
    def engine_changed(self,*_):
        self.version.set('latest')
        if self.engine.get()=='Bedrock':self.log('Bedrock selected: latest official stable release, UDP 19132, native executable; Java mods and RAM controls do not apply.')
        self.refresh_versions()
    def refresh_versions(self):
        kind=self.engine.get();self.version_request+=1;request=self.version_request
        if kind=='CurseForge':
            self.version_combo.configure(state='disabled')
            self.log('CurseForge uses the Minecraft version from the selected pack release.');return
        self.version_combo.configure(state='normal')
        def work():
            try:
                versions=available_versions(kind)
                self.version_events.put((request,kind,versions,None))
            except Exception as e:self.version_events.put((request,kind,[],str(e)))
        threading.Thread(target=work,daemon=True).start()
    def browse_curse(self):
        if self.curse_panel is None:
            from curse_browser import CurseBrowser
            def picked(item,key):
                self.cf_selected=item;self.cf_api_key=key
                self.engine.set('CurseForge');self.cf_label.set(item['name']+' / '+item['release'])
                self.save_settings();self.log('Selected CurseForge pack: '+item['name']+' / '+item['release'])
            self.curse_panel=CurseBrowser(self.pages['Modpacks'],picked,self.cf_api_key,embedded=True,on_close=self.dashboard)
        if self.navigation.select()!=str(self.pages['Modpacks']):self.navigation.select(self.pages['Modpacks'])
    def schedule_save(self,*_):
        if self.save_job is not None:self.root.after_cancel(self.save_job)
        self.save_job=self.root.after(350,self.save_settings)
    def save_settings(self,show=False):
        if self.save_job is not None:
            self.root.after_cancel(self.save_job);self.save_job=None
        try:
            ram=int(self.ram.get())
            if not 2<=ram<=16:raise ValueError('RAM must be between 2 and 16 GB.')
        except (ValueError,tk.TclError):
            ram=self.settings.data['ram']
        data={'folder':self.folder.get(),'version':self.version.get(),'ram':ram,'key':self.key.get(),'engine':self.engine.get(),'loader':self.loader.get(),'cf_pack':self.cf_selected or {}}
        try:data.update(self.connection().as_dict())
        except (ValueError,UnicodeError) as error:
            if show:
                messagebox.showerror('Connection settings',str(error));return False
            data.update({key:self.settings.data[key] for key in CONNECTION_DEFAULTS})
        try:
            self.settings.save(data)
            self.last_save_error=None
            if show:self.log('Settings saved. They will restore next time you open the app.')
            return True
        except OSError as e:
            if str(e)!=self.last_save_error or show:self.log('Could not save settings: '+str(e))
            self.last_save_error=str(e)
            if show:messagebox.showerror('Settings not saved',str(e))
            return False
    def active(self,p):return p is not None and p.poll() is None
    def log(self,text):self.events.put(('log',str(text)))
    def poll(self):
        while True:
            try:function,done,result=self.ui_requests.get_nowait()
            except queue.Empty:break
            try:result['value']=function()
            except Exception as e:result['error']=e
            finally:done.set()
        while True:
            try:request,kind,versions,error=self.version_events.get_nowait()
            except queue.Empty:break
            if request!=self.version_request:continue
            if error:self.log('Could not fetch versions; you can type one manually. '+error)
            else:
                self.version_combo.configure(values=['latest',*versions])
                self.log(f'{kind}: loaded {len(versions)} Minecraft versions.'+(' BuildTools checks Spigot support during setup.' if kind=='Spigot' else ''))
        while True:
            try:kind,text=self.events.get_nowait()
            except queue.Empty:break
            if kind=='tunnel':self.tunnel=text;continue
            if kind=='done':
                self.busy=False;self.install_button.state(['!disabled'])
            else:
                self.output.configure(state='normal');self.output.insert('end',text+'\n')
                if self.follow_log.get():self.output.see('end')
                if int(self.output.index('end-1c').split('.')[0])>4000:self.output.delete('1.0','500.0')
                self.output.configure(state='disabled')
        s='Running' if self.active(self.server) else 'Stopped'
        t='Connected' if self.active(self.tunnel) else 'Stopped'
        self.health.set(f'Server: {s}   |   Tunnel: {t}')
        server_running=self.active(self.server);tunnel_running=self.active(self.tunnel)
        ready=server_running and getattr(self,'server_ready',threading.Event()).is_set()
        self.server_status.set('SERVER  '+('Ready' if ready else 'Starting' if server_running else 'Stopped'))
        self.tunnel_status.set('TUNNEL  '+('Connected' if tunnel_running else 'Disconnected'))
        self.server_badge.configure(style='OnlineBadge.TLabel' if ready else 'BusyBadge.TLabel' if server_running else 'IdleBadge.TLabel')
        self.tunnel_badge.configure(style='OnlineBadge.TLabel' if tunnel_running else 'IdleBadge.TLabel')
        elapsed=int(time.monotonic()-self.session_start) if server_running and self.session_start else 0
        self.uptime.set('Uptime  '+('%02d:%02d:%02d'%(elapsed//3600,elapsed//60%60,elapsed%60) if server_running else '--'))
        working=self.busy or self.startup_pending or self.exit_requested
        self.activity.set('Shutting down...' if self.exit_requested else 'Loading server...' if self.startup_pending else 'Working...' if self.busy else 'Ready')
        if working!=self.last_busy:
            self.progress.start(12) if working else self.progress.stop();self.last_busy=working
        states={'hosting':working or (server_running and tunnel_running),'server':working or server_running,'tunnel':working or not server_running or tunnel_running,'stop':self.exit_requested or not (server_running or tunnel_running),'backup':working or server_running or tunnel_running}
        for key,disabled in states.items():self.ui_buttons[key].state(['disabled'] if disabled else ['!disabled'])
        self.update_join_preview()
        if not self.closing:self.root.after(150,self.poll)
    def choose_folder(self):
        if self.busy or self.active(self.server):return
        p=filedialog.askdirectory()
        if p:self.folder.set(p)
    def choose_key(self):
        p=filedialog.askopenfilename(title='Select your local SSH private key (never uploaded)')
        if p:self.key.set(p)
    def task(self,fn):
        if self.exit_requested:return
        if self.busy:messagebox.showinfo('Working','Wait for the current operation to finish.');return
        self.busy=True;self.install_button.state(['disabled'])
        def work():
            try:fn()
            except Exception as e:self.log('ERROR: '+str(e))
            finally:self.events.put(('done',''))
        start_worker(work)
    def setup(self):
        if self.busy:return
        if self.active(self.server) or self.active(self.tunnel):
            messagebox.showerror('Stop first','Stop the server and tunnel before replacement.');return
        if not self.agreed.get():messagebox.showerror('EULA','Read and agree to the Minecraft EULA first.');return
        try:
            ram=4 if self.engine.get()=='Bedrock' else int(self.ram.get());assert 2<=ram<=16
        except Exception:messagebox.showerror('RAM','Choose 2 to 16 GB.');return
        target=self.folder.get().strip();version=self.version.get().strip()
        if not target or not version:return
        if not messagebox.askyesno('Replace everything?',f'Replace ALL files in:\n{target}\n\nNo automatic backup. Old worlds and files will be deleted. Stop any server you started outside this app first.'):return
        kind=self.engine.get();loader=self.loader.get();selection=self.cf_selected;key=self.cf_api_key
        if kind=='CurseForge' and (not selection or not key):
            messagebox.showinfo('Select a pack','Click Browse CurseForge, enter your API key and choose a release.');return
        self.task(lambda:setup_engine(kind,target,version,loader,ram,self.log,selection,key))
    def backup(self):
        if self.busy:return
        if self.active(self.server) or self.active(self.tunnel):
            messagebox.showinfo('Stop first','Stop the server and tunnel before making a consistent backup.');return
        target=self.folder.get().strip()
        if not messagebox.askokcancel('Manual backup','Stop any server started outside the app first. Click OK to copy the selected server folder.'):return
        def work():
            self.log('Copying server files...')
            destination=manual_backup(target)
            self.log('Manual backup saved: '+str(destination))
        self.task(work)
    def configure(self):
        if self.busy:return
        if self.active(self.tunnel):messagebox.showinfo('Stop tunnel first','Stop the current tunnel before configuring a VPS.');return
        try:connection=self.connection()
        except (ValueError,UnicodeError) as error:messagebox.showerror('VPS settings',str(error));return
        key=self.key.get();password=self.password.get();passphrase=self.passphrase.get()
        def work():
            from ssh_backend import connect,configure
            client=connect(key,password,passphrase,self.approve_host,self.log,host=connection.vps_host,username=connection.ssh_username,port=connection.ssh_port)
            script=setup_script((BASE/'vps_setup.sh').read_text(encoding='utf-8'),connection.ssh_username)
            configure(client,script,self.log,use_sudo=connection.ssh_username!='root')
        self.task(work)
    def start_server(self):
        if self.busy:return
        if self.active(self.server):return
        try:
            folder=Path(self.folder.get()).expanduser().resolve()
            state=json.loads((folder/'switcher-server.json').read_text())
            if 'eula=true' not in (folder/'eula.txt').read_text().splitlines():raise ValueError('Minecraft EULA is not accepted.')
            if state.get('engine')=='Bedrock':
                executable=folder/'bedrock_server.exe'
                if not executable.is_file():raise ValueError('Bedrock executable is missing. Install Bedrock first.')
                command=[str(executable)]
                self.log('Starting Bedrock on UDP 19132. Java RAM controls do not apply.')
            else:
                ram=int(self.ram.get())
                if not 2<=ram<=16:raise ValueError('Choose 2 to 16 GB RAM.')
                java=Path(state['java']).resolve()
                if CACHE.resolve() not in java.parents or java.name.lower()!='java.exe':raise ValueError('Unexpected Java path. Select the correct server folder or reinstall the selected server type.')
                args=state.get('args',['-jar','server.jar','nogui'])
                if not isinstance(args,list) or not all(isinstance(a,str) for a in args):raise ValueError('Invalid server launch metadata.')
                command=[str(java),'-Xms1G',f'-Xmx{ram}G',*args]
            self.running_engine=state.get('engine','Vanilla')
            self.server_ready=threading.Event();self.session_start=time.monotonic()
            self.server=managed_popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,creationflags=NO_WINDOW)
            proc=self.server;ready_event=self.server_ready
            def read():
                for line in proc.stdout:
                    if 'Done (' in line or 'Server started' in line:ready_event.set()
                    self.log(line.rstrip())
                proc.wait();self.log('Server exited with code '+str(proc.returncode))
            threading.Thread(target=read,daemon=True).start()
        except Exception as e:messagebox.showerror('Start server',str(e))
    def start_tunnel(self):
        if self.busy or self.active(self.tunnel):return
        if not self.active(self.server):messagebox.showerror('Start server first','Start the local server before the tunnel.');return
        try:connection=self.connection()
        except (ValueError,UnicodeError) as error:messagebox.showerror('VPS settings',str(error));return
        key=self.key.get();password=self.password.get();passphrase=self.passphrase.get()
        def work():
            from ssh_backend import connect,ReverseTunnel
            client=connect(key,password,passphrase,self.approve_host,self.log,host=connection.vps_host,username=connection.ssh_username,port=connection.ssh_port)
            if getattr(self,'running_engine','Vanilla')=='Bedrock':
                from bedrock import BedrockTunnel
                tunnel=BedrockTunnel(client,self.log)
            else:tunnel=ReverseTunnel(client,self.log)
            self.events.put(('tunnel',tunnel))
        self.task(work)
    def stop_tunnel(self):
        if self.active(self.tunnel):self.tunnel.terminate();self.log('Tunnel stopped.')
    def stop_server(self):
        self.startup_pending=False
        if self.active(self.server):
            try:self.server.stdin.write('stop\n');self.server.stdin.flush();self.log('Saving world and stopping. Wait for Server: Stopped.')
            except OSError as e:self.log(str(e))
    def test(self):
        try:connection=self.connection()
        except (ValueError,UnicodeError) as error:messagebox.showerror('Connection settings',str(error));return
        try:state=json.loads((Path(self.folder.get())/'switcher-server.json').read_text())
        except (OSError,ValueError):state={}
        bedrock=state.get('engine')=='Bedrock'
        def run():
            for host in dict.fromkeys(['127.0.0.1',connection.vps_host,connection.join_address]):
                try:
                    if bedrock:
                        from bedrock import probe
                        address,status=probe(host)
                        self.log(host+' -> '+address+': Bedrock UDP status reply: '+status)
                    else:
                        addresses=sorted(set(i[4][0] for i in socket.getaddrinfo(host,25565,type=socket.SOCK_STREAM)))
                        with socket.create_connection((host,25565),timeout=6):pass
                        self.log(host+' resolves to '+', '.join(addresses)+': TCP 25565 reachable. Confirm Minecraft by joining with the installed game version.')
                except (OSError,ValueError) as e:self.log(host+': '+('Bedrock UDP' if bedrock else 'TCP')+' test failed: '+str(e))
        self.task(run)
    def dns(self):
        try:connection=self.connection()
        except (ValueError,UnicodeError) as error:messagebox.showerror('Connection settings',str(error));return
        import ipaddress
        try:
            address=ipaddress.ip_address(connection.join_address)
            text='Your join address is already an IP; no DNS record is needed.'
        except ValueError:
            text='Create or edit an A record for '+connection.join_address+' pointing to the public IPv4 address of your VPS: '+connection.vps_host+'. Use @ for a root domain, or the corresponding subdomain name. On IONOS, use Domains & SSL > your domain > DNS. TTL 1 hour is fine. If using Cloudflare, select DNS only.'
        text+='\n\nChanging this field does not change DNS automatically.\nJava: TCP 25565. Bedrock: UDP 19132. Allow the correct game port in your VPS firewall. Run Configure VPS once on each new Ubuntu 24.04 VPS. Root or passwordless sudo is required for configuration.'
        messagebox.showinfo('Join address / DNS',text)
    def zip_guard(self):
        if self.busy or self.active(self.server) or self.active(self.tunnel):
            messagebox.showinfo('Stop first','Stop the server and tunnel and wait for current work to finish.');return False
        return True
    def zip_busy(self,value):
        self.busy=value
        self.install_button.state(['disabled'] if value else ['!disabled'])
    def pack(self):
        if self.zip_panel is None:
            self.zip_panel=PackApp(self.pages['Downloads'],embedded=True,guard=self.zip_guard,on_busy=self.zip_busy,target_var=self.folder)
        if self.navigation.select()!=str(self.pages['Downloads']):self.navigation.select(self.pages['Downloads'])
    def start_tray(self):
        if self.exit_requested:return
        from tray_support import Tray
        self.tray=Tray(self.post_ui,self.restore_window,self.exit_app,self.log,on_ready=self.tray_ready)
        self.tray.start()
    def tray_ready(self):
        if self.hide_when_tray_ready and not self.exit_requested and self.root.state()=='iconic':
            self.root.withdraw();self.hide_when_tray_ready=False
    def restore_window(self):
        if self.closing:return
        self.hide_when_tray_ready=False
        self.root.deiconify();self.root.state('normal');self.root.lift()
        self.root.focus_force()
        if getattr(self,'resume_fullscreen',False):self.resume_fullscreen=False;self.toggle_fullscreen()
    def minimize_to_tray(self):
        if self.exit_requested:return
        self.save_settings()
        if getattr(self,'fullscreen',False):self.resume_fullscreen=True;self.leave_fullscreen()
        if self.tray is not None and self.tray.ready.is_set():
            self.root.withdraw()
            self.log('Nova minimized to the notification area. Server and tunnel remain running.')
        else:
            self.hide_when_tray_ready=True
            self.root.iconify()
            self.log('Tray is not ready; Nova is minimized to the taskbar. Hosting continues.')
    def close(self):
        # X hides the interface; it never stops Python, the server or the tunnel.
        self.minimize_to_tray()
    def exit_app(self):
        if self.exit_requested:return
        self.restore_window()
        if self.settings_panel and (self.settings_panel.property_dirty() or self.settings_panel.editor_dirty()):
            if not messagebox.askyesno('Unsaved server settings','Discard unsaved server-file edits and exit Nova?'):return
        if not self.save_settings(show=True):return
        self.exit_requested=True
        self.log('Exiting Nova: stopping tunnel and saving the server world...')
        self.root.title('Nova | Saving world and shutting down...')
        from process_manager import cancelled,stop_all,wait_workers
        cancelled.set()
        self.stop_tunnel()
        if self.active(self.server):self.stop_server()
        def shutdown():
            deadline=time.monotonic()+45
            while self.active(self.server) and time.monotonic()<deadline:time.sleep(.1)
            if self.active(self.server):self.log('Server did not stop within 45 seconds; ending its managed process tree.')
            stop_all()
            while not wait_workers(10):self.log('Waiting for canceled file operations to finish safely...')
            self.shutdown_worker_done.set()
        threading.Thread(target=shutdown,daemon=True).start()
        self.root.after(100,self.finish_exit)
    def finish_exit(self):
        if not self.shutdown_worker_done.is_set():
            self.root.after(100,self.finish_exit);return
        if self.tray:self.tray.stop()
        self.password.set('');self.passphrase.set('');self.closing=True;self.root.destroy()

if __name__=='__main__':
    root=tk.Tk();Control(root);root.mainloop()
