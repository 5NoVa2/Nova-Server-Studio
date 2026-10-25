from bubble_ui import BubbleButton, BubbleNotebook, BubbleCard, Launcher
from process_manager import check_cancelled,start_worker,copy_file
import os
import shutil
import stat
import tempfile
import threading
import uuid
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def validate_server_folder(target):
    target = Path(target).expanduser().resolve()
    home = Path.home().resolve()
    forbidden = [home, Path(target.anchor), home/'Downloads', home/'Desktop', home/'Documents', Path(__file__).resolve().parent]
    if any(target == p or target in p.parents for p in forbidden):
        raise ValueError('Choose a dedicated Minecraft server folder, not a personal or app folder.')
    if target.exists() and not target.is_dir():
        raise ValueError('The server destination must be a folder.')
    if target.exists() and any(p.is_symlink() or (getattr(p.stat(follow_symlinks=False), 'st_file_attributes', 0) & 1024) for p in [target, *target.parents]):
        raise ValueError('Choose a destination without symbolic links or junctions.')
    if target.exists() and any(target.iterdir()):
        markers = ['server.properties','mods','libraries','world','run.bat','start.bat','eula.txt','bedrock_server.exe','worlds']
        if not any((target/m).exists() for m in markers):
            raise ValueError('Nonempty destination does not look like a Minecraft server. Choose a dedicated server folder.')
    return target


def manual_backup(target):
    check_cancelled()
    target = validate_server_folder(target)
    if not target.is_dir() or not any(target.iterdir()):
        raise ValueError('No existing server files to back up.')
    for entry in target.rglob('*'):
        check_cancelled()
        if entry.is_symlink() or (getattr(entry.stat(follow_symlinks=False), 'st_file_attributes', 0) & 1024):
            raise ValueError('Backup does not support symbolic links or junctions inside the server folder.')
    destination = target.with_name(target.name+'.backup-'+uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix='.mc-backup-', dir=target.parent) as temp:
        staged = Path(temp)/'copy'
        shutil.copytree(target, staged,copy_function=copy_file)
        staged.rename(destination)
    return destination


def install(archive, target):
    check_cancelled()
    archive = Path(archive).resolve()
    target = validate_server_folder(target)
    if target == archive or target in archive.parents:
        raise ValueError('The ZIP must be outside the destination folder.')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.mc-stage-', dir=target.parent) as temp:
        stage = Path(temp)/'new'
        stage.mkdir()
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist()) > 30*1024**3:
                raise ValueError('Archive expands beyond the 30 GB limit.')
            for i in z.infolist():
                parts = i.filename.replace('\\','/').split('/')
                if any(p in ('..',) or ':' in p or p.endswith((' ','.')) for p in parts if p) or i.filename.startswith(('/','\\')) or stat.S_ISLNK(i.external_attr >> 16):
                    raise ValueError('Unsafe archive path: '+i.filename)
                out = stage.joinpath(*parts).resolve()
                if stage not in out.parents and out != stage:
                    raise ValueError('Unsafe archive path.')
            for member in z.infolist():
                check_cancelled();z.extract(member,stage)
        entries = list(stage.iterdir())
        while len(entries)==1 and entries[0].is_dir():
            stage = entries[0]
            entries = list(stage.iterdir())
        if not entries:
            raise ValueError('ZIP is empty.')
        if not (stage/'bedrock_server.exe').is_file() and not any(p.suffix.lower() in ('.bat','.sh','.jar') for p in stage.rglob('*')):
            raise ValueError('No server launcher or JAR found. Download the server pack, not a client modpack.')
        check_cancelled()
        previous = None
        if target.exists():
            previous = target.with_name('.mc-replace-'+uuid.uuid4().hex)
            target.rename(previous)
        try:
            stage.rename(target)
        except Exception:
            if previous:
                try:
                    previous.rename(target)
                except OSError as error:
                    raise RuntimeError('Replacement failed; old files preserved at '+str(previous)) from error
            raise
        if previous:
            try:
                shutil.rmtree(previous)
            except OSError as error:
                raise RuntimeError('New server installed, but old-file cleanup failed at '+str(previous)) from error
        return None


class App:
    def __init__(self, root, embedded=False, guard=None, on_busy=None, target_var=None):
        self.root = root
        self.guard=guard or (lambda:True);self.on_busy=on_busy or (lambda value:None)
        from theme import apply_theme
        if not embedded:
            apply_theme(root)
            root.title('Nova | Downloads & server switching')
            root.geometry('740x560')
        self.downloads = Path.home()/'Downloads'
        if os.name == 'nt':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as k:
                    self.downloads = Path(os.path.expandvars(winreg.QueryValueEx(k,'{374DE290-123F-4565-9164-39C4925E467B}')[0]))
            except OSError:
                pass
        f = ttk.Frame(root, padding=20); f.pack(fill='both', expand=True)
        ttk.Label(f,text='Created by Nova',style='Brand.TLabel').pack(anchor='w',pady=(0,5))
        ttk.Label(f,text='Replace your Minecraft server',font=('Segoe UI',18,'bold')).pack(anchor='w')
        ttk.Label(f,text='Choose a server ZIP. Switching replaces everything without an automatic backup.').pack(anchor='w',pady=8)
        self.files = tk.Listbox(f,height=7,bg='#0d1523',fg='#e6edf7',selectbackground='#24574f',selectforeground='#ffffff',relief='flat',borderwidth=0,font=('Segoe UI',10)); self.files.pack(fill='x')
        self.paths = []
        row = ttk.Frame(f); row.pack(fill='x',pady=6)
        BubbleButton(row,text='Refresh Downloads',command=self.refresh).pack(side='left')
        BubbleButton(row,text='Browse ZIP...',command=self.browse).pack(side='left',padx=8)
        ttk.Label(f,text='Optional: direct HTTPS server ZIP download link').pack(anchor='w')
        self.url = ttk.Entry(f); self.url.pack(fill='x',pady=4)
        ttk.Label(f,text='Dedicated server folder (all current contents will be replaced)').pack(anchor='w')
        row = ttk.Frame(f); row.pack(fill='x',pady=4)
        self.target = ttk.Entry(row, textvariable=target_var); self.target.pack(side='left',fill='x',expand=True)
        if target_var is None:self.target.insert(0,str(Path.home()/'MinecraftServer'))
        BubbleButton(row,text='Choose...',command=self.folder).pack(side='right')
        self.button = BubbleButton(f,text='Replace everything (no automatic backup)',command=self.run); self.button.pack(pady=12)
        self.backup_button = BubbleButton(f,text='Back up server now',command=self.backup); self.backup_button.pack(pady=3)
        self.status = tk.StringVar(value='Stop the Minecraft server before replacing it. ZIP scripts are never run automatically.')
        ttk.Label(f,textvariable=self.status,wraplength=690).pack(anchor='w')
        self.refresh()
    def refresh(self):
        self.paths = sorted(self.downloads.glob('*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)
        self.files.delete(0,'end')
        for p in self.paths: self.files.insert('end',p.name)
        if self.paths: self.files.selection_set(0)
    def browse(self):
        p = filedialog.askopenfilename(initialdir=self.downloads,filetypes=[('Server ZIP','*.zip')])
        if p:
            self.paths.append(Path(p)); self.files.insert('end',Path(p).name)
            self.files.selection_clear(0,'end'); self.files.selection_set('end')
    def folder(self):
        p = filedialog.askdirectory()
        if p: self.target.delete(0,'end'); self.target.insert(0,p)
    def backup(self):
        if not self.guard():return
        target = self.target.get().strip()
        if not messagebox.askokcancel('Back up server','Stop the server first, then click OK to copy its files.'):return
        self.on_busy(True)
        self.button.state(['disabled']);self.backup_button.state(['disabled'])
        self.status.set('Copying server files...')
        def finish(result,error=None):
            self.on_busy(False)
            self.button.state(['!disabled']);self.backup_button.state(['!disabled'])
            if error:
                self.status.set('Backup failed: '+str(error));messagebox.showerror('Backup failed',str(error))
            else:
                self.status.set('Backup saved: '+str(result));messagebox.showinfo('Backup saved',str(result))
        def work():
            try:
                result=manual_backup(target)
                self.root.after(0,lambda r=result:finish(r))
            except Exception as e:self.root.after(0,lambda err=e:finish(None,err))
        start_worker(work)
    def run(self):
        if not self.guard():return
        dest = self.target.get().strip(); url = self.url.get().strip()
        selection = self.files.curselection()
        if not dest or (not url and not selection):
            messagebox.showerror('Missing selection','Select a server ZIP and destination folder.'); return
        if url and not url.startswith('https://'):
            messagebox.showerror('Link','Use a direct HTTPS ZIP download link.'); return
        if not messagebox.askyesno('Replace server?',f'Stop your server first.\n\nReplace ALL files in:\n{dest}\n\nNo automatic backup. Old worlds and files will be deleted. Continue?'): return
        source = self.paths[selection[0]] if selection else None
        self.on_busy(True)
        self.button.state(['disabled']); self.backup_button.state(['disabled']); self.status.set('Preparing server files...')
        def finish(error, backup=None):
            self.on_busy(False)
            self.button.state(['!disabled']); self.backup_button.state(['!disabled'])
            if error:
                self.status.set('Replacement failed. '+str(error)); messagebox.showerror('Could not replace',str(error))
            else:
                self.status.set('Ready. New server files installed. No automatic backup was created.')
                messagebox.showinfo('Files ready','Server files installed. Follow the pack instructions and run its supplied launcher. No automatic backup was created.')
        def work():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    archive = source
                    if url:
                        archive = Path(tmp)/'server.zip'
                        with urlopen(Request(url,headers={'User-Agent':'MCServerSwitcher/1.0'}),timeout=60) as response, archive.open('wb') as out:
                            count=0
                            while True:
                                check_cancelled()
                                chunk=response.read(1024*1024)
                                if not chunk: break
                                count+=len(chunk)
                                if count>10*1024**3: raise ValueError('Download exceeds 10 GB.')
                                out.write(chunk)
                    backup = install(archive,dest)
                self.root.after(0,lambda b=backup:finish(None,b))
            except Exception as e:
                self.root.after(0,lambda err=e:finish(err))
        start_worker(work)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
