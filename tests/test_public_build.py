import os,sys,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtCore import QUrl
from PySide6.QtTest import QTest
import shiboken6
import qt_app
from hosts import HostManager
from connection_settings import DEFAULTS,Connection,preferences
from server_locations import folder_name
app=QApplication.instance() or QApplication([])

class PublicBuildTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.patch=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.patch.start()
  self.manager=HostManager(app,qt_app.Bridge);self.manager.setServersRoot(str(Path(self.temp.name)/'Servers'))
 def tearDown(self):
  for session in self.manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  self.patch.stop();self.temp.cleanup()
 def test_no_preconfigured_remote_and_local_profile_save(self):
  self.assertEqual(DEFAULTS['vps_host'],'');self.assertEqual(DEFAULTS['join_address'],'')
  self.assertTrue(self.manager.active.save());self.assertEqual(self.manager.active.s['vps_host'],'')
  self.manager.addProfile('Survival');self.assertEqual(len(self.manager.entries),2)
  self.assertTrue((Path(self.temp.name)/'Servers'/'Survival').is_dir())
 def test_connection_validation_is_strict_when_connecting(self):
  with self.assertRaises(ValueError):Connection.parse(DEFAULTS)
  self.assertEqual(preferences(DEFAULTS)['vps_host'],'')
  c=Connection.parse(dict(DEFAULTS,vps_host='203.0.113.10'));self.assertEqual(c.join_address,'203.0.113.10')
 def test_named_folders_do_not_overwrite(self):
  self.manager.addProfile('Friends');first=Path(self.manager.active.s['folder']);(first/'keep.txt').write_text('world')
  self.manager.addProfile('Friends');self.assertEqual(Path(self.manager.active.s['folder']).name,'Friends 2');self.assertEqual((first/'keep.txt').read_text(),'world')
  self.assertEqual(folder_name('CON'),'Server CON')
 def test_local_preflight_does_not_require_vps(self):
  self.manager.preflight(self.manager.active)
  with self.assertRaises(ValueError):self.manager.preflight(self.manager.active,for_tunnel=True)
 def test_unconfigured_profiles_do_not_break_vps_port_collection(self):
  first=self.manager.active;first.update('vps_host','203.0.113.10');self.manager.addProfile('Local only');self.manager.active.update('vps_host','')
  ports=self.manager.vps_ports(Connection.parse(first.s));self.assertEqual(ports,([first.s['remote_java_port']],[first.s['remote_bedrock_port']]))
 def test_local_join_address_uses_local_port(self):
  self.manager.active.s['local_java_port']=25599
  self.manager.active.s['remote_java_port']=25565
  self.assertEqual(self.manager.active.join_display(),'localhost:25599')
 def test_qml_loads_and_renders(self):
  engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',self.manager)
  engine.load(QUrl.fromLocalFile(str(ROOT/'app'/'qml'/'Main.qml')))
  self.assertTrue(engine.rootObjects());window=engine.rootObjects()[0];self.manager.window=window
  for index in range(6):window.setProperty('page',index);QTest.qWait(30)
  self.assertFalse(window.grabWindow().isNull());self.assertEqual(QQuickWindow.sceneGraphBackend(),'software')
  shiboken6.delete(engine)
 def test_release_has_no_personal_endpoint_or_runtime_data(self):
  # Runtime data belongs outside source distributions.
  for path in (ROOT/'app').rglob('*'):
   if not path.is_file() or '__pycache__' in path.parts:continue
   self.assertNotIn(path.name,('settings.json','profiles.json','app.log','ssh-known-hosts'))
   self.assertNotEqual(path.suffix,'.dpapi')
  self.assertTrue((ROOT/'LICENSE').read_text().startswith('MIT License'))
if __name__=='__main__':unittest.main()
