from bubble_ui import BubbleButton, BubbleNotebook, BubbleCard, Launcher
import base64
import io
import math
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
import webbrowser
from engines import CurseAPI
from curse_catalog import SORTS,relevant,release_mods,thumbnail
from theme import apply_theme


class CurseBrowser:
    def __init__(self,parent,on_pick,key='',embedded=False,on_close=None):
        self.embedded=embedded;self.on_close=on_close;self.on_pick=on_pick
        if embedded:self.window=ttk.Frame(parent);self.window.pack(fill='both',expand=True)
        else:
            self.window=tk.Toplevel(parent);self.window.title('Nova | Discover modpacks');self.window.geometry('1100x800');apply_theme(self.window)
        self.results=[];self.releases=[];self.project=None;self.file_index=0;self.index=0;self.context=None
        self.busy=False;self.closed=False;self.queue=queue.Queue();self.image_requests=queue.Queue();self.image_results=queue.Queue();self.photos={};self.pack_token=0;self.mod_token=0;self.mod_rows=[]
        for _ in range(4):threading.Thread(target=self.image_worker,daemon=True).start()
        f=ttk.Frame(self.window,padding=18);f.pack(fill='both',expand=True)
        header=ttk.Frame(f);header.pack(fill='x')
        ttk.Label(header,text='Discover modpacks',style='Title.TLabel').pack(side='left')
        ttk.Label(header,text='CURSEFORGE  /  Created by Nova',style='Brand.TLabel').pack(side='right')
        row=ttk.Frame(f);row.pack(fill='x',pady=(12,8))
        ttk.Label(row,text='API key').pack(side='left');self.key=tk.StringVar(value=key or os.environ.get('CURSEFORGE_API_KEY',''))
        ttk.Entry(row,textvariable=self.key,show='*',width=30).pack(side='left',fill='x',expand=True,padx=8)
        BubbleButton(row,text='Load popular',command=self.popular).pack(side='left',padx=(0,8))
        BubbleButton(row,text='API access',command=lambda:webbrowser.open('https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key')).pack(side='right')
        row=ttk.Frame(f);row.pack(fill='x',pady=(0,10))
        self.search_text=tk.StringVar();entry=ttk.Entry(row,textvariable=self.search_text);entry.pack(side='left',fill='x',expand=True,padx=(0,8));entry.bind('<Return>',lambda e:self.search())
        self.sort=tk.StringVar(value='Popular');sort=ttk.Combobox(row,textvariable=self.sort,values=['Popular','Relevant','Recently updated','Most downloaded'],state='readonly',width=18);sort.pack(side='left',padx=(0,8));sort.bind('<<ComboboxSelected>>',lambda e:self.search())
        ttk.Label(row,text='MC version').pack(side='left');self.game_version=tk.StringVar();ttk.Entry(row,textvariable=self.game_version,width=10).pack(side='left',padx=8)
        BubbleButton(row,text='Search',style='Primary.TButton',command=self.search).pack(side='right')
        body=ttk.Panedwindow(f,orient='horizontal');body.pack(fill='both',expand=True)
        left=ttk.Frame(body);right=ttk.Frame(body,style='Card.TFrame',padding=14);body.add(left,weight=3);body.add(right,weight=2)
        listing=ttk.Frame(left);listing.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(listing,columns=('name','downloads'),show='tree headings',style='Catalog.Treeview',selectmode='browse')
        self.tree.heading('#0',text='');self.tree.column('#0',width=76,stretch=False);self.tree.heading('name',text='Modpack');self.tree.column('name',width=270);self.tree.heading('downloads',text='Downloads');self.tree.column('downloads',width=95,stretch=False)
        scroll=ttk.Scrollbar(listing,command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set);self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.load_files)
        row=ttk.Frame(left);row.pack(fill='x',pady=10)
        BubbleButton(row,text='Previous',command=lambda:self.search(-20)).pack(side='left');BubbleButton(row,text='Next',command=lambda:self.search(20)).pack(side='left',padx=8)
        self.page_info=tk.StringVar(value='Enter your API key, then load popular packs.');ttk.Label(row,textvariable=self.page_info,style='Muted.TLabel').pack(side='left',padx=8)
        self.cover=ttk.Label(right,text='Select a modpack',style='CardMuted.TLabel',anchor='center');self.cover.pack(fill='x',pady=(0,10))
        self.title=tk.StringVar(value='Find your next world');ttk.Label(right,textvariable=self.title,style='Section.TLabel',wraplength=390).pack(anchor='w')
        self.summary=tk.StringVar(value='Browse popular packs, search by name, and inspect the mods in a release before installing.');ttk.Label(right,textvariable=self.summary,style='CardMuted.TLabel',wraplength=390).pack(anchor='w',pady=8)
        self.author=tk.StringVar();ttk.Label(right,textvariable=self.author,style='CardMuted.TLabel',wraplength=390).pack(anchor='w')
        self.release=ttk.Combobox(right,state='readonly');self.release.pack(fill='x',pady=(12,8));self.release.bind('<<ComboboxSelected>>',self.release_changed)
        row=ttk.Frame(right,style='Card.TFrame');row.pack(fill='x')
        BubbleButton(row,text='Older releases',command=self.more_releases).pack(side='left');BubbleButton(row,text='Pack website',command=self.open_page).pack(side='right')
        BubbleButton(right,text='View release mod list',command=self.load_mods).pack(fill='x',pady=8)
        self.mod_filter=tk.StringVar();mod_search=ttk.Entry(right,textvariable=self.mod_filter);mod_search.pack(fill='x',pady=(0,6));self.mod_filter.trace_add('write',lambda *_:self.render_mods())
        mod_frame=ttk.Frame(right,style='Card.TFrame');mod_frame.pack(fill='both',expand=True)
        self.mods=ttk.Treeview(mod_frame,columns=('name','file'),show='tree headings',style='ModCatalog.Treeview',height=4)
        self.mods.column('#0',width=56,stretch=False);self.mods.heading('#0',text='');self.mods.column('name',width=220);self.mods.heading('name',text='Mod / filter above');self.mods.column('file',width=75,stretch=False);self.mods.heading('file',text='File ID')
        scroll=ttk.Scrollbar(mod_frame,command=self.mods.yview);scroll.pack(side='right',fill='y');self.mods.configure(yscrollcommand=scroll.set);self.mods.pack(fill='both',expand=True);self.mods.bind('<Double-1>',self.open_mod);self.mods.bind('<<TreeviewSelect>>',self.mod_details)
        self.mod_info=tk.StringVar(value='Mod list uses the selected client release manifest.');ttk.Label(right,textvariable=self.mod_info,style='CardMuted.TLabel',wraplength=390).pack(anchor='w',pady=8)
        self.pick_button=BubbleButton(right,text='Use selected pack release',style='Primary.TButton',command=self.pick);self.pick_button.pack(fill='x')
        self.status=tk.StringVar(value='Ready. API key stays in memory only.');ttk.Label(f,textvariable=self.status,style='Muted.TLabel',wraplength=980).pack(anchor='w',pady=(8,0))
        if not embedded:self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.after(100,self.poll)
        if self.key.get():self.window.after(200,self.popular)
    def close(self):
        if self.embedded:
            if self.on_close:self.on_close()
        else:self.closed=True;self.window.destroy()
    def image_worker(self):
        while not self.closed:
            request=self.image_requests.get()
            if request is None:return
            kind,token,item,url=request
            if (kind=='pack' and token!=self.pack_token) or (kind=='mod' and token!=self.mod_token):continue
            try:self.image_results.put((kind,token,item,thumbnail(url)))
            except Exception:pass
    def photo(self,data,size):
        try:
            from PIL import Image,ImageTk
            image=Image.open(io.BytesIO(data))
            if image.width*image.height>10000000:raise ValueError('Image dimensions too large.')
            image.thumbnail((size,size));return ImageTk.PhotoImage(image,master=self.window)
        except ImportError:
            image=tk.PhotoImage(master=self.window,data=base64.b64encode(data))
            return image.subsample(max(1,math.ceil(image.width()/size)),max(1,math.ceil(image.height()/size)))
    def poll(self):
        while True:
            try:done,value,error=self.queue.get_nowait()
            except queue.Empty:break
            self.busy=False
            if error:self.status.set(str(error))
            else:done(value)
        for _ in range(12):
            try:kind,token,item,data=self.image_results.get_nowait()
            except queue.Empty:break
            try:
                if kind=='pack' and token==self.pack_token and self.tree.exists(item):
                    image=self.photo(data,64);self.photos[('pack',item)]=image;self.tree.item(item,image=image)
                    if self.tree.selection()==(item,):self.set_cover(data)
                elif kind=='mod' and token==self.mod_token and self.mods.exists(item):
                    image=self.photo(data,44);self.photos[('mod',item)]=image;self.mods.item(item,image=image)
            except Exception:pass
        self.pick_button.state(['disabled'] if self.busy or self.selected_release() is None or not self.selected_release().get('serverPackFileId') else ['!disabled'])
        if not self.closed:self.window.after(100,self.poll)
    def set_cover(self,data):
        image=self.photo(data,110);self.photos['cover']=image;self.cover.configure(image=image,text='')
    def task(self,work,done):
        if self.busy:return
        self.busy=True;self.status.set('Loading...')
        def run():
            try:self.queue.put((done,work(),None))
            except Exception as error:self.queue.put((done,None,error))
        threading.Thread(target=run,daemon=True).start()
    def popular(self):
        if self.busy:return
        self.sort.set('Popular');self.search_text.set('');self.search()
    def search(self,delta=0):
        if self.busy:return
        try:api=CurseAPI(self.key.get())
        except ValueError as error:self.status.set(str(error));return
        query=self.search_text.get().strip();sort=self.sort.get();version=self.game_version.get().strip();context=(query,sort,version)
        self.index=max(0,self.index+delta) if delta and context==self.context else 0;self.context=context
        self.project=None;self.releases=[];self.release.set('');self.release.configure(values=[]);self.release_changed()
        def done(value):
            self.results=relevant(value['data'],query) if sort=='Relevant' else value['data']
            self.pack_token+=1;self.tree.delete(*self.tree.get_children());self.photos={}
            self.cover.configure(image='',text='Select a modpack')
            for i,pack in enumerate(self.results):
                item=str(i);self.tree.insert('','end',iid=item,values=(pack['name'],f"{pack.get('downloadCount',0):,}"))
                url=(pack.get('logo') or {}).get('thumbnailUrl','')
                if url:self.image_requests.put(('pack',self.pack_token,item,url))
            total=value.get('pagination',{}).get('totalCount','?');self.page_info.set(f'{self.index+1}–{self.index+len(self.results)} / {total}')
            self.status.set('Relevant ranks name matches within this result page.' if sort=='Relevant' else 'Select a pack to see releases and its mod list.')
        self.task(lambda:api.search(query,self.index,SORTS.get(sort,2),version),done)
    def selected_release(self):
        index=self.release.current()
        return self.releases[index] if self.project is not None and 0<=index<len(self.releases) else None
    def release_changed(self,event=None):
        self.mod_token+=1;self.mod_rows=[]
        self.photos={key:value for key,value in self.photos.items() if not (isinstance(key,tuple) and key[0]=='mod')}
        self.mods.delete(*self.mods.get_children());self.mod_info.set('Click View release mod list. Client-only mods may be excluded from the server pack.')
    def fill_releases(self):
        self.release.configure(values=[r.get('displayName',r['fileName'])+' | Server: '+('Yes' if r.get('serverPackFileId') else 'No') for r in self.releases])
    def load_files(self,event=None):
        if self.busy:return
        selected=self.tree.selection()
        if not selected:return
        try:api=CurseAPI(self.key.get())
        except ValueError as error:self.status.set(str(error));return
        pack=self.results[int(selected[0])];self.project=None;self.releases=[];self.release.set('');self.release_changed()
        self.title.set(pack['name']);self.summary.set(pack.get('summary',''));self.author.set('By '+', '.join(a['name'] for a in pack.get('authors',[])))
        image=self.photos.get(('pack',selected[0]))
        self.cover.configure(image=image or '',text='' if image else 'Loading artwork...')
        def done(value):
            if self.tree.selection()!=selected:self.load_files();return
            self.project=pack;self.file_index=len(value['data']);self.releases=[r for r in value['data'] if not r.get('isServerPack')];self.fill_releases()
            if self.releases:self.release.current(next((i for i,r in enumerate(self.releases) if r.get('serverPackFileId')),0))
            self.status.set('Choose a server-capable release. View its mod list or use it for installation.')
        self.task(lambda:api.files(pack['id']),done)
    def more_releases(self):
        if self.busy or self.project is None:return
        project=self.project;index=self.file_index;api=CurseAPI(self.key.get())
        def done(value):
            self.file_index+=len(value['data']);self.releases.extend(r for r in value['data'] if not r.get('isServerPack'));self.fill_releases()
            self.status.set('Older releases loaded.' if value['data'] else 'No older releases available.')
        self.task(lambda:api.files(project['id'],index),done)
    def load_mods(self):
        if self.busy:return
        release=self.selected_release()
        if release is None:return
        project=self.project;api=CurseAPI(self.key.get());token=(project['id'],release['id'])
        def done(rows):
            current=self.selected_release()
            if current is None or (self.project['id'],current['id'])!=token:return
            self.mod_rows=rows;self.mod_token+=1;self.render_mods()
            self.mod_info.set(str(len(rows))+' mods from the selected client manifest. Double-click a mod to open its page.')
            self.status.set('Release mod list loaded. File IDs identify the exact published mod files.')
        self.task(lambda:release_mods(api,project['id'],release['id']),done)
    def render_mods(self):
        self.mods.delete(*self.mods.get_children())
        query=self.mod_filter.get().casefold().strip()
        for i,row in enumerate(self.mod_rows):
            if query and query not in (row['name']+' '+row['authors']).casefold():continue
            item=str(i);self.mods.insert('','end',iid=item,values=(row['name'],row['file_id']))
            image=self.photos.get(('mod',item))
            if image:self.mods.item(item,image=image)
            elif row['logo']:self.image_requests.put(('mod',self.mod_token,item,row['logo']))
    def open_page(self):
        selected=self.tree.selection()
        if selected:
            url=self.results[int(selected[0])].get('links',{}).get('websiteUrl','')
            if url.startswith('https://www.curseforge.com/'):webbrowser.open(url)
    def mod_details(self,event=None):
        selected=self.mods.selection()
        if selected:
            row=self.mod_rows[int(selected[0])]
            self.mod_info.set(row['name']+' / '+(row['authors'] or 'Author unavailable')+' / '+('Required' if row['required'] else 'Optional')+' / File '+str(row['file_id']))
    def open_mod(self,event=None):
        selected=self.mods.selection()
        if selected:
            url=self.mod_rows[int(selected[0])]['url']
            if url.startswith('https://www.curseforge.com/'):webbrowser.open(url)
    def pick(self):
        release=self.selected_release()
        if self.busy or release is None:return
        if not release.get('serverPackFileId'):messagebox.showerror('No server pack','Choose a release with a published server pack.');return
        self.on_pick({'project_id':self.project['id'],'file_id':release['id'],'name':self.project['name'],'release':release.get('displayName',release['fileName'])},self.key.get());self.close()
