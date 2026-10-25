"""Frozen Store entry point: no pip bootstrap, shell scripts, or shortcut writes."""
import ctypes,json,os,sys,traceback
from pathlib import Path

def main():
 from distribution import STORE_BUILD
 if not STORE_BUILD:raise RuntimeError('Store distribution marker is missing.')
 from runtime import CACHE
 CACHE.mkdir(parents=True,exist_ok=True)
 log=(CACHE/'app.log').open('a',encoding='utf-8',buffering=1)
 sys.stdout=sys.stderr=log
 try:
  from qt_runtime import configure_rendering
  configure_rendering()
  # Build-time smoke check loads QML and bundled modules without hosting anything.
  if '--smoke-test' in sys.argv:
   from PySide6.QtWidgets import QApplication
   from PySide6.QtQuick import QQuickWindow
   from PySide6.QtQml import QQmlApplicationEngine
   from PySide6.QtCore import QUrl
   import paramiko,qt_app,engines,bedrock
   from hosts import HostManager
   app=QApplication([]);manager=HostManager(app,qt_app.Bridge)
   manager.active.update('startup_animation',False)
   engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',manager)
   engine.load(QUrl.fromLocalFile(str(qt_app.BASE/'qml/Main.qml')))
   if not engine.rootObjects():raise RuntimeError('Bundled QML failed to load')
   result={'store':STORE_BUILD,'qml':True,'paramiko':paramiko.__version__}
   (CACHE/'store-smoke.json').write_text(json.dumps(result))
   import shiboken6
   shiboken6.delete(engine)
   return 0
  from qt_app import main as run
  return run()
 except Exception:
  traceback.print_exc()
  if sys.platform=='win32' and '--smoke-test' not in sys.argv:
   ctypes.windll.user32.MessageBoxW(None,'Saturn could not start. Error details: '+str(CACHE/'app.log'),'Saturn startup error',0x10)
  return 1
if __name__=='__main__':raise SystemExit(main())
