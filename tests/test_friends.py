import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from test_public_build import app,qt_app,HostManager,ROOT,QTest,QQmlApplicationEngine,QUrl,shiboken6
from PySide6.QtCore import QObject,QPointF,Qt
from friends import friend_entry,friend_key,normalized_friends,MAX_FRIENDS
from settings_store import SettingsStore,validated

class FriendsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.cache=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.s=self.manager.active
  self.s.timer.stop();self.s.api_save_timer.stop()
 def tearDown(self):
  self.manager.queue.timer.stop()
  for session in self.manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def running(self,edition='Java'):
  proc=Mock();proc.poll.return_value=None
  self.s.server=proc;self.s.running_engine='Bedrock' if edition=='Bedrock' else 'Vanilla'
  return proc
 def test_validate_names_edition_and_command_injection(self):
  self.assertEqual(friend_entry(' Alice_12 ','Java'),dict(name='Alice_12',edition='Java'))
  self.assertEqual(friend_entry('Bedrock Friend','Bedrock')['name'],'Bedrock Friend')
  for name,edition in [('Alice;op me','Java'),('Alice\nstop','Java'),('Bad" Name','Bedrock'),('   ','Java'),('a'*33,'Bedrock'),('Alice','unknown')]:
   with self.assertRaises(ValueError):friend_entry(name,edition)
 def test_settings_sanitize_and_bound_friend_lists(self):
  rows=[dict(name='Alice',edition='Java'),dict(name='alice',edition='Java'),dict(name='Alice',edition='Bedrock'),dict(name='x\nstop',edition='Java'),None]
  self.assertEqual(len(normalized_friends(rows)),2)
  self.assertEqual(len(normalized_friends([dict(name='Player'+str(i),edition='Java') for i in range(110)])),MAX_FRIENDS)
  self.assertEqual(validated({})['friends'],[]);self.assertTrue(validated({})['auto_whitelist_friends'])
 def test_offline_friends_save_persist_and_remain_profile_specific(self):
  self.assertTrue(self.s.addFriend('Alice','Java'));self.assertIn('Queued',self.s.friend_rows()[0]['status'])
  restored=SettingsStore(self.s.store.path);self.assertEqual(restored.data['friends'],[dict(name='Alice',edition='Java')])
  self.assertFalse(self.s.addFriend('ALICE','Java'));self.assertEqual(len(self.s.s['friends']),1)
  self.manager.addProfile('Other');self.assertEqual(self.manager.active.s['friends'],[])
  self.manager.selectProfile(0);self.assertEqual(self.manager.active.s['friends'][0]['name'],'Alice')
 def test_sync_waits_for_ready_and_sends_each_friend_once_per_process(self):
  self.s.addFriend('Alice','Java');self.running()
  with patch.object(self.s,'command',return_value=True) as send:
   self.assertEqual(self.s._sync_friends(),0);send.assert_not_called()
   self.s.ready.set();self.assertEqual(self.s._sync_friends(),1);send.assert_called_once_with('whitelist add Alice')
   self.assertIn('Command sent',self.s.friend_rows()[0]['status']);self.s._sync_friends();self.assertEqual(send.call_count,1)
   self.running();self.s._sync_friends();self.assertEqual(send.call_count,2)
 def test_ready_tick_integrates_automatic_sync(self):
  self.s.addFriend('Alice','Java');self.running();self.s.ready.set()
  with patch.object(self.s,'command',return_value=True) as send,patch.object(self.s,'refresh_files'),patch.object(self.s.stats,'sample',return_value={}):
   self.s.tick()
   self.assertIn(('whitelist add Alice',),[call.args for call in send.call_args_list])
 def test_bedrock_names_are_quoted_and_wrong_edition_waits(self):
  self.s.addFriend('Alice','Java');self.s.addFriend('Bedrock Friend','Bedrock');self.running('Bedrock');self.s.ready.set()
  with patch.object(self.s,'command',return_value=True) as send:
   self.s._sync_friends();send.assert_called_once_with('allowlist add "Bedrock Friend"')
   self.assertIn('Java',self.s.friend_rows()[0]['status'])
 def test_auto_off_and_explicit_retry_do_not_enable_whitelist_or_grant_op(self):
  self.s.addFriend('Alice','Java');self.s.autoWhitelistFriends(False);self.running();self.s.ready.set()
  with patch.object(self.s,'command',return_value=True) as send:
   self.s._sync_friends();send.assert_not_called();self.s.syncFriendsNow()
   send.assert_called_once_with('whitelist add Alice')
  self.assertFalse(SettingsStore(self.s.store.path).data['auto_whitelist_friends'])
 def test_failed_save_does_not_add_or_send_and_failed_send_is_not_marked_synced(self):
  self.running();self.s.ready.set()
  with patch.object(self.s,'save',return_value=False),patch.object(self.s,'command') as send:
   self.assertFalse(self.s.addFriend('Alice','Java'));self.assertEqual(self.s.s['friends'],[]);send.assert_not_called()
  self.s.addFriend('Bob','Java');self.s._friend_sent.clear()
  with patch.object(self.s,'command',return_value=False) as send:
   self.s._sync_friends();self.assertNotIn(friend_key(dict(name='Bob',edition='Java')),self.s._friend_sent)
   self.s._sync_friends();self.assertEqual(send.call_count,1)
 def test_automatic_sync_is_batched_and_forget_keeps_server_entries(self):
  for i in range(12):self.s.addFriend('Player'+str(i),'Java')
  self.running();self.s.ready.set()
  with patch.object(self.s,'command',return_value=True) as send:
   self.assertEqual(self.s._sync_friends(),5);self.assertEqual(send.call_count,5)
   self.s.forgetFriend('Player0','Java');self.assertEqual(send.call_count,5)
   self.assertEqual(len(SettingsStore(self.s.store.path).data['friends']),11)
 def test_players_friends_tab_adds_name_using_real_qml_button(self):
  engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',self.manager)
  engine.load(QUrl.fromLocalFile(str(ROOT/'app/qml/Main.qml')));self.assertTrue(engine.rootObjects())
  try:
   window=engine.rootObjects()[0];window.findChild(QObject,'startupScene').finish();window.setProperty('page',5);QTest.qWait(80)
   def items(item):
    yield item
    for child in item.childItems():yield from items(child)
   def named(name):return next(i for i in items(window.contentItem()) if i.objectName()==name)
   def click(name):
    item=named(name);QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint());QTest.qWait(60)
   click('friendsTab');self.assertEqual(named('playerSections').property('currentIndex'),1)
   named('friendNameField').setProperty('text','Alice');click('addFriendButton')
   self.assertEqual(self.s.s['friends'],[dict(name='Alice',edition='Java')]);self.assertEqual(named('friendNameField').property('text'),'')
   self.assertFalse(window.grabWindow().isNull())
  finally:shiboken6.delete(engine)
if __name__=='__main__':unittest.main()
