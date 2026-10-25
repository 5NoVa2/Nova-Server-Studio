import tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch,Mock
from test_public_build import app,qt_app,HostManager
from file_browser import FileBrowser

class BrowserQueueTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.cache=patch.object(qt_app,'CACHE',self.base/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.bridge=self.manager.active;self.queue=self.manager.queue
  self.folder=self.base/'server';self.folder.mkdir();(self.folder/'server.properties').write_text('motd=Test\n');(self.folder/'switcher-server.json').write_text('{"engine":"Forge"}')
  self.bridge.s['folder']=str(self.folder);self.bridge.installed()
 def tearDown(self):
  self.queue.timer.stop()
  for s in self.manager.sessions.values():s.timer.stop();s.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def test_listing_and_safe_nested_editor(self):
  (self.folder/'mods').mkdir();(self.folder/'mods/mod.jar').write_bytes(b'PKbinary');(self.folder/'config').mkdir();path=self.folder/'config/example.toml';path.write_text('value=1\n')
  files=FileBrowser(self.folder);rows=files.listing();self.assertTrue(rows[0]['folder'])
  self.assertFalse(files.listing('mods')[0]['editable'])
  text,digest,encoding=files.read_text('config/example.toml');files.write_text('config/example.toml','value=2\n',digest,encoding);self.assertIn('2',path.read_text())
  with self.assertRaises(ValueError):files.write_text('config/example.toml','value=3\n',digest,encoding)
  with self.assertRaises(ValueError):files.listing('../')
  with self.assertRaises(ValueError):files.read_text('mods/mod.jar')
 def test_invalid_json_and_binary_text_rejected(self):
  (self.folder/'data.json').write_text('{}');files=FileBrowser(self.folder);text,digest,encoding=files.read_text('data.json')
  with self.assertRaises(ValueError):files.write_text('data.json','{',digest,encoding)
  self.assertEqual((self.folder/'data.json').read_text(),'{}')
  (self.folder/'binary.txt').write_bytes(b'a\0b')
  with self.assertRaises(ValueError):files.read_text('binary.txt')
 def test_queue_waits_for_ready_then_runs_save(self):
  self.queue.add('main','start');self.queue.add('main','save_world');self.queue.running=True
  def action(op):
   if op=='start':self.bridge.server=Mock();self.bridge.server.poll.return_value=None
  with patch.object(self.bridge,'action',side_effect=action),patch.object(self.bridge,'command') as command:
   self.queue.tick();self.assertEqual(self.queue.rows[0]['status'],'Running')
   self.queue.tick();self.bridge.ready.set();self.queue.tick();self.queue.tick()
   command.assert_called_once_with('save-all flush');self.assertEqual(self.queue.rows[1]['status'],'Running')
   self.bridge.world_saved.set();self.queue.tick();self.assertEqual(self.queue.rows[1]['status'],'Completed')
 def test_backup_preserves_running_and_tunnel_state(self):
  self.bridge.server=Mock();self.bridge.server.poll.return_value=None;self.bridge.tunnel=Mock();self.bridge.tunnel.poll.return_value=None
  def stop():self.bridge.server=None;self.bridge.tunnel=None
  def backup(op):self.assertEqual(op,'backup');self.bridge.publish(busy=True)
  def start():self.bridge.server=Mock();self.bridge.server.poll.return_value=None;self.bridge.ready.set()
  def tunnel():self.bridge.tunnel=Mock();self.bridge.tunnel.poll.return_value=None
  self.queue.add('main','backup');self.queue.running=True
  with patch.object(self.bridge,'stop',side_effect=stop),patch.object(self.bridge,'action',side_effect=backup) as copy,patch.object(self.bridge,'start_server',side_effect=start) as launch,patch.object(self.bridge,'connect_tunnel',side_effect=tunnel) as connect:
   self.queue.tick();copy.assert_called_once();self.queue.tick();launch.assert_not_called()
   self.bridge.publish(busy=False);self.queue.tick();launch.assert_called_once();self.queue.tick();connect.assert_called_once();self.queue.tick()
   self.assertEqual(self.queue.rows[0]['status'],'Completed')
 def test_backup_failure_pauses_and_does_not_restart(self):
  self.queue.add('main','backup');self.queue.running=True
  with patch.object(self.bridge,'action',side_effect=lambda op:self.bridge.publish(error='Disk full')),patch.object(self.bridge,'start_server') as start:
   self.queue.tick();self.assertEqual(self.queue.rows[0]['status'],'Failed');self.assertTrue(self.queue.paused);start.assert_not_called()
 def test_custom_command_validation_and_execution(self):
  self.bridge.server=Mock();self.bridge.server.poll.return_value=None
  for value in ('','stop\nsay hi','x'*513):
   with self.assertRaises(ValueError):self.queue.add('main','command',command=value)
  self.queue.add('main','command',command='say Hello players');self.queue.running=True
  with patch.object(self.bridge,'command') as command:self.queue.tick();command.assert_called_once_with('say Hello players')
  self.assertEqual(self.queue.rows[0]['status'],'Completed')
 def test_only_supported_actions_are_accepted(self):
  for operation in ('restart','players','save_all','tunnel'):
   with self.assertRaises(ValueError):self.queue.add('main',operation)
 def test_stop_all_prevents_queue_restarts(self):
  self.queue.add('main','backup');self.queue.current=self.queue.rows[0];self.queue.current['status']='Running'
  with patch.object(self.bridge,'stop'):self.manager.action('stop_all')
  self.assertTrue(self.queue.paused);self.assertIsNone(self.queue.current)
 def test_invalid_run_now_does_not_start_existing_queue(self):
  self.queue.add('main','stop');self.manager.runTask('command','')
  self.assertFalse(self.queue.running);self.assertEqual(len(self.queue.rows),1)

 def test_due_schedule_targets_original_profile(self):
  from datetime import datetime,timedelta
  date=datetime.now()+timedelta(days=1)
  self.manager.scheduleTask('command',date.strftime('%Y-%m-%d'),'23:00','daily','say Scheduled')
  self.manager.setServersRoot(str(self.base/'servers'));self.manager.addProfile('Second')
  self.bridge.server=Mock();self.bridge.server.poll.return_value=None
  self.queue.schedules.rows[0]['next_due']=0
  with patch.object(self.bridge,'command') as first,patch.object(self.manager.active,'command') as second:
   self.queue.tick();first.assert_called_once_with('say Scheduled');second.assert_not_called()
  self.assertEqual(self.queue.rows[0]['profile'],'main')
 def test_paused_schedules_are_skipped_without_enqueuing(self):
  from datetime import datetime,timedelta
  date=datetime.now()+timedelta(days=1);self.manager.scheduleTask('stop',date.strftime('%Y-%m-%d'),'23:00','daily','')
  self.queue.schedules.rows[0]['next_due']=0;self.queue.paused=True;self.queue.schedule()
  self.assertEqual(self.queue.rows,[]);self.assertIn('paused',self.queue.schedules.rows[0]['last_status'])
