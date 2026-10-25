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
 def prepared(self):
  bridge=self.manager.active;folder=Path(self.temp.name)/'installed';folder.mkdir()
  (folder/'server.properties').write_text('motd=Original\nmax-players=20\n')
  (folder/'switcher-server.json').write_text('{"engine":"Forge"}')
  bridge.s['folder']=str(folder);bridge.installed();return bridge,folder
 def test_only_vital_files_without_recursive_scan(self):
  from server_files import ServerFiles
  bridge,folder=self.prepared();(folder/'config').mkdir();(folder/'config'/'a-mod.toml').write_text('a=1')
  (folder/'config'/'paper-global.yml').write_text('version: 1')
  with patch('os.walk',side_effect=AssertionError('recursive scan')):
   self.assertEqual(ServerFiles(folder).config_files(),['config/paper-global.yml','server.properties'])
 def test_creation_and_addon_reload_stay_clean(self):
  bridge,folder=self.prepared();self.assertFalse(bridge.s['dirty']);self.assertFalse(bridge.s['propertyDirty'])
  bridge.load_files(preserve=True);self.assertFalse(bridge.s['dirty'])
 def test_save_all_merges_editor_and_settings(self):
  bridge,folder=self.prepared()
  bridge.update('editor',bridge.s['editor'].replace('motd=Original','motd=Edited'))
  bridge.property_value('max-players','35');bridge.save_all()
  content=(folder/'server.properties').read_text();self.assertIn('motd=Edited',content);self.assertIn('max-players=35',content)
  self.assertFalse(bridge.s['dirty']);self.assertFalse(bridge.s['propertyDirty'])
 def test_save_all_rejects_conflicting_edits_and_external_changes(self):
  bridge,folder=self.prepared();bridge.update('editor',bridge.s['editor'].replace('motd=Original','motd=Raw'))
  bridge.property_value('motd','Form')
  with self.assertRaisesRegex(ValueError,'Conflicting'):bridge.save_all()
  self.assertIn('motd=Original',(folder/'server.properties').read_text())
  (folder/'server.properties').write_text('motd=External\n')
  with self.assertRaisesRegex(ValueError,'changed on disk'):bridge.save_all()
 def test_no_state_notification_for_unchanged_values(self):
  bridge=self.manager.active;calls=[];bridge.changed.connect(lambda:calls.append(1))
  bridge.publish(busy=False);self.assertEqual(calls,[])
 def test_vanilla_version_list_includes_snapshots(self):
  import engines
  manifest={'versions':[{'id':'release','type':'release'},{'id':'snapshot','type':'snapshot'}]}
  with patch.object(engines.net,'get_json',return_value=manifest):
   self.assertEqual(engines.available_versions('Vanilla'),['release','snapshot'])
   self.assertEqual(engines.available_versions('Spigot'),['release'])
 def test_backup_restore_preserves_backup_and_replaces_server(self):
  from app import manual_backup
  from backups import list_backups,restore_backup
  bridge,folder=self.prepared();(folder/'world').mkdir();(folder/'world'/'level.dat').write_bytes(b'original')
  saved=manual_backup(folder);(folder/'world'/'level.dat').write_bytes(b'changed');(folder/'new.txt').write_text('new')
  self.assertEqual(list_backups(folder)[0]['path'],str(saved))
  restore_backup(folder,saved)
  self.assertEqual((folder/'world'/'level.dat').read_bytes(),b'original');self.assertTrue(saved.exists());self.assertFalse((folder/'new.txt').exists())
  with self.assertRaises(ValueError):restore_backup(folder,folder)
 def test_failed_restore_keeps_current_world(self):
  from app import manual_backup
  from backups import restore_backup
  bridge,folder=self.prepared();saved=manual_backup(folder);(folder/'keep.txt').write_text('keep')
  with patch('backups.copy_file',side_effect=OSError('disk full')):
   with self.assertRaises(OSError):restore_backup(folder,saved)
  self.assertEqual((folder/'keep.txt').read_text(),'keep')
 def test_installer_logs_are_batched(self):
  bridge=self.manager.active;calls=[];bridge.changed.connect(lambda:calls.append(1))
  for i in range(1000):bridge.log('Downloading mod '+str(i))
  self.assertEqual(calls,[]);bridge.flush_logs();self.assertEqual(len(calls),1);self.assertIn('mod 999',bridge.s['logs'])
 def test_qml_reload_does_not_mark_editor_dirty(self):
  bridge,folder=self.prepared();engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',self.manager)
  engine.load(QUrl.fromLocalFile(str(ROOT/'app'/'qml'/'Main.qml')))
  self.assertTrue(engine.rootObjects());window=engine.rootObjects()[0];window.setProperty('page',3);QTest.qWait(20)
  (folder/'server.properties').write_text('motd=External update\n');bridge.refresh_files();QTest.qWait(20)
  self.assertFalse(bridge.s['dirty']);self.assertIn('External update',bridge.s['editor'])
  shiboken6.delete(engine)
 def test_release_has_no_personal_endpoint_or_runtime_data(self):
  # Runtime data belongs outside source distributions.
  for path in (ROOT/'app').rglob('*'):
   if not path.is_file() or '__pycache__' in path.parts:continue
   self.assertNotIn(path.name,('settings.json','profiles.json','app.log','ssh-known-hosts'))
   self.assertNotEqual(path.suffix,'.dpapi')
  self.assertTrue((ROOT/'LICENSE').read_text().startswith('MIT License'))
if __name__=='__main__':unittest.main()
