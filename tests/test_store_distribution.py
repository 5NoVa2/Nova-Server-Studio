import importlib.util,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch,Mock
from test_public_build import app,qt_app,HostManager,ROOT
import hosts,updater,ssh_backend

class StoreDistributionTests(unittest.TestCase):
 def test_store_backend_blocks_all_external_update_paths(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(qt_app,'CACHE',Path(temp)),patch.object(hosts,'STORE_BUILD',True):
   manager=HostManager(app,qt_app.Bridge)
   with patch.object(updater,'check_updates') as check,patch.object(updater,'download_update') as download,patch.object(updater,'launch_after_exit') as install:
    for action in ['check_updates','download_update','install_update']:manager.update_action(action)
    check.assert_not_called();download.assert_not_called();install.assert_not_called()
   self.assertTrue(manager.state['updateStore']);self.assertIn('Microsoft Store',manager.state['updateStatus'])
   manager.queue.timer.stop()
   for session in manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
  with patch.object(updater,'STORE_BUILD',True):
   for action in [updater.check_updates,lambda:updater.download_update({},Path(temp)),lambda:updater.launch_after_exit('unused','unused')]:
    with self.assertRaisesRegex(ValueError,'Microsoft Store'):action()
 def test_store_ssh_uses_bundled_library_without_pip(self):
  sentinel=object()
  with patch.object(ssh_backend,'STORE_BUILD',True),patch.object(ssh_backend.importlib,'import_module',return_value=sentinel),patch.object(ssh_backend,'managed_popen') as process:
   self.assertIs(ssh_backend.ensure_ssh(lambda text:None),sentinel);process.assert_not_called()
  with patch.object(ssh_backend,'STORE_BUILD',True),patch.object(ssh_backend.importlib,'import_module',side_effect=ImportError),patch.object(ssh_backend,'managed_popen') as process:
   with self.assertRaisesRegex(RuntimeError,'Repair Saturn'):ssh_backend.ensure_ssh(lambda text:None)
   process.assert_not_called()
 def test_manifest_identity_namespace_and_submission_guard(self):
  spec=importlib.util.spec_from_file_location('saturn_manifest',ROOT/'store/generate_manifest.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as temp:
   target=Path(temp)/'AppxManifest.xml'
   module.generate(target,'SaturnServerLauncher.Preview','CN=SaturnDevelopment','Nova','1.0.17.0',True)
   manifest=ET.parse(target).getroot();ns={'f':module.F,'r':module.R}
   self.assertEqual(manifest.find('f:Identity',ns).get('ProcessorArchitecture'),'x64')
   self.assertEqual(manifest.find('f:Capabilities/r:Capability',ns).get('Name'),'runFullTrust')
   with self.assertRaisesRegex(ValueError,'Preview identity'):module.generate(target,'SaturnServerLauncher.Preview','CN=SaturnDevelopment','Nova','1.0.17.0')
   with self.assertRaisesRegex(ValueError,'fourth'):module.generate(target,'Company.Saturn','CN=123456','Nova','1.0.17.1')
