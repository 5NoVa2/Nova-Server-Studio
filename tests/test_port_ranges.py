import os
import json,os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_public_build import app,qt_app,HostManager,ROOT
from port_ranges import parse_ranges,normalize,compact
from connection_settings import Connection
from host_ports import vps_script
from settings_store import SettingsStore

class PortRangeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.cache=patch.object(qt_app,'CACHE',self.base/'cache');self.cache.start()
  self.manager=HostManager(app,qt_app.Bridge);self.manager.setServersRoot(str(self.base/'servers'))
 def tearDown(self):
  for session in self.manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  self.cache.stop();self.temp.cleanup()
 def test_parse_normalize_and_reject_invalid_input(self):
  self.assertEqual(parse_ranges(' 25565 - 25567, 25566,25580 '),[25565,25566,25567,25580])
  self.assertEqual(normalize('25567,25565-25566, 25580'),'25565-25567, 25580')
  self.assertEqual(parse_ranges(''),[]);self.assertEqual(parse_ranges('65535'),[65535])
  for value in ('0','65536','25570-25565','1-65535','25565,','25565; reboot','-1','hello',True):
   with self.subTest(value=value),self.assertRaises(ValueError):parse_ranges(value)
 def test_ranges_persist_and_invalid_save_preserves_disk(self):
  bridge=self.manager.active;bridge.update('java_port_ranges','25565-25575, 25580')
  self.assertEqual(SettingsStore(bridge.store.path).data['java_port_ranges'],'25565-25575, 25580')
  before=bridge.store.path.read_bytes();bridge.draft('java_port_ranges','30000-20000')
  self.assertFalse(bridge.save());self.assertEqual(before,bridge.store.path.read_bytes())
 def test_new_profiles_take_unique_public_ports_and_inherit_ranges(self):
  bridge=self.manager.active;bridge.update('vps_host','203.0.113.10');bridge.update('java_port_ranges','30000-30001');bridge.update('bedrock_port_ranges','20000-20001')
  self.manager.addProfile('Modded');first=self.manager.active
  self.assertEqual(first.s['remote_java_port'],30000);self.assertEqual(first.s['remote_bedrock_port'],20000)
  self.assertEqual(first.s['local_java_port'],25566)
  self.manager.addProfile('Friends');second=self.manager.active
  self.assertEqual(second.s['remote_java_port'],30001);self.assertEqual(second.s['remote_bedrock_port'],20001)
  self.assertEqual(second.store.data['java_port_ranges'],'30000-30001')
  before=len(self.manager.entries);self.manager.addProfile('Full')
  self.assertEqual(len(self.manager.entries),before);self.assertIn('All ports',self.manager.s['error']);self.assertFalse((self.base/'servers'/'Full').exists())
 def test_vps_union_includes_ranges_and_existing_profiles_without_other_vps(self):
  first=self.manager.active;first.update('vps_host','203.0.113.10');first.update('java_port_ranges','25570-25572');first.update('bedrock_port_ranges','19140-19142')
  self.manager.addProfile('Second');second=self.manager.active;second.update('java_port_ranges','25580')
  java,bedrock=self.manager.vps_ports(Connection.parse(first.s))
  self.assertEqual(java,[25565,25570,25571,25572,25580]);self.assertEqual(bedrock,[19132,19140,19141,19142])
  second.update('vps_host','203.0.113.11')
  java,_=self.manager.vps_ports(Connection.parse(first.s));self.assertNotIn(25580,java)
 def test_generated_rules_and_real_sshd_permissions(self):
  source=(ROOT/'app'/'vps_setup.sh').read_text();java=list(range(25565,25576));udp=list(range(19132,19143))
  script=vps_script(source,'root',java,udp)
  self.assertIn('ufw allow 25565:25575/tcp',script);self.assertIn('ufw allow 19132:19142/udp',script)
  bash=str(Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Git/bin/bash.exe') if os.name=='nt' else 'bash'
  subprocess.run([bash,'-n'],input=script.encode('utf-8'),check=True,capture_output=True)
  if not Path('/usr/sbin/sshd').exists():self.skipTest('sshd unavailable')
  key=self.base/'hostkey';subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
  conf=self.base/'sshd_config';conf.write_text(f'HostKey {key}\nPort 22222\nUsePAM no\n')
  # Exercise the maximum additional range plus an existing out-of-range port.
  for ports in (java,[25565]+list(range(30000,30256))):
   rendered=vps_script(source,'root',ports,udp)
   code=rendered.split("python3 - <<'PYCONF'\n",1)[1].split('\nPYCONF',1)[0].replace("Path('/etc/ssh/sshd_config')",'Path('+repr(str(conf))+')')
   exec(compile(code,'managed-config','exec'))
   result=subprocess.run(['/usr/sbin/sshd','-T','-f',str(conf),'-C','user=root,host=localhost,addr=127.0.0.1'],check=True,capture_output=True,text=True)
   expected='permitlisten '+' '.join('0.0.0.0:'+str(p) for p in ports)
   self.assertIn(expected,result.stdout)
  self.assertEqual(conf.read_text().count('Match User root\n'),1)
if __name__=='__main__':unittest.main()
