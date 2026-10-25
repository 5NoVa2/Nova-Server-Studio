"""Rounded controls, eased transitions and a native animated launcher surface."""
import math
import random
import time
import tkinter as tk
from tkinter import ttk,font as tkfont

BG='#08090c';CARD='#111318';TEXT='#eef0f5';MUTED='#868b98'
FONT='Segoe UI';DISPLAY_FONT='Segoe UI Light'


def ease(value):return 1-(1-max(0,min(1,value)))**3


def mix(a,b,t):
    t=max(0,min(1,t))
    return '#'+''.join(f'{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02x}' for i in (1,3,5))


def parent_color(parent):
    try:return parent.cget('background')
    except tk.TclError:
        try:return ttk.Style(parent).lookup(parent.cget('style') or 'TFrame','background') or BG
        except tk.TclError:return BG


def rounded(canvas,x1,y1,x2,y2,r,**kwargs):
    r=max(0,min(r,(x2-x1)/2,(y2-y1)/2))
    points=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
    return canvas.create_polygon(points,smooth=True,splinesteps=20,**kwargs)


class BubbleButton(tk.Canvas):
    def __init__(self,parent,text='',command=None,style='TButton',width=None,**kwargs):
        self.text=text;self.command=command;self.style=style;self.enabled=True;self.hovered=False;self.pressed=False;self._job=None
        self.face=self.target_color();self._font=tkfont.Font(parent,font=(FONT,10,'bold' if 'Primary' in style else 'normal'))
        desired=max(70,self._font.measure(text)+30) if width is None else max(70,int(width)*8)
        super().__init__(parent,width=desired,height=42,background=parent_color(parent),highlightthickness=0,borderwidth=0,cursor='hand2',takefocus=1)
        self.bind('<Configure>',lambda event:self.draw());self.bind('<Enter>',lambda e:self.hover(True));self.bind('<Leave>',lambda e:self.hover(False))
        self.bind('<ButtonPress-1>',self.press);self.bind('<ButtonRelease-1>',self.release)
        self.bind('<Return>',lambda e:self.invoke());self.bind('<space>',lambda e:self.invoke())
        self.bind('<FocusIn>',lambda e:self.draw());self.bind('<FocusOut>',lambda e:self.draw())
        self.draw()
    def target_color(self):
        if not self.enabled:return '#14161c'
        if 'Primary' in self.style:return '#ffffff' if self.hovered else '#d9deea'
        if 'Danger' in self.style:return '#4c2731' if self.hovered else '#281c24'
        return '#343844' if self.hovered else '#1a1d25'
    def draw(self):
        if not self.winfo_exists():return
        self.delete('surface');w=max(self.winfo_width(),int(super().cget('width')) if self.winfo_width()<2 else 1);h=max(self.winfo_height(),42)
        inset=3 if self.pressed else 1
        rounded(self,inset,3,w-inset,h-1,20,fill='#030407',outline='',tags='surface')
        border='#747b8e' if self.hovered or self.focus_get()==self else '#333742'
        rounded(self,inset,inset,w-inset,h-4,20,fill=self.face,outline=border,width=1,tags='surface')
        fg=('#0e1016' if 'Primary' in self.style else '#f2c6ce' if 'Danger' in self.style else TEXT) if self.enabled else '#626774'
        self.create_text(w/2,h/2-1+(1 if self.pressed else 0),text=self.text,font=self._font,fill=fg,tags='surface')
    def animate(self):
        if self._job is not None:self.after_cancel(self._job)
        start=self.face;target=self.target_color();began=time.monotonic()
        def tick():
            t=min(1,(time.monotonic()-began)/.16);self.face=mix(start,target,ease(t));self.draw()
            self._job=self.after(16,tick) if t<1 else None
        tick()
    def hover(self,value):self.hovered=value;self.animate()
    def press(self,event):
        if self.enabled:self.focus_set();self.pressed=True;self.draw()
    def release(self,event):
        pressed=self.pressed;self.pressed=False;self.draw()
        if pressed and self.enabled and 0<=event.x<=self.winfo_width() and 0<=event.y<=self.winfo_height():self.invoke()
    def invoke(self):
        if self.enabled and self.command:return self.command()
    def state(self,spec=None):
        if spec is None:return () if self.enabled else ('disabled',)
        previous=self.enabled
        if 'disabled' in spec:self.enabled=False
        if '!disabled' in spec:self.enabled=True
        if previous!=self.enabled:
            super().configure(cursor='hand2' if self.enabled else 'arrow');self.animate()
        return ()
    def configure(self,cnf=None,**kwargs):
        if cnf:kwargs.update(cnf)
        changed=False
        for key in ('text','command','style'):
            if key in kwargs:setattr(self,key,kwargs.pop(key));changed=True
        if 'state' in kwargs:self.state(['disabled'] if kwargs.pop('state')=='disabled' else ['!disabled'])
        result=super().configure(**kwargs) if kwargs else None
        if changed:
            super().configure(width=max(70,self._font.measure(self.text)+30));self.animate()
        return result
    config=configure
    def destroy(self):
        if self._job is not None:
            try:self.after_cancel(self._job)
            except tk.TclError:pass
        super().destroy()


class BubbleCard(tk.Frame):
    def __init__(self,parent,padding=20,**kwargs):
        super().__init__(parent,background=parent_color(parent),borderwidth=0,**kwargs)
        self.surface=tk.Canvas(self,highlightthickness=0,borderwidth=0,background=parent_color(parent));self.surface.place(relwidth=1,relheight=1)
        self.content=ttk.Frame(self,style='Card.TFrame');self.content.pack(fill='both',expand=True,padx=padding,pady=padding)
        self.surface.bind('<Configure>',self.draw)
        self.tk.call('lower',self.surface._w)
    def draw(self,event=None):
        c=self.surface;c.delete('all');w=c.winfo_width();h=c.winfo_height()
        rounded(c,2,6,w-2,h-1,25,fill='#030407',outline='')
        rounded(c,1,1,w-4,h-5,24,fill=CARD,outline='#2d3039',width=1)


class BubbleNotebook(ttk.Frame):
    """Notebook-compatible page navigation with rounded pills and eased reveals."""
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs);self.pages=[];self.selected=None;self.job=None
        self.bar=ttk.Frame(self,padding=(18,8));self.bar.pack(fill='x')
        self.body=ttk.Frame(self);self.body.pack(fill='both',expand=True)
    def add(self,child,text='',**kwargs):
        button=BubbleButton(self.bar,text=text,command=lambda:self.select(child));button.pack(side='left',padx=(0,7))
        self.pages.append((child,text,button))
        if self.selected is None:self.select(child,animate=False)
    def select(self,tab_id=None,animate=True):
        if tab_id is None:return str(self.selected) if self.selected is not None else ''
        target=self.resolve(tab_id)
        if target is self.selected:return str(target)
        if self.job is not None:self.after_cancel(self.job);self.job=None
        if self.selected is not None:self.selected.place_forget()
        self.selected=target
        for child,text,button in self.pages:button.configure(style='Primary.TButton' if child is target else 'TButton')
        offset=22 if animate else 0;began=time.monotonic()
        target.place(in_=self.body,x=offset,y=0,relwidth=1,width=-offset,relheight=1);target.lift()
        def step():
            t=min(1,(time.monotonic()-began)/.26);x=round(offset*(1-ease(t)))
            if target is not self.selected:return
            target.place_configure(x=x,width=-x)
            self.job=self.after(16,step) if t<1 else None
        if animate:step()
        self.event_generate('<<NotebookTabChanged>>',when='tail')
        return str(target)
    def resolve(self,tab_id):
        if isinstance(tab_id,int):return self.pages[tab_id][0]
        for child,text,button in self.pages:
            if tab_id is child or str(tab_id)==str(child):return child
        raise tk.TclError('Unknown Saturn page')
    def tab(self,tab_id,option=None,**kwargs):
        child=self.resolve(tab_id);text=next(text for page,text,button in self.pages if page is child)
        return text if option=='text' else {'text':text}
    def destroy(self):
        if self.job is not None:
            try:self.after_cancel(self.job)
            except tk.TclError:pass
        super().destroy()


class Launcher(tk.Canvas):
    """Original Saturn artwork and motion, inspired by the supplied visual reference."""
    def __init__(self,parent,actions,**kwargs):
        super().__init__(parent,background=BG,highlightthickness=0,borderwidth=0,**kwargs)
        self.actions=actions;self.levels=[0.0]*len(actions);self.hover=-1;self.started=time.monotonic();self.job=None;self.pointer=(.5,.5)
        rng=random.Random(12);self.stars=[(rng.random(),rng.random(),rng.uniform(.4,1.3),rng.random()*6.28) for _ in range(58)]
        self.bind('<Motion>',self.motion);self.bind('<Leave>',lambda e:setattr(self,'hover',-1));self.bind('<ButtonRelease-1>',self.activate)
        self.bind('<Configure>',lambda e:self.draw());self.tick()
    def motion(self,event):
        w=max(1,self.winfo_width());h=max(1,self.winfo_height());self.pointer=(event.x/w,event.y/h)
        self.hover=next((i for i,box in enumerate(self.boxes()) if box[0]<=event.x<=box[2] and box[1]<=event.y<=box[3]),-1)
        self.configure(cursor='hand2' if self.hover>=0 else 'arrow')
    def boxes(self):
        w=max(1,self.winfo_width());h=max(1,self.winfo_height());size=min(156,max(116,(w-160)/4-16));total=size*4+16*3;x=(w-total)/2;y=max(154,h*.43)
        return [(x+i*(size+16),y,x+i*(size+16)+size,y+size) for i in range(4)]
    def activate(self,event):
        for i,box in enumerate(self.boxes()):
            if box[0]<=event.x<=box[2] and box[1]<=event.y<=box[3]:self.actions[i][2]();break
    def icon(self,kind,x,y,color,tag):
        kw={'fill':color,'width':2,'tags':tag}
        if kind=='cube':
            self.create_polygon(x,y-24,x+25,y-11,x+25,y+18,x,y+32,x-25,y+18,x-25,y-11,fill='',outline=color,width=2,tags=tag)
            self.create_line(x-25,y-11,x,y+3,x+25,y-11,**kw);self.create_line(x,y+3,x,y+32,**kw);self.create_line(x,y-24,x+25,y-11,**kw)
        elif kind=='pack':
            for dx,dy in [(-17,-17),(12,-17),(-17,12),(12,12)]:rounded(self,x+dx,y+dy,x+dx+21,y+dy+21,5,fill='',outline=color,width=2,tags=tag)
        elif kind=='settings':
            for dy,offset in [(-18,-12),(0,13),(18,-4)]:
                self.create_line(x-26,y+dy,x+26,y+dy,**kw);self.create_oval(x+offset-5,y+dy-5,x+offset+5,y+dy+5,fill=CARD,outline=color,width=2,tags=tag)
        else:
            self.create_polygon(x-14,y-25,x+26,y,x-14,y+25,fill=color,outline='',tags=tag)
    def draw(self):
        if not self.winfo_exists():return
        self.delete('scene');w=max(1,self.winfo_width());h=max(1,self.winfo_height());t=time.monotonic()-self.started
        for x,y,r,phase in self.stars:
            px=x*w+math.sin(t*.11+phase)*7+(self.pointer[0]-.5)*8;py=(y*h-t*(1+r))%max(h,1)
            color=mix('#171a22','#565d6c',(.5+.5*math.sin(t*.4+phase))*.5)
            self.create_oval(px-r,py-r,px+r,py+r,fill=color,outline='',tags='scene')
        for i in range(7):
            x=w*(.07+i*.14)+math.sin(t*.12+i)*14;y=h*(.25+.48*((i*7)%5)/5)+math.cos(t*.14+i)*18;r=4+i%3*3
            self.create_oval(x-r,y-r,x+r,y+r,outline='#252a35',width=1,tags='scene')
        fade=ease(min(1,t/.65));title=mix(BG,TEXT,fade)
        self.create_text(w/2,max(64,h*.19),text='WELCOME TO NOVA',font=(DISPLAY_FONT,30),fill=title,tags='scene')
        self.create_text(w/2,max(100,h*.19+40),text='Your world. Your rules. One control center.',font=(FONT,11),fill=mix(BG,MUTED,fade),tags='scene')
        for i,(box,action) in enumerate(zip(self.boxes(),self.actions)):
            x1,y1,x2,y2=box;level=self.levels[i];lift=level*5;y1-=lift;y2-=lift
            face=mix('#101217','#282c35',level);border=mix('#282d36','#8c95a7',level)
            rounded(self,x1,y1+5,x2,y2+5,15,fill='#030407',outline='',tags='scene')
            rounded(self,x1,y1,x2,y2,15,fill=face,outline=border,width=1,tags='scene')
            for line in range(16):
                glow=mix(face,'#515865',(1-line/16)*(.13+.12*level))
                self.create_line(x1+13,y1+2+line,x2-13,y1+2+line,fill=glow,tags='scene')
            self.create_text((x1+x2)/2,y1+23,text=action[0].upper(),font=(FONT,9),fill='#b6bdcb',tags='scene')
            self.icon(action[1],(x1+x2)/2,(y1+y2)/2+8,mix('#b2bac9','#ffffff',level), 'scene')
        self.create_text(w/2,max(350,h-40),text='N O V A   /   Created by Nova',font=(FONT,10),fill='#585f6f',tags='scene')
    def tick(self):
        if not self.winfo_exists():return
        if self.winfo_viewable():
            for i,level in enumerate(self.levels):self.levels[i]=level+((1 if i==self.hover else 0)-level)*.22
            self.draw();delay=33
        else:delay=180
        self.job=self.after(delay,self.tick)
    def destroy(self):
        if self.job is not None:
            try:self.after_cancel(self.job)
            except tk.TclError:pass
        super().destroy()

class BubbleBadge(tk.Canvas):
    def __init__(self,parent,textvariable,style='IdleBadge.TLabel',**kwargs):
        self.variable=textvariable;self.style=style;self._font=tkfont.Font(parent,font=(FONT,9,'bold'))
        super().__init__(parent,height=32,width=160,background=parent_color(parent),highlightthickness=0,borderwidth=0,**kwargs)
        self.trace=self.variable.trace_add('write',lambda *_:self.draw());self.bind('<Configure>',lambda e:self.draw());self.draw()
    def draw(self):
        text=self.variable.get();width=self._font.measure(text)+30
        super().configure(width=width);self.delete('all')
        w=max(self.winfo_width(),width) if self.winfo_width()<2 else self.winfo_width()
        face,fg=('#15382e','#9fe1c1') if self.style.startswith('Online') else ('#352c1c','#dfc596') if self.style.startswith('Busy') else ('#191d26','#a0a9ba')
        rounded(self,1,1,w-1,30,15,fill=face,outline=mix(face,fg,.16),width=1)
        self.create_text(w/2,16,text=text,font=self._font,fill=fg)
    def configure(self,cnf=None,**kwargs):
        if cnf:kwargs.update(cnf)
        changed='style' in kwargs
        if changed:self.style=kwargs.pop('style')
        result=super().configure(**kwargs) if kwargs else None
        if changed:self.draw()
        return result
    config=configure
    def destroy(self):
        try:self.variable.trace_remove('write',self.trace)
        except tk.TclError:pass
        super().destroy()
