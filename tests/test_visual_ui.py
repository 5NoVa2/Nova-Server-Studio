import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_public_build import app,qt_app,HostManager,ROOT,QTest,QQmlApplicationEngine,QUrl,shiboken6
from PySide6.QtCore import QObject
from settings_store import SettingsStore

class VisualUITests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.cache=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.manager.active.secrets['apiKey']='';self.engine=QQmlApplicationEngine()
 def load(self):
  self.engine.rootContext().setContextProperty('nova',self.manager);self.engine.load(QUrl.fromLocalFile(str(ROOT/'app/qml/Main.qml')))
  self.assertTrue(self.engine.rootObjects());self.window=self.engine.rootObjects()[0];return self.window.findChild(QObject,'startupScene')
 def tearDown(self):
  shiboken6.delete(self.engine)
  for session in self.manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def test_intro_auto_finishes_and_does_not_replay_on_window_restore(self):
  intro=self.load();self.assertTrue(intro.property('active'));QTest.qWait(5000);self.assertFalse(intro.property('active'))
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
  for index in range(8):
   self.window.setProperty('page',index);QTest.qWait(30);self.assertFalse(self.window.grabWindow().isNull())
 def test_dashboard_card_selects_hero_without_navigating(self):
  self.manager.setServersRoot(str(Path(self.temp.name)/'servers'));self.manager.renameProfile('First');self.manager.addProfile('Second');self.manager.selectProfile(0)
  intro=self.load();intro.finish();self.window.selectDashboardServer(1);QTest.qWait(30)
  self.assertEqual(self.window.property('page'),0);self.assertEqual(self.manager.current,1)
  self.assertEqual(self.window.findChild(QObject,'serverHeroName').property('text'),'Second')
  self.manager.active.publish(busy=True);self.window.selectDashboardServer(0);QTest.qWait(30)
  self.assertEqual(self.manager.current,1);self.assertEqual(self.window.property('page'),0)
 def test_single_click_opens_folder_then_file(self):
  from PySide6.QtCore import QPointF,Qt
  folder=Path(self.temp.name)/'server';folder.mkdir();(folder/'server.properties').write_text('motd=Test\n');(folder/'config').mkdir();(folder/'config/example.txt').write_text('Hello editor')
  self.manager.active.s['folder']=str(folder);self.manager.active.installed()
  intro=self.load();intro.finish();self.window.setProperty('page',3);QTest.qWait(100)
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  def click(name):
   item=next(i for i in items(self.window.contentItem()) if i.objectName()==name)
   point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint();QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point)
  click('browserItem_config')
  for _ in range(20):
   QTest.qWait(30)
   if self.manager.s['browserPath']=='config':break
  self.assertEqual(self.manager.s['browserPath'],'config');click('browserItem_config/example.txt');QTest.qWait(30)
  self.assertEqual(self.manager.s['file'],'config/example.txt');self.assertEqual(self.manager.s['editor'],'Hello editor')
 def test_task_popup_uses_dropdowns_without_date_and_saves(self):
  from PySide6.QtCore import QPointF,Qt
  intro=self.load();intro.finish();self.window.setProperty('page',6)
  popup=self.window.findChild(QObject,'taskCreatePopup');popup.open();QTest.qWait(60)
  self.assertTrue(popup.property('visible'));self.assertIsNone(self.window.findChild(QObject,'taskDate'))
  for name,index in [('taskHour',0),('taskMinute',5),('taskPeriod',1),('taskRepeat',1)]:self.window.findChild(QObject,name).setProperty('currentIndex',index)
  period=self.window.findChild(QObject,'taskPeriod');self.assertFalse(period.property('contentItem').property('truncated'))
  button=self.window.findChild(QObject,'saveTimedTask');position=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
  QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,position);QTest.qWait(60)
  self.assertFalse(popup.property('visible'));self.assertEqual(len(self.manager.queue.schedules.rows),1)
  self.assertIn('T13:05:00',self.manager.queue.schedules.rows[0]['anchor'])
  self.assertIn('Saturn',self.window.title())
 def test_sidebar_order_and_server_modpacks_section(self):
  from PySide6.QtCore import QPointF,Qt
  intro=self.load();intro.finish()
  nav=self.window.property('navigation');nav=nav.toVariant() if hasattr(nav,'toVariant') else nav;self.assertEqual([item['label'] for item in nav],['Dashboard','Server','Files','Tasks','Players','Settings','Help'])
  self.assertEqual([item['page'] for item in nav],[0,1,3,6,5,4,7])
  self.window.setProperty('page',2);QTest.qWait(40)
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  buttons=[item for item in items(self.window.contentItem()) if item.objectName().startswith('nav_')]
  self.assertEqual([item.objectName() for item in buttons],['nav_Dashboard','nav_Server','nav_Files','nav_Tasks','nav_Players','nav_Settings','nav_Help'])
  self.assertTrue(next(item for item in buttons if item.objectName()=='nav_Server').property('primary'))
  tab=self.window.findChild(QObject,'serverControlTab');point=tab.mapToScene(QPointF(tab.width()/2,tab.height()/2)).toPoint()
  QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point);self.assertEqual(self.window.property('page'),1)
 def test_prepare_world_pack_popup_uses_server_release_filter(self):
  intro=self.load();intro.finish();self.window.setProperty('page',1)
  self.assertIsNotNone(self.window.findChild(QObject,'browseModpacksButton'))
  self.manager.active.publish(project={'id':1,'name':'Preview pack','summary':'Example for layout checks.'},packs=[{'id':1,'name':'Preview pack','downloadCount':0}],releases=[{'id':10,'displayName':'Client only'},{'id':11,'displayName':'Server ready','serverPackFileId':12}],releaseIndex=1)
  popup=self.window.findChild(QObject,'packBrowserPopup');popup.open();QTest.qWait(100)
  self.assertTrue(popup.property('visible'));self.assertFalse(self.window.grabWindow().isNull())
  filtered=self.window.packReleases();filtered=filtered.toVariant() if hasattr(filtered,'toVariant') else filtered;self.assertEqual([item['index'] for item in filtered],[1])
  self.window.setProperty('serverReleasesOnly',False);values=self.window.packReleases();self.assertEqual(len(values.toVariant() if hasattr(values,'toVariant') else values),2)
  self.assertEqual(self.window.property('page'),1)
  from PySide6.QtCore import QPointF,Qt
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  button=next(item for item in items(self.window.contentItem()) if item.objectName()=='selectPackForServer')
  point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint();QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point);QTest.qWait(40)
  self.assertFalse(popup.property('visible'));self.assertEqual(self.manager.s['engine'],'CurseForge');self.assertEqual(self.manager.s['cf_pack']['file_id'],11)
 def test_settings_sections_toggle_and_java_preference_survives_reload(self):
  intro=self.load();intro.finish();self.window.setProperty('page',4);QTest.qWait(30)
  sections=['updateSettings','storageSettings','connectionSettings','portSettings','dnsSettings','environmentSettings']
  for name in sections:
   section=self.window.findChild(QObject,name);self.assertIsNotNone(section);self.assertFalse(section.property('expanded'))
   section.setProperty('expanded',True);QTest.qWait(10);self.assertTrue(section.property('expanded'))
   section.setProperty('expanded',False)
  selector=self.window.findChild(QObject,'javaVersionSelector');self.assertIsNotNone(selector)
  self.manager.active.update('java_version','17');QTest.qWait(10)
  self.assertEqual(selector.property('currentText'),'17')
  self.assertEqual(SettingsStore(self.manager.active.store.path).data['java_version'],'17')
  self.manager.active.update('java_version','invalid');self.assertEqual(self.manager.active.s['java_version'],'17')
 def test_java_override_changes_actual_launch_and_requires_preparation(self):
  session=self.manager.active;folder=Path(self.temp.name)/'server';folder.mkdir()
  import json
  original=qt_app.CACHE/'runtime/21/jdk/bin/java.exe';original.parent.mkdir(parents=True);original.touch()
  (folder/'switcher-server.json').write_text(json.dumps({'java':str(original),'engine':'Vanilla'}));(folder/'eula.txt').write_text('eula=true\n')
  session.s.update(folder=str(folder),java_version='17')
  with patch.object(session,'apply_ports'),patch.object(self.manager,'preflight'):
   with self.assertRaisesRegex(ValueError,'Prepare Java 17'):session.start_server()
   chosen=qt_app.CACHE/'runtime/17/jdk/bin/java.exe';chosen.parent.mkdir(parents=True);chosen.touch()
   with patch.object(qt_app,'managed_popen',side_effect=RuntimeError('launch intercepted')) as launch:
    with self.assertRaisesRegex(RuntimeError,'launch intercepted'):session.start_server()
    self.assertEqual(launch.call_args.args[0][0],str(chosen.resolve()))

 def test_live_server_resource_display_and_stopped_reset(self):
  intro=self.load();intro.finish();self.window.setProperty('page',0)
  self.manager.active.timer.stop()
  self.manager.active.publish(cpuLoad=12.5,ramBytes=1610612736)
  QTest.qWait(20)
  self.assertEqual(self.window.findChild(QObject,'serverCpuStat').property('text'),'12.5%')
  self.assertEqual(self.window.findChild(QObject,'serverRamStat').property('text'),'1.50 GB')
  self.manager.active.tick();QTest.qWait(20)
  self.assertEqual(self.window.findChild(QObject,'serverCpuStat').property('text'),'—')
  self.assertEqual(self.window.findChild(QObject,'serverRamStat').property('text'),'—')
 def test_startup_audio_preferences_and_skip(self):
  session=self.manager.active;session.update('startup_sound',False);session.update('sound_volume',0.15)
  intro=self.load();self.assertFalse(intro.property('soundEnabled'));self.assertEqual(intro.property('soundVolume'),0.15)
  audio=self.window.findChild(QObject,'startupAudio');self.assertIsNotNone(audio);self.assertFalse(audio.property('playing'))
  intro.finish();self.assertFalse(intro.property('soundPending'));self.assertFalse(audio.property('playing'))
  saved=SettingsStore(session.store.path).data;self.assertFalse(saved['startup_sound']);self.assertEqual(saved['sound_volume'],0.15)
 def test_ui_sound_events_and_master_mute(self):
  from PySide6.QtTest import QSignalSpy
  from PySide6.QtCore import QPointF,Qt
  intro=self.load();intro.finish();QTest.qWait(30)
  bus=self.window.findChild(QObject,'uiSounds');self.assertIsNotNone(bus)
  spy=QSignalSpy(bus.requested)
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  button=next(item for item in items(self.window.contentItem()) if item.objectName()=='nav_Settings')
  point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
  QTest.mouseMove(self.window,point);QTest.qWait(20)
  QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point);QTest.qWait(20)
  kinds=[spy.at(i)[0] for i in range(spy.count())]
  self.assertIn('click',kinds);self.assertIn('transition',kinds);self.assertEqual(self.window.property('page'),4)
  QTest.qWait(180);before=spy.count();bus.play('hover');bus.play('hover');self.assertEqual(spy.count(),before+1)
  self.manager.active.update('sound_enabled',False);QTest.qWait(10);before=spy.count()
  for kind in ['hover','click','transition']:bus.play(kind)
  self.assertEqual(spy.count(),before);self.assertFalse(bus.property('soundsEnabled'));self.assertFalse(intro.property('soundEnabled'))
  self.assertFalse(SettingsStore(self.manager.active.store.path).data['sound_enabled'])
  self.manager.active.update('sound_enabled',True);self.manager.active.update('sound_volume',0);QTest.qWait(10)
  bus.play('click');self.assertEqual(spy.count(),before)
 def test_help_search_expansion_survives_status_updates(self):
  intro=self.load();intro.finish();self.window.setProperty('page',7);QTest.qWait(30)
  help_page=self.window.findChild(QObject,'helpPage');search=help_page.findChild(QObject,'helpSearch')
  self.assertIsNone(help_page.findChild(QObject,'helpJoinAddressField'))
  search.setProperty('text','The VPS did not accept a usable key');QTest.qWait(30)
  matches=help_page.property('matches');matches=matches.toVariant() if hasattr(matches,'toVariant') else matches
  self.assertEqual([row['id'] for row in matches],['publickey'])
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  topic=next(item for item in items(self.window.contentItem()) if item.objectName()=='helpTopic_publickey');topic.setProperty('expanded',True)
  self.manager.active.publish(activity='A routine status update');QTest.qWait(600)
  self.assertTrue(topic.property('expanded'))
  search.setProperty('text','no-such-help-topic');QTest.qWait(20)
  self.assertEqual(help_page.findChild(QObject,'helpResultCount').property('text'),'0 help topics')
 def test_ssh_guide_commands_copy_without_running_and_survive_refresh(self):
  from PySide6.QtCore import QPointF,Qt
  intro=self.load();intro.finish();self.window.setHeight(1800);self.window.setProperty('page',7);QTest.qWait(50)
  page=self.window.findChild(QObject,'helpPage');page.findChild(QObject,'helpSearch').setProperty('text','First-time VPS');QTest.qWait(30)
  def items(item):
   yield item
   for child in item.childItems():yield from items(child)
  topic=next(item for item in items(self.window.contentItem()) if item.objectName()=='helpTopic_ssh-startup')
  topic.setProperty('expanded',True);QTest.qWait(80)
  button=next(item for item in items(topic) if item.objectName()=='copyHelpCommand_0_main')
  point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
  with patch.object(self.manager.active,'task') as task:
   QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point);QTest.qWait(20)
   self.assertEqual(app.clipboard().text(),'whoami');self.assertEqual(button.property('text'),'Copied');task.assert_not_called()
  self.manager.active.publish(activity='Status refresh');QTest.qWait(300);self.assertTrue(topic.property('expanded'))
  page.findChild(QObject,'helpSearch').setProperty('text','ss -lnup');QTest.qWait(30)
  matches=page.property('matches');matches=matches.toVariant() if hasattr(matches,'toVariant') else matches
  self.assertEqual([row['id'] for row in matches],['ssh-startup'])
 def test_optional_vps_checkbox_synchronizes_and_keeps_join_addresses_separate(self):
  from PySide6.QtCore import QPointF,Qt
  self.manager.setJoinAddress('vps.example.com')
  intro=self.load();intro.finish();self.window.setHeight(1800);self.window.setProperty('page',4)
  hosting=self.window.findChild(QObject,'hostingSettings');hosting.setProperty('expanded',True);QTest.qWait(60)
  toggle=self.window.findChild(QObject,'settingsUseVpsToggle');point=toggle.mapToScene(QPointF(toggle.width()/2,toggle.height()/2)).toPoint()
  QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point);QTest.qWait(40)
  self.assertFalse(self.manager.s['use_vps']);self.assertFalse(self.window.findChild(QObject,'connectionSettings').property('visible'))
  self.assertFalse(self.window.findChild(QObject,'serverUseVpsToggle').property('checked'))
  hosting.setProperty('expanded',False);dns=self.window.findChild(QObject,'dnsSettings');dns.setProperty('expanded',True);QTest.qWait(40)
  field=dns.findChild(QObject,'helpJoinAddressField');self.assertEqual(field.property('text'),'')
  self.manager.setJoinAddress('home.example.com');QTest.qWait(30);self.assertEqual(field.property('text'),'home.example.com')
  self.manager.update('use_vps',True);QTest.qWait(30);self.assertEqual(field.property('text'),'vps.example.com')
  self.assertTrue(self.window.findChild(QObject,'settingsUseVpsToggle').property('checked'))
 def test_settings_domain_editor_save_validation_and_profile_isolation(self):
  from settings_store import SettingsStore
  self.manager.active.update('vps_host','203.0.113.20');self.manager.active.update('remote_java_port',25566)
  intro=self.load();intro.finish();self.window.setHeight(1800);self.window.setProperty('page',4)
  page=self.window.findChild(QObject,'dnsSettings');page.setProperty('expanded',True);QTest.qWait(40)
  field=page.findChild(QObject,'helpJoinAddressField')
  from PySide6.QtCore import QPointF,Qt
  point=field.mapToScene(QPointF(field.width()/2,field.height()/2)).toPoint();QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point)
  app.clipboard().setText('Play.Example.com.');QTest.keyClick(self.window,Qt.Key_A,Qt.ControlModifier);QTest.keyClick(self.window,Qt.Key_V,Qt.ControlModifier);QTest.qWait(20)
  button=page.findChild(QObject,'saveJoinAddressButton');self.assertTrue(button.property('enabled'))
  point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint();QTest.mouseClick(self.window,Qt.LeftButton,Qt.NoModifier,point)
  QTest.qWait(20);self.assertEqual(field.property('text'),'play.example.com')
  self.assertEqual(self.manager.s['joinDisplay'],'play.example.com:25566')
  self.assertEqual(SettingsStore(self.manager.active.store.path).data['join_address'],'play.example.com')
  self.assertFalse(self.manager.setJoinAddress('https://example.com:25565'));self.assertEqual(self.manager.s['join_address'],'play.example.com')
  self.manager.action('copy');self.assertEqual(app.clipboard().text(),'play.example.com:25566')
  self.manager.addProfile('Other');self.assertTrue(self.manager.setJoinAddress('other.example.com'));self.manager.selectProfile(0)
  QTest.qWait(20);self.assertEqual(field.property('text'),'play.example.com')
  self.assertTrue(self.manager.setJoinAddress(''));self.assertEqual(self.manager.s['joinDisplay'],'203.0.113.20:25566')
if __name__=='__main__':unittest.main()
