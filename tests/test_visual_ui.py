import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_public_build import app,qt_app,HostManager,ROOT,QTest,QQmlApplicationEngine,QUrl,shiboken6
from PySide6.QtCore import QObject
from settings_store import SettingsStore

class VisualUITests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.cache=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.engine=QQmlApplicationEngine()
 def load(self):
  self.engine.rootContext().setContextProperty('nova',self.manager);self.engine.load(QUrl.fromLocalFile(str(ROOT/'app/qml/Main.qml')))
  self.assertTrue(self.engine.rootObjects());self.window=self.engine.rootObjects()[0];return self.window.findChild(QObject,'startupScene')
 def tearDown(self):
  shiboken6.delete(self.engine)
  for session in self.manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def test_intro_auto_finishes_and_does_not_replay_on_window_restore(self):
  intro=self.load();self.assertTrue(intro.property('active'));QTest.qWait(2800);self.assertFalse(intro.property('active'))
  self.window.hide();self.window.show();QTest.qWait(30);self.assertFalse(intro.property('active'))
 def test_skip_and_replay(self):
  intro=self.load();intro.finish();self.assertFalse(intro.property('active'));intro.begin();self.assertTrue(intro.property('active'));intro.finish()
 def test_reduced_motion_skips_intro(self):
  self.manager.active.update('reduced',True);intro=self.load();self.assertFalse(intro.property('active'))
 def test_startup_preference_persists_and_skips(self):
  self.manager.active.update('startup_animation',False);self.assertFalse(SettingsStore(self.manager.active.store.path).data['startup_animation'])
  intro=self.load();self.assertFalse(intro.property('active'));self.assertFalse(self.window.grabWindow().isNull())
 def test_dashboard_profiles_and_pages_render_without_intro(self):
  self.manager.setServersRoot(str(Path(self.temp.name)/'servers'));self.manager.addProfile('Modded survival');self.manager.addProfile('Friends')
  intro=self.load();intro.finish();QTest.qWait(50)
  self.assertEqual(len(self.window.property('serverRows')),3)
  for index in range(6):
   self.window.setProperty('page',index);QTest.qWait(30);self.assertFalse(self.window.grabWindow().isNull())
if __name__=='__main__':unittest.main()
