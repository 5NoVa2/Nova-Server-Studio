"""Windowless bootstrap; one Nova window at a time."""
import os, sys, traceback, threading, queue, tempfile, shutil
from pathlib import Path
from qt_runtime import activate_runtime, configure_rendering
configure_rendering()
folder=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.cache')))/'MCServerSwitcher'
folder.mkdir(parents=True,exist_ok=True)
log=(folder/'app.log').open('a',encoding='utf-8',buffering=1)
sys.stdout=log;sys.stderr=log
print('Nova 1.0.0-beta.3 startup: '+str(Path(__file__).resolve()))
print('Python: '+sys.executable+' | Qt renderer: '+os.environ.get('QT_QUICK_BACKEND',''))
qt=folder/'qt-libs';activate_runtime(qt)

def install_desktop_icon():
    if sys.platform!='win32':return
    try:
        import subprocess
        from process_manager import managed_popen
        script=Path(__file__).resolve().parent/'Install-Desktop-Icon.vbs'
        runner=Path(os.environ['SystemRoot'])/'System32'/'cscript.exe'
        proc=managed_popen([str(runner),'//nologo',str(script)],stdout=log,stderr=log,
                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:code=proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill();proc.wait();raise RuntimeError('Desktop shortcut creation timed out.')
        if code:print('Desktop shortcut could not be created. Run Install-Desktop-Icon.vbs to retry.')
    except Exception:
        print('Could not create desktop shortcut:');traceback.print_exc()

def bootstrap():
    try:import PySide6;return True
    except ImportError:pass
    import tkinter as tk
    from tkinter import ttk
    root=tk.Tk();root.title('Nova | Preparing interface');root.geometry('540x230');root.resizable(False,False)
    root.configure(bg='#11141c')
    tk.Label(root,text='N O V A',font=('Segoe UI',25,'bold'),bg='#11141c',fg='#eeeeef').pack(pady=(24,8))
    label=tk.Label(root,text='Preparing the new interface…\nFirst launch downloads Qt. This can take a few minutes.',font=('Segoe UI',11),bg='#11141c',fg='#a9b6cb');label.pack(pady=10)
    bar=ttk.Progressbar(root,mode='indeterminate');bar.pack(fill='x',padx=30,pady=12);bar.start()
    events=queue.Queue();result=[False];closing=[False]
    def work():
        try:
            from process_manager import managed_popen
            import subprocess
            with tempfile.TemporaryDirectory(dir=folder,prefix='qt-install-') as temp:
                proc=managed_popen([sys.executable,'-m','pip','install','--disable-pip-version-check','--target',temp,'PySide6==6.12.0'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if proc.wait()!=0:raise RuntimeError('Qt download failed. Check your internet connection and app.log.')
                if qt.exists():shutil.rmtree(qt)
                shutil.move(temp,str(qt))
            events.put(None)
        except Exception as e:traceback.print_exc();events.put(str(e))
    def close():
        closing[0]=True
        from process_manager import stop_all
        stop_all();root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    def poll():
        try:value=events.get_nowait()
        except queue.Empty:root.after(150,poll);return
        bar.stop()
        if value is None:result[0]=True;root.destroy()
        else:label.configure(text=value+'\nClose Nova, then launch it again to retry.',wraplength=480)
    threading.Thread(target=work,daemon=True).start();root.after(150,poll);root.mainloop()
    if result[0] and not closing[0]:
        activate_runtime(qt)
        return True
    return False
try:
    install_desktop_icon()
    if os.environ.get('NOVA_CLASSIC')=='1':
        import tkinter as tk
        from control import Control
        root=tk.Tk();Control(root);root.mainloop()
    elif bootstrap():
        from qt_app import main
        sys.exit(main())
except Exception:
    traceback.print_exc()
    import tkinter as tk
    from tkinter import ttk
    root=tk.Tk();root.title('Nova | Startup error');root.geometry('700x210')
    ttk.Label(root,text='Nova could not start',font=('Segoe UI',20,'bold')).pack(pady=25)
    ttk.Label(root,text='Error details: '+str(folder/'app.log'),wraplength=650).pack(padx=20)
    root.mainloop()
