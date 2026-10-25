import hashlib,os,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import ssh_backend,updater,private_files

class SecurityTests(unittest.TestCase):
 def tunnel(self):
  client=Mock()
  return ssh_backend.ReverseTunnel(client,Mock())
 def test_flood_does_not_spawn_more_than_limit(self):
  tunnel=self.tunnel()
  with patch.object(ssh_backend.threading,'Thread') as worker:
   channels=[Mock() for _ in range(65)]
   for channel in channels:tunnel.accept(channel,None,None)
   self.assertEqual(worker.call_count,64)
   channels[-1].close.assert_called_once()
 def test_slot_returned_after_connect_failure(self):
  tunnel=self.tunnel();tunnel.slots=threading.BoundedSemaphore(1)
  tunnel.slots.acquire()
  with patch.object(ssh_backend.socket,'create_connection',side_effect=OSError('failure')):
   tunnel.bridge(Mock())
  self.assertTrue(tunnel.slots.acquire(blocking=False))
 def test_stopped_tunnel_rejects_without_thread(self):
  tunnel=self.tunnel();tunnel.terminate();channel=Mock()
  with patch.object(ssh_backend.threading,'Thread') as worker:
   tunnel.accept(channel,None,None);worker.assert_not_called()
  channel.close.assert_called_once()
 def test_failed_thread_start_returns_slot(self):
  tunnel=self.tunnel();tunnel.slots=threading.BoundedSemaphore(1)
  with patch.object(ssh_backend.threading,'Thread') as worker:
   worker.return_value.start.side_effect=RuntimeError('no threads')
   with self.assertRaises(RuntimeError):tunnel.accept(Mock(),None,None)
  self.assertTrue(tunnel.slots.acquire(blocking=False))
 def test_no_publisher_blocks_install(self):
  with patch.object(updater.os,'name','nt'),patch.object(updater,'TRUSTED_PUBLISHER_THUMBPRINTS',()):
   with self.assertRaisesRegex(ValueError,'trusted publisher'):updater.launch_after_exit('missing.exe','a'*64)
 def test_acl_failure_blocks_startup(self):
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)
   with patch.object(private_files.os,'name','nt'),patch.dict(os.environ,{'SystemRoot':'C:/Windows'}),patch.object(private_files,'Path',return_value=folder),patch.object(private_files.subprocess,'run',return_value=Mock(returncode=1)):
    with self.assertRaisesRegex(ValueError,'Could not protect'):private_files.protect_agent_directory(folder)
 def test_posix_credentials_private(self):
  if os.name=='nt':self.skipTest('POSIX permissions')
  with tempfile.TemporaryDirectory() as temp:
   secret=Path(temp)/'playit.toml';secret.write_text('secret');secret.chmod(0o666)
   private_files.protect_agent_directory(temp)
   self.assertEqual(secret.stat().st_mode & 0o777,0o600)
   self.assertEqual(Path(temp).stat().st_mode & 0o777,0o700)

 def test_signature_checked_before_exit_and_in_handoff(self):
  with tempfile.TemporaryDirectory() as temp:
   installer=Path(temp)/'installer.exe';installer.write_bytes(b'MZtest')
   digest=hashlib.sha256(installer.read_bytes()).hexdigest()
   with patch.object(updater.os,'name','nt'),patch.object(updater,'Path',return_value=installer),patch.dict(os.environ,{'SystemRoot':'C:/Windows'}),patch.object(updater,'TRUSTED_PUBLISHER_THUMBPRINTS',('A'*40,)),patch.object(updater.subprocess,'run',return_value=Mock(returncode=0)) as verify,patch.object(updater.subprocess,'Popen') as launch:
    updater.launch_after_exit(str(installer),digest,pid=123)
    self.assertIn('Get-AuthenticodeSignature',verify.call_args.args[0][-1])
    script=launch.call_args.args[0][-1]
    self.assertIn('Get-AuthenticodeSignature',script)
    self.assertIn('A'*40,script)
    self.assertLess(script.index('Get-AuthenticodeSignature'),script.index('Start-Process'))
 def test_invalid_signature_never_launches(self):
  with tempfile.TemporaryDirectory() as temp:
   installer=Path(temp)/'installer.exe';installer.write_bytes(b'MZtest')
   digest=hashlib.sha256(installer.read_bytes()).hexdigest()
   with patch.object(updater.os,'name','nt'),patch.object(updater,'Path',return_value=installer),patch.dict(os.environ,{'SystemRoot':'C:/Windows'}),patch.object(updater,'TRUSTED_PUBLISHER_THUMBPRINTS',('A'*40,)),patch.object(updater.subprocess,'run',return_value=Mock(returncode=3)),patch.object(updater.subprocess,'Popen') as launch:
    with self.assertRaisesRegex(ValueError,'signature'):updater.launch_after_exit(str(installer),digest)
    launch.assert_not_called()
