import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from test_public_build import app,qt_app,HostManager
import playit_backend as pb
from settings_store import SettingsStore,validated
from server_files import Properties

class PlayitBackendTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.manager=pb.PlayitManager(Path(self.temp.name),Mock())
 def tearDown(self):self.manager.stop();self.temp.cleanup()
 def test_parser_accepts_only_loopback_targets_and_plain_public_addresses(self):
  self.assertEqual(pb.mapping('abc.ply.gg:32123 => 127.0.0.1:25565'),(25565,('abc.ply.gg',32123)))
  self.assertEqual(pb.mapping('abc.joinmc.link => 127.0.0.1:25565'),(25565,('abc.joinmc.link',None)))
  self.assertEqual(pb.mapping('[2001:db8::1]:32123 => [::1]:25565'),(25565,('2001:db8::1',32123)))
  for line in ['abc.ply.gg:32123 => 192.168.1.2:25565','https://bad.example => 127.0.0.1:25565','abc.ply.gg:99999 => 127.0.0.1:25565','abc.ply.gg:123 => (disabled)','abc.ply.gg:123 => 127.0.0.1:0']:
   self.assertIsNone(pb.mapping(line),line)
 def test_private_urls_and_raw_output_never_reach_public_state(self):
  m=self.manager;m.consume('Visit link to setup https://playit.gg/claim/0123456789');self.assertEqual(m.claim,'https://playit.gg/claim/0123456789')
  self.assertEqual(pb.claim_url('https://playit.gg/claim/0123456789'),'https://playit.gg/claim/0123456789');self.assertEqual(pb.claim_url('https://playit.gg.evil/claim/0123456789'),'')
  m.consume('login: https://playit.gg/login/guest-account/SECRET_TOKEN');m.consume('secret_key=SUPER_SECRET')
  public=json.dumps(m.snapshot());self.assertNotIn('SECRET_TOKEN',public);self.assertNotIn('SUPER_SECRET',public)
  m.consume('playit (v0.17.1): 123 tunnel running, 1 tunnels registered');m.consume('TUNNELS');m.consume('abc.ply.gg:32123 => 127.0.0.1:25565');self.assertEqual(m.address(25565),('abc.ply.gg',32123));self.assertEqual(m.claim,'')
  m.consume('TUNNELS');self.assertIsNone(m.address(25565))
 def test_shared_agent_has_one_process_and_stops_after_last_lease(self):
  m=self.manager;proc=Mock();proc.poll.return_value=None
  with patch.object(pb,'verified',return_value=True),patch.object(pb,'managed_popen',return_value=proc) as launch,patch.object(pb,'start_worker'):
   first=m.acquire('one',25565);second=m.acquire('two',25566);self.assertEqual(launch.call_count,1)
   args=launch.call_args.args[0];self.assertIn('--secret_path',args);self.assertIn('--stdout',args);self.assertEqual(args[-1],'start');self.assertNotIn('--secret',args)
   first.terminate();proc.terminate.assert_not_called();second.terminate();proc.terminate.assert_called_once();self.assertIsNotNone(first.poll())
 def test_setup_only_agent_stop_and_stale_lease_do_not_kill_restarted_agent(self):
  m=self.manager;proc=Mock();proc.poll.return_value=None
  with patch.object(pb,'verified',return_value=True),patch.object(pb,'managed_popen',return_value=proc),patch.object(pb,'start_worker'):
   old=m.acquire('one',25565);m.stop();current=m.acquire('one',25565);old.terminate();self.assertIn('one',m.leases);self.assertIsNone(current.poll())
 def test_duplicate_local_ports_are_rejected_even_between_game_protocols(self):
  m=self.manager;m.process=Mock();m.process.poll.return_value=None;m.leases={'first':25565}
  with self.assertRaisesRegex(ValueError,'different local game port'):m.acquire('second',25565)
 def test_missing_or_unverified_agent_is_never_executed(self):
  with patch.object(pb,'managed_popen') as launch:
   with self.assertRaisesRegex(ValueError,'Prepare playit'):self.manager.start()
   launch.assert_not_called()
 def test_prepare_verifies_checksum_before_atomic_install(self):
  from runtime import download
  with patch.object(pb,'WINDOWS',True),patch('runtime.download') as fetch:
   def downloaded(url,path,algorithm,checksum,limit):
    self.assertEqual(url,pb.URL);self.assertEqual(checksum,pb.SHA256);self.assertEqual(algorithm,'sha256');Path(path).write_bytes(b'MZverified')
   fetch.side_effect=downloaded;path=pb.prepare(self.temp.name,Mock());self.assertEqual(Path(path).read_bytes(),b'MZverified')
   Path(path).unlink()
   def fail(*args,**kwargs):Path(args[1]).write_bytes(b'bad');raise ValueError('checksum mismatch')
   fetch.side_effect=fail
   with self.assertRaisesRegex(ValueError,'checksum'):pb.prepare(self.temp.name,Mock())
   self.assertFalse(Path(path).exists());self.assertFalse(Path(path).with_suffix('.download').exists())
 def test_agent_status_does_not_claim_connection_until_route_reported(self):
  m=self.manager;m.process=Mock();m.process.poll.return_value=None
  self.assertNotEqual(m.tunnel_status(25565),'Connected');m.claim='https://playit.gg/claim/0123456789';self.assertIn('approval',m.tunnel_status(25565))
  m.claim='';m.connected=True;m.mappings={25565:('abc.ply.gg',32123)};self.assertEqual(m.tunnel_status(25565),'Connected')
 def test_official_api_lookup_uses_agent_config_and_excludes_disabled_or_wrong_targets(self):
  secret=pb.paths(self.temp.name)[2];secret.parent.mkdir(parents=True);secret.write_text('secret_key = "012345abcdef"\n')
  def tunnel(address,local_port,ip='127.0.0.1',**extra):
   return dict(display_address=address,agent_config={'fields':[{'name':'local_port','value':str(local_port)},{'name':'local_ip','value':ip}]},**extra)
  tunnels=[tunnel('one.joinmc.link',25565),tunnel('two.ply.gg:32123',25566),tunnel('bedrock.ply.gg:19133',19132),tunnel('disabled.ply.gg:1234',25567,disabled_reason='disabled'),tunnel('wrong.ply.gg:1234',25568,ip='192.168.1.2')]
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=json.dumps({'status':'success','data':{'tunnels':tunnels}}).encode()
  with patch.object(pb,'build_opener') as opener:
   opener.return_value.open.return_value=response
   routes=pb.assigned_tunnels(secret);request=opener.return_value.open.call_args.args[0]
   self.assertEqual(request.full_url,pb.RUN_DATA_URL);self.assertEqual(request.get_method(),'POST');self.assertEqual(request.get_header('Authorization'),'Agent-Key 012345abcdef');self.assertEqual(request.data,b'{}')
  self.assertEqual(routes,{25565:('one.joinmc.link',None),25566:('two.ply.gg',32123),19132:('bedrock.ply.gg',19133)})
 def test_api_refresh_resolves_addresses_missing_from_real_stdout(self):
  m=self.manager;m.process=Mock();m.process.poll.return_value=None
  m.consume('INFO playit (v0.17.1): 123 tunnel running, 1 tunnels registered')
  self.assertIsNone(m.address(25565))
  with patch.object(pb,'assigned_tunnels',return_value={25565:('one.joinmc.link',None)}):m.refresh_addresses(m.generation)
  self.assertEqual(m.address(25565),('one.joinmc.link',None));self.assertEqual(m.tunnel_status(25565),'Connected')
 def test_refresh_failure_and_stopped_generation_never_leave_stale_addresses_or_secrets(self):
  m=self.manager;m.process=Mock();m.process.poll.return_value=None;m.connected=True;m.mappings={25565:('old.ply.gg',1234)}
  with patch.object(pb,'assigned_tunnels',side_effect=ValueError('PRIVATE_SECRET')):m.refresh_addresses(m.generation)
  self.assertIsNone(m.address(25565));self.assertNotIn('PRIVATE_SECRET',json.dumps(m.snapshot()))
  generation=m.generation
  def stopped_lookup(*args):m.stop();return {25565:('old.ply.gg',1234)}
  with patch.object(pb,'assigned_tunnels',side_effect=stopped_lookup):m.refresh_addresses(generation)
  self.assertEqual(m.mappings,{});self.assertTrue(m.lookup_stop.is_set())
 def test_api_rejects_invalid_config_without_network_request(self):
  secret=Path(self.temp.name)/'playit.toml';secret.write_text('secret_key = "not-a-key"')
  with patch.object(pb,'build_opener') as opener:
   with self.assertRaises(ValueError):pb.assigned_tunnels(secret)
   opener.assert_not_called()

class PlayitHostingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.cache=patch.object(qt_app,'CACHE',Path(self.temp.name)/'cache');self.cache.start();self.manager=HostManager(app,qt_app.Bridge);self.s=self.manager.active
 def tearDown(self):
  self.manager.playit.stop()
  for s in self.manager.sessions.values():s.timer.stop();s.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def test_mutually_exclusive_modes_persist_without_erasing_addresses(self):
  s=self.s;s.s.update(vps_host='203.0.113.20',join_address='vps.example.com',direct_join_address='home.example.com');s.update('use_playit',True)
  self.assertFalse(s.s['use_vps']);self.assertTrue(SettingsStore(s.store.path).data['use_playit']);self.assertEqual(s.s['join_address'],'vps.example.com');self.assertEqual(s.s['direct_join_address'],'home.example.com')
  s.update('use_vps',True);self.assertFalse(s.s['use_playit']);self.assertFalse(SettingsStore(s.store.path).data['use_playit']);self.assertFalse(validated({'use_playit':True,'use_vps':True})['use_vps'])
 def test_java_binds_loopback_and_public_address_comes_from_matching_route(self):
  folder=Path(self.temp.name)/'server';folder.mkdir();(folder/'switcher-server.json').write_text(json.dumps({'engine':'Paper'}));(folder/'server.properties').write_text('server-ip=\n')
  s=self.s;s.s.update(folder=str(folder),use_vps=False,use_playit=True);s.apply_ports();self.assertEqual(Properties(folder/'server.properties').values['server-ip'],'127.0.0.1')
  self.assertIn('Configure playit',s.join_display());self.manager.playit.connected=True;self.manager.playit.mappings={25565:('abc.ply.gg',32123)}
  self.assertEqual(s.join_display(),'abc.ply.gg:32123');s.action('copy');self.assertEqual(app.clipboard().text(),'abc.ply.gg:32123');self.assertFalse(s.setJoinAddress('override.example.com'))
 def test_playit_start_and_tasks_do_not_require_a_vps(self):
  s=self.s;s.s.update(use_playit=True,use_vps=False,vps_host='');proc=Mock();proc.poll.return_value=None
  with patch.object(s,'start_server',side_effect=lambda:setattr(s,'server',proc)),patch.object(self.manager.playit,'acquire',return_value=Mock()) as acquire:
   s.action('hosting');self.assertTrue(s.pending);s.connect_tunnel();acquire.assert_called_once_with('main',25565)
   self.manager.queue.dispatch(s,'start');self.assertTrue(self.manager.queue.restore_tunnel)
  s.server=None;s.tunnel=None
 def test_copy_uses_api_route_for_selected_profile_java_and_bedrock(self):
  s=self.s;m=self.manager.playit;s.s.update(use_playit=True,use_vps=False,local_java_port=25566)
  m.process=Mock();m.process.poll.return_value=None;m.consume('INFO playit (v0.17.1): 123 tunnel running, 3 tunnels registered')
  with patch.object(pb,'assigned_tunnels',return_value={25565:('other.joinmc.link',None),25566:('selected.joinmc.link',None),19132:('bedrock.ply.gg',19133)}):m.refresh_addresses(m.generation)
  s.action('copy');self.assertEqual(app.clipboard().text(),'selected.joinmc.link')
  s.s.update(engine='Bedrock',installedEngine='Bedrock');s.action('copy');self.assertEqual(app.clipboard().text(),'bedrock.ply.gg');self.assertEqual(s.join_port(),19133)
  m.mappings={};app.clipboard().setText('keep clipboard');s.action('copy');self.assertEqual(app.clipboard().text(),'keep clipboard')
 def test_stop_all_and_updates_include_setup_only_agent(self):
  m=self.manager.playit;m.process=Mock();m.process.poll.return_value=None;proc=m.process
  with self.assertRaisesRegex(ValueError,'playit agent'):self.manager.updates_idle()
  self.manager.stopAll();proc.terminate.assert_called_once();self.assertIsNotNone(m.poll())
