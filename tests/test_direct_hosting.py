import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from test_public_build import app,qt_app,HostManager
from settings_store import SettingsStore,validated
from server_files import Properties

class DirectHostingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.cache=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.session=self.manager.active
 def tearDown(self):
  for s in self.manager.sessions.values():s.timer.stop();s.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def fixture(self,engine='Vanilla'):
  folder=Path(self.temp.name)/'server';folder.mkdir(exist_ok=True)
  (folder/'switcher-server.json').write_text(json.dumps({'engine':engine}))
  (folder/'server.properties').write_text('motd=Keep this world\nserver-ip=127.0.0.1\nonline-mode=false\n')
  self.session.s['folder']=str(folder);return folder
 def test_java_binding_round_trip_and_editor_enforces_selected_mode(self):
  folder=self.fixture();self.session.update('use_vps',False);self.session.s['local_java_port']=25568;self.session.apply_ports()
  doc=Properties(folder/'server.properties');self.assertEqual(doc.values['server-ip'],'');self.assertEqual(doc.values['server-port'],'25568');self.assertEqual(doc.values['online-mode'],'true')
  doc.save({'server-ip':'127.0.0.1','motd':'Edited'});self.assertEqual(Properties(doc.path).values['server-ip'],'')
  self.session.update('use_vps',True);self.session.apply_ports();doc=Properties(doc.path)
  self.assertEqual(doc.values['server-ip'],'127.0.0.1');self.assertEqual(doc.values['motd'],'Edited')
 def test_direct_join_ignores_saved_vps_and_preserves_both_addresses(self):
  s=self.session;s.update('vps_host','203.0.113.20');s.setJoinAddress('vps.example.com');s.update('use_vps',False)
  self.assertIn('Set direct',s.join_display());app.clipboard().setText('unchanged');s.action('copy');self.assertEqual(app.clipboard().text(),'unchanged')
  s.setJoinAddress('home.example.com');s.update('direct_java_port',25580);s.update('remote_java_port',25590)
  self.assertEqual(s.join_display(),'home.example.com:25580');s.action('copy');self.assertEqual(app.clipboard().text(),'home.example.com:25580')
  stored=SettingsStore(s.store.path).data;self.assertFalse(stored['use_vps']);self.assertEqual(stored['join_address'],'vps.example.com');self.assertEqual(stored['direct_join_address'],'home.example.com')
  s.update('use_vps',True);self.assertEqual(s.join_display(),'vps.example.com:25590')
 def test_direct_start_and_scheduled_start_never_request_ssh(self):
  s=self.session;s.s.update(use_vps=False,vps_host='203.0.113.20');proc=Mock();proc.poll.return_value=None
  def started():s.server=proc
  with patch.object(s,'start_server',side_effect=started),patch.object(s,'connect_tunnel') as tunnel:
   s.action('hosting');self.assertFalse(s.pending);tunnel.assert_not_called()
   self.manager.queue.dispatch(s,'start');self.assertFalse(self.manager.queue.restore_tunnel);tunnel.assert_not_called()
  with self.assertRaisesRegex(ValueError,'off'):s.connect_tunnel()
  s.server=None
 def test_mode_change_is_blocked_while_server_or_tunnel_active(self):
  s=self.session;proc=Mock();proc.poll.return_value=None
  for attr in ('server','tunnel'):
   setattr(s,attr,proc);s.update('use_vps',False);self.assertTrue(s.s['use_vps']);setattr(s,attr,None)
  s.update('use_vps','false');self.assertTrue(s.s['use_vps'])
 def test_bedrock_direct_ports_and_new_profile_inheritance(self):
  folder=self.fixture('Bedrock');s=self.session;s.s.update(use_vps=False,engine='Bedrock',installedEngine='Bedrock',tunnel_type='Java',local_bedrock_port=19140,bedrock_ipv6_port=19141,direct_bedrock_port=19200)
  s.setJoinAddress('home.example.com');s.apply_ports();doc=Properties(folder/'server.properties')
  self.assertEqual(doc.values['server-port'],'19140');self.assertEqual(doc.values['server-portv6'],'19141');self.assertEqual(s.join_display(),'home.example.com : 19200 (Bedrock UDP)')
  s.action('copy');self.assertEqual(app.clipboard().text(),'home.example.com')
  self.manager.setServersRoot(str(Path(self.temp.name)/'servers'));self.manager.addProfile('Second');new=self.manager.active
  self.assertFalse(new.s['use_vps']);self.assertEqual(new.s['direct_join_address'],'home.example.com');self.assertEqual(new.s['direct_java_port'],new.s['local_java_port']);self.assertEqual(new.s['direct_bedrock_port'],new.s['local_bedrock_port'])
 def test_direct_profile_creation_ignores_exhausted_vps_range_and_allocates_public_port(self):
  s=self.session;s.s.update(use_vps=False,vps_host='203.0.113.20',java_port_ranges='25565',direct_java_port=25566)
  self.manager.setServersRoot(str(Path(self.temp.name)/'servers'));self.manager.addProfile('Second')
  self.assertEqual(len(self.manager.entries),2);self.assertEqual(self.manager.active.s['local_java_port'],25566);self.assertEqual(self.manager.active.s['direct_java_port'],25567)
 def test_old_preferences_keep_tunnel_behavior_and_direct_input_validates(self):
  self.assertTrue(validated({'vps_host':'203.0.113.20'})['use_vps']);self.assertEqual(validated({'direct_java_port':70000})['direct_java_port'],25565)
  s=self.session;s.update('use_vps',False);self.assertFalse(s.setJoinAddress('https://bad.example:123'));self.assertEqual(s.s['direct_join_address'],'')
