from bubble_ui import BubbleButton, BubbleNotebook, BubbleCard, Launcher
import re
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from server_files import ServerFiles,Properties
from theme import apply_theme

# key, label, type/options, displayed default, numeric bounds
GENERAL=[('motd','Server description / MOTD','text','A Minecraft Server',None),('max-players','Maximum players','number','20',(1,10000)),('view-distance','View distance / chunks','number','10',(3,32)),('simulation-distance','Simulation distance / chunks','number','10',(3,32)),('spawn-protection','Spawn protection / blocks','number','16',(0,100000)),('player-idle-timeout','Idle kick / minutes (0 = off)','number','0',(0,100000)),('white-list','Enable whitelist','bool','false',None),('enforce-whitelist','Enforce whitelist immediately','bool','false',None)]
GAMEPLAY=[('gamemode','Default game mode',('survival','creative','adventure','spectator'),'survival',None),('difficulty','Difficulty',('peaceful','easy','normal','hard'),'easy',None),('pvp','Player versus player','bool','true',None),('allow-flight','Allow flight','bool','false',None),('force-gamemode','Force default game mode','bool','false',None),('hardcore','Hardcore mode','bool','false',None),('spawn-monsters','Spawn monsters','bool','true',None),('spawn-animals','Spawn animals','bool','true',None),('spawn-npcs','Spawn villagers / NPCs','bool','true',None),('enable-command-block','Command blocks','bool','false',None)]
WORLD=[('level-name','World folder name','text','world',None),('level-seed','Seed (new worlds only)','text','',None),('level-type','World type','text','minecraft:normal',None),('generator-settings','Generator settings / JSON','text','{}',None),('generate-structures','Generate structures','bool','true',None),('allow-nether','Allow Nether','bool','true',None),('max-world-size','Maximum world radius','number','29999984',(1,29999984))]

BEDROCK_GENERAL=[('server-name','Server name','text','Dedicated Server',None),('max-players','Maximum players','number','10',(1,10000)),('view-distance','View distance / chunks','number','32',(5,96)),('tick-distance','Tick distance / chunks','number','4',(4,12)),('player-idle-timeout','Idle kick / minutes','number','30',(0,100000)),('allow-list','Enable allowlist','bool','false',None)]
BEDROCK_GAMEPLAY=[('gamemode','Default game mode',('survival','creative','adventure'),'survival',None),('difficulty','Difficulty',('peaceful','easy','normal','hard'),'easy',None),('allow-cheats','Allow cheats','bool','false',None),('force-gamemode','Force default game mode','bool','false',None),('default-player-permission-level','Default permission',('visitor','member','operator'),'member',None)]
BEDROCK_WORLD=[('level-name','World name / worlds folder','text','Bedrock level',None),('level-seed','Seed (new worlds only)','text','',None),('texturepack-required','Require resource packs','bool','false',None)]


class ServerSettings:
    def __init__(self,parent,folder,is_running,send_command,stop_server,log,embedded=False,on_close=None):
        self.files=ServerFiles(folder);self.is_running=is_running;self.send_command=send_command;self.stop_server=stop_server;self.log=log
        self.bedrock=self.files.state.get('engine')=='Bedrock'
        self.specs=(BEDROCK_GENERAL,BEDROCK_GAMEPLAY,BEDROCK_WORLD) if self.bedrock else (GENERAL,GAMEPLAY,WORLD)
        self.doc=Properties(self.files.path('server.properties'));self.variables={};self.initial={};self.current_file=None;self.file_hash=None;self.encoding='utf-8';self.loaded_text='';self.loaded_paths=[]
        self.status=tk.StringVar(value='Loaded existing configuration. Unknown settings and comments are preserved.')
        self.embedded=embedded;self.on_close=on_close
        if embedded:
            self.window=ttk.Frame(parent);self.window.pack(fill='both',expand=True)
        else:
            self.window=tk.Toplevel(parent);apply_theme(self.window);self.window.title('Nova | Server settings');self.window.geometry('990x760');self.window.minsize(860,650)
        shell=ttk.Frame(self.window,padding=18);shell.pack(fill='both',expand=True)
        header=ttk.Frame(shell);header.pack(fill='x')
        title=ttk.Frame(header);title.pack(side='left')
        ttk.Label(title,text='Server settings',style='Title.TLabel').pack(anchor='w')
        ttk.Label(title,text=str(self.files.root),style='Muted.TLabel').pack(anchor='w')
        BubbleButton(header,text='Stop server',command=self.stop_server).pack(side='right')
        ttk.Label(shell,text='Created by Nova  /  Stop the server to edit files or add-ons. Settings apply on the next start.',style='Muted.TLabel').pack(anchor='w',pady=(8,12))
        self.tabs=BubbleNotebook(shell);self.tabs.pack(fill='both',expand=True)
        for name,spec in zip(('General','Gameplay','World'),self.specs):
            panel=ttk.Frame(self.tabs,padding=18);self.tabs.add(panel,text=name)
            panel.columnconfigure(1,weight=1)
            for i,(key,label,kind,default,bounds) in enumerate(spec):
                value=self.doc.values.get(key,default);variable=tk.StringVar(value=value);self.variables[key]=variable;self.initial[key]=value
                ttk.Label(panel,text=label).grid(row=i,column=0,sticky='w',padx=(0,20),pady=6)
                if kind=='bool':widget=ttk.Checkbutton(panel,variable=variable,onvalue='true',offvalue='false')
                elif isinstance(kind,tuple):widget=ttk.Combobox(panel,textvariable=variable,values=kind,state='readonly')
                elif kind=='number':widget=ttk.Spinbox(panel,textvariable=variable,from_=bounds[0],to=bounds[1])
                else:widget=ttk.Entry(panel,textvariable=variable)
                widget.grid(row=i,column=1,sticky='ew',pady=6)
            note='Bedrock tunnel uses UDP 19132; Xbox Live authentication remains enabled.' if self.bedrock else 'Network is managed by the tunnel: 127.0.0.1:25565, online-mode enabled.'
            if name=='World':note='Seed/generation changes apply to newly generated worlds. Changing the folder selects a different world; it does not reset or convert the existing one.'
            ttk.Label(panel,text=note,wraplength=810,style='Muted.TLabel').grid(row=len(spec),column=0,columnspan=2,sticky='w',pady=15)
        self.addon_tab=ttk.Frame(self.tabs,padding=16);self.tabs.add(self.addon_tab,text='Mods / plugins');self.build_addons()
        self.editor_tab=ttk.Frame(self.tabs,padding=16);self.tabs.add(self.editor_tab,text='Config files');self.build_editor()
        self.players_tab=ttk.Frame(self.tabs,padding=18);self.tabs.add(self.players_tab,text='Players');self.build_players()
        bottom=ttk.Frame(shell);bottom.pack(fill='x',pady=(12,0))
        BubbleButton(bottom,text='Reload properties',command=self.reload_properties).pack(side='left')
        BubbleButton(bottom,text='Save server properties',style='Primary.TButton',command=self.save_properties).pack(side='right')
        ttk.Label(shell,textvariable=self.status,wraplength=930,style='Muted.TLabel').pack(anchor='w',pady=(10,0))
        if not embedded:self.window.protocol('WM_DELETE_WINDOW',self.close)
    def can_edit(self):
        if self.is_running():messagebox.showinfo('Stop server first','Stop the server and wait for it to exit before editing files.');return False
        return True
    def error(self,error):self.status.set(str(error));messagebox.showerror('Server settings',str(error))
    def property_dirty(self):return any(v.get()!=self.initial[k] for k,v in self.variables.items())
    def editor_dirty(self):return self.current_file is not None and self.editor.get('1.0','end-1c')!=self.loaded_text
    def close(self):
        if (self.property_dirty() or self.editor_dirty()) and not messagebox.askyesno('Unsaved edits','Discard unsaved edits and close?'):return
        if self.embedded:
            if self.on_close:self.on_close()
        else:self.window.destroy()
    def reload_properties(self):
        if self.property_dirty() and not messagebox.askyesno('Reload','Discard unsaved property changes?'):return
        try:
            self.doc=Properties(self.files.path('server.properties'))
            for key,label,kind,default,bounds in sum(self.specs,[]):
                value=self.doc.values.get(key,default);self.variables[key].set(value);self.initial[key]=value
            self.status.set('Properties reloaded.')
        except Exception as e:self.error(e)
    def save_properties(self):
        if not self.can_edit():return
        try:
            updates={key:v.get() for key,v in self.variables.items() if v.get()!=self.initial[key]}
            for key,label,kind,default,bounds in sum(self.specs,[]):
                if key not in updates:continue
                value=updates[key]
                if kind=='number':
                    n=int(value)
                    if not bounds[0]<=n<=bounds[1]:raise ValueError(f'{label}: choose {bounds[0]} to {bounds[1]}.')
                    updates[key]=str(n)
                if key=='level-name' and (not value.strip() or value in ('.','..') or any(c in value for c in '/\\:')):
                    raise ValueError('World folder must be a simple folder name inside the server folder.')
                if key=='server-name' and ';' in value:raise ValueError('Bedrock server name cannot contain a semicolon.')
                if key=='generator-settings':
                    import json
                    json.loads(value)
            self.doc.save(updates)
            for key,v in self.variables.items():self.initial[key]=v.get()
            self.status.set('Server properties saved. Start the server to apply them.');self.log('Server properties saved.')
        except Exception as e:self.error(e)
    def build_addons(self):
        if self.bedrock:
            ttk.Label(self.addon_tab,text='Bedrock uses behavior and resource packs',style='Section.TLabel').pack(anchor='w')
            ttk.Label(self.addon_tab,text='Java JAR mods and Bukkit plugins do not run on Bedrock. This version does not import Bedrock pack archives. Generated allowlist, permissions and world pack-list JSON files can be edited under Config files.',style='Muted.TLabel',wraplength=820).pack(anchor='w',pady=14)
            return
        row=ttk.Frame(self.addon_tab);row.pack(fill='x')
        engine=self.files.state.get('engine','Vanilla')
        self.kind=tk.StringVar(value='plugins' if engine in ('Paper','Spigot') else 'mods')
        select=ttk.Combobox(row,textvariable=self.kind,values=['mods','plugins'],state='readonly',width=12);select.pack(side='left');select.bind('<<ComboboxSelected>>',lambda e:self.refresh_addons())
        ttk.Label(row,text='Installed engine: '+engine,style='Muted.TLabel').pack(side='left',padx=12)
        BubbleButton(row,text='Refresh',command=self.refresh_addons).pack(side='right')
        self.addons=ttk.Treeview(self.addon_tab,columns=('name','state'),show='headings',height=12)
        self.addons.heading('name',text='JAR file');self.addons.heading('state',text='State');self.addons.column('name',width=650);self.addons.column('state',width=120)
        self.addons.pack(fill='both',expand=True,pady=12)
        row=ttk.Frame(self.addon_tab);row.pack(fill='x')
        for label,action in [('Add JAR files',self.add_jars),('Enable / disable',self.toggle_jar),('Remove selected',self.remove_jar)]:BubbleButton(row,text=label,command=action).pack(side='left',padx=(0,10))
        ttk.Label(self.addon_tab,text='Use files matching your Minecraft version and loader. Disabling renames .jar to .jar.disabled. Modpack clients may need the same changes.',style='Muted.TLabel',wraplength=840).pack(anchor='w',pady=14)
        self.refresh_addons()
    def refresh_addons(self):
        if self.bedrock:return
        try:
            self.addons.delete(*self.addons.get_children())
            for name in self.files.addons(self.kind.get()):self.addons.insert('','end',iid=name,values=(name,'Disabled' if name.endswith('.disabled') else 'Enabled'))
        except Exception as e:self.error(e)
    def add_jars(self):
        if not self.can_edit():return
        paths=filedialog.askopenfilenames(title='Select mod/plugin JARs',filetypes=[('Java archives','*.jar')])
        try:
            for source in paths:
                name=Path(source).name;existing=name in self.files.addons(self.kind.get())
                if existing and not messagebox.askyesno('Replace JAR?',f'Replace {name}?'):continue
                self.files.add(self.kind.get(),source,overwrite=existing)
            self.refresh_addons();self.status.set('Add-ons updated. Restart to apply changes.')
        except Exception as e:self.refresh_addons();self.error(e)
    def selected_addon(self):
        selection=self.addons.selection()
        if not selection:raise ValueError('Select a JAR first.')
        return selection[0]
    def toggle_jar(self):
        if not self.can_edit():return
        try:self.files.toggle(self.kind.get(),self.selected_addon());self.refresh_addons()
        except Exception as e:self.error(e)
    def remove_jar(self):
        if not self.can_edit():return
        try:
            name=self.selected_addon()
            if messagebox.askyesno('Remove add-on?',f'Delete {name}? Its configuration files will remain.'):
                self.files.remove(self.kind.get(),name);self.refresh_addons()
        except Exception as e:self.error(e)
    def build_editor(self):
        row=ttk.Frame(self.editor_tab);row.pack(fill='x')
        self.config_name=tk.StringVar()
        self.config_combo=ttk.Combobox(row,textvariable=self.config_name,state='readonly');self.config_combo.pack(side='left',fill='x',expand=True,padx=(0,8))
        BubbleButton(row,text='Open',command=self.open_config).pack(side='left')
        BubbleButton(row,text='Refresh list',command=self.refresh_configs).pack(side='left',padx=8)
        BubbleButton(row,text='Save file',style='Primary.TButton',command=self.save_config).pack(side='right')
        frame=ttk.Frame(self.editor_tab);frame.pack(fill='both',expand=True,pady=12)
        self.editor=tk.Text(frame,background='#090f19',foreground='#d6e3f0',insertbackground='#60e3c2',font=('Consolas',10),undo=True,wrap='none',borderwidth=0,padx=12,pady=10)
        sy=ttk.Scrollbar(frame,command=self.editor.yview);sy.pack(side='right',fill='y')
        sx=ttk.Scrollbar(frame,orient='horizontal',command=self.editor.xview);sx.pack(side='bottom',fill='x')
        self.editor.pack(fill='both',expand=True);self.editor.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        ttk.Label(self.editor_tab,text='Edit generated config, defaultconfigs, plugin settings and world/serverconfig files. JSON is validated; TOML is validated on Python 3.11+. YAML and other formats require correct syntax.',style='Muted.TLabel',wraplength=840).pack(anchor='w')
        self.refresh_configs()
    def refresh_configs(self):
        try:
            self.loaded_paths=self.files.config_files();self.config_combo.configure(values=self.loaded_paths)
            if not self.config_name.get() and self.loaded_paths:self.config_name.set(self.loaded_paths[0])
        except Exception as e:self.error(e)
    def open_config(self):
        if self.editor_dirty() and not messagebox.askyesno('Unsaved edits','Discard current file edits?'):return
        try:
            relative=self.config_name.get();text,token,encoding=self.files.read_config(relative)
            self.current_file=relative;self.file_hash=token;self.encoding=encoding;self.loaded_text=text
            self.editor.delete('1.0','end');self.editor.insert('1.0',text);self.editor.edit_reset()
            self.status.set('Editing '+relative)
        except Exception as e:self.error(e)
    def save_config(self):
        if not self.can_edit():return
        if self.current_file is None:return
        try:
            text=self.editor.get('1.0','end-1c')
            self.file_hash=self.files.write_config(self.current_file,text,self.file_hash,self.encoding)
            actual,token,encoding=self.files.read_config(self.current_file)
            self.loaded_text=actual;self.editor.delete('1.0','end');self.editor.insert('1.0',actual)
            self.status.set('Saved '+self.current_file+'. Restart to apply.')
            self.log('Configuration saved: '+self.current_file)
        except Exception as e:self.error(e)
    def build_players(self):
        ttk.Label(self.players_tab,text='Player commands',style='Section.TLabel').pack(anchor='w')
        ttk.Label(self.players_tab,text='These commands require the server to be running. Results appear in the main console.',style='Muted.TLabel').pack(anchor='w',pady=12)
        row=ttk.Frame(self.players_tab);row.pack(fill='x')
        ttk.Label(row,text='Minecraft username').pack(side='left')
        self.player=tk.StringVar();ttk.Entry(row,textvariable=self.player,width=28).pack(side='left',padx=12)
        groups=[[('Allowlist add','allowlist add'),('Allowlist remove','allowlist remove')],[('Give operator','op'),('Remove operator','deop')],[('Kick player','kick')]] if self.bedrock else [[('Whitelist add','whitelist add'),('Whitelist remove','whitelist remove')],[('Give operator','op'),('Remove operator','deop')],[('Ban player','ban'),('Unban player','pardon'),('Kick player','kick')]]
        for group in groups:
            row=ttk.Frame(self.players_tab);row.pack(fill='x',pady=(14,0))
            for label,command in group:BubbleButton(row,text=label,command=lambda c=command:self.player_command(c)).pack(side='left',padx=(0,10))
        BubbleButton(self.players_tab,text='List online players',command=lambda:self.send_command('list')).pack(anchor='w',pady=20)
    def player_command(self,command):
        name=self.player.get().strip()
        if self.bedrock:
            if not 1<=len(name)<=32 or any(c in name for c in '\r\n\\"'):messagebox.showerror('Gamertag','Enter a valid Xbox gamertag.');return
            name='"'+name+'"'
        elif not re.fullmatch(r'[A-Za-z0-9_]{1,16}',name):messagebox.showerror('Username','Enter a valid Minecraft username.');return
        self.send_command(command+' '+name)
