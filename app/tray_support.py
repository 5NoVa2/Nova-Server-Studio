"""Windows notification-area icon. Tray callbacks are dispatched to Tk's thread."""
import importlib
import os
import subprocess
import sys
import threading
from pathlib import Path
from runtime import CACHE
from process_manager import managed_popen,check_cancelled


def ensure_tray(log):
    vendor=CACHE/'tray-libs'
    if str(vendor) not in sys.path:sys.path.insert(0,str(vendor))
    try:
        return importlib.import_module('pystray'),importlib.import_module('PIL.Image'),importlib.import_module('PIL.ImageDraw')
    except ImportError:pass
    log('Installing notification-area support (first use only)...')
    vendor.mkdir(parents=True,exist_ok=True)
    python=Path(sys.executable)
    if python.name.lower()=='pythonw.exe' and python.with_name('python.exe').exists():python=python.with_name('python.exe')
    with managed_popen([str(python),'-m','pip','install','--disable-pip-version-check','--no-input','--target',str(vendor),'pystray>=0.19.5,<1','Pillow>=10,<13'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)) as proc:
        for line in proc.stdout:log(line.rstrip())
        code=proc.wait()
    if code:raise ValueError('Tray support could not be installed. Saturn will minimize to the taskbar instead.')
    check_cancelled();importlib.invalidate_caches()
    return importlib.import_module('pystray'),importlib.import_module('PIL.Image'),importlib.import_module('PIL.ImageDraw')


class Tray:
    def __init__(self,dispatch,show,exit_app,log,on_ready=None):
        self.dispatch=dispatch;self.show=show;self.exit_app=exit_app;self.log=log;self.on_ready=on_ready or (lambda:None)
        self.ready=threading.Event();self.stopping=threading.Event();self.icon=None
    def start(self):threading.Thread(target=self.run,daemon=True).start()
    def run(self):
        if os.name!='nt':self.log('Windows tray is unavailable here; minimize uses the taskbar.');return
        try:
            pystray,image,draw=ensure_tray(self.log)
            check_cancelled()
            bitmap=image.new('RGBA',(64,64),(0,0,0,0));pen=draw.Draw(bitmap)
            pen.rounded_rectangle((3,3,61,61),radius=14,fill='#d9deea')
            pen.line([(19,46),(19,18),(45,46),(45,18)],fill='#0b101b',width=7,joint='curve')
            self.icon=pystray.Icon('NovaServerStudio',bitmap,'Saturn — server and tunnel manager',pystray.Menu(
                pystray.MenuItem('Open Saturn',lambda icon,item:self.dispatch(self.show),default=True),
                pystray.MenuItem('Exit Saturn (stop server and tunnel)',lambda icon,item:self.dispatch(self.exit_app))))
            def setup(icon):
                if self.stopping.is_set():icon.stop();return
                icon.visible=True;self.ready.set();self.log('Saturn tray icon ready. X keeps hosting in the background.');self.dispatch(self.on_ready)
            self.icon.run(setup=setup)
        except Exception as error:
            if not self.stopping.is_set():self.log('Tray unavailable: '+str(error)+'. Minimize uses the taskbar.')
        finally:
            was_ready=self.ready.is_set();self.ready.clear()
            if was_ready and not self.stopping.is_set():self.dispatch(self.show)
    def stop(self):
        self.stopping.set();self.ready.clear()
        if self.icon:self.icon.stop()
