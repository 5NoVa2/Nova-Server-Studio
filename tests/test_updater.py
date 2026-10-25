import hashlib,io,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from test_public_build import app,qt_app,HostManager
import updater


def release(tag,**values):
 row={'tag_name':tag,'draft':False,'prerelease':'beta' in tag,'body':'Changes','assets':[{'name':name,'browser_download_url':f'https://github.com/{updater.REPO}/releases/download/{tag}/{name}'} for name in ('SaturnSetup.exe','SHA256SUMS.txt')]}
 row.update(values);return row

class UpdaterTests(unittest.TestCase):
 def setUp(self):
  override=patch.object(updater,'PRIVATE_BUILD',False);override.start();self.addCleanup(override.stop)
 def test_release_order_handles_betas_and_stable(self):
  self.assertGreater(updater.version_key('1.0.0'),updater.version_key('1.0.0-beta.99'))
  rows=[release('v1.0.0-beta.10'),release('v1.0.0-beta.3'),release('v1.0.0-beta.20',draft=True)]
  self.assertEqual(updater.select_release(rows,'1.0.0-beta.4')['version'],'v1.0.0-beta.10')
  self.assertIsNone(updater.select_release(rows,'1.0.0'))
 def test_missing_assets_and_unknown_tags_are_skipped(self):
  self.assertIsNone(updater.select_release([release('v1.0.1',assets=[]),release('unsafe')] ,'1.0.0'))
 def test_foreign_or_insecure_asset_urls_rejected(self):
  for url in ('http://github.com/x','https://evil.test/SaturnSetup.exe','https://github.com/other/repo/releases/download/v1.0.1/SaturnSetup.exe'):
   with self.assertRaises(ValueError):updater.asset_url(url,'v1.0.1','SaturnSetup.exe')
 def test_checksum_requires_unique_exact_filename(self):
  digest='a'*64
  self.assertEqual(updater.installer_checksum((digest+'  SaturnSetup.exe\n').encode()),digest)
  for data in ('bad  SaturnSetup.exe',digest+' other.exe',(digest+' SaturnSetup.exe\n')*2):
   with self.assertRaises(ValueError):updater.installer_checksum(data.encode())
 def test_verified_download_and_corruption_cleanup(self):
  info=updater.select_release([release('v1.0.1')],'1.0.0');data=b'MZinstaller';digest=hashlib.sha256(data).hexdigest()
  with tempfile.TemporaryDirectory() as temp,patch.object(updater,'fetch_bytes',return_value=(digest+'  SaturnSetup.exe\n').encode()):
   with patch.object(updater,'urlopen',return_value=io.BytesIO(data)):
    path,expected=updater.download_update(info,temp);self.assertEqual(expected,digest);self.assertEqual(Path(path).read_bytes(),data)
   with patch.object(updater,'urlopen',return_value=io.BytesIO(b'MZcorrupt')):
    with self.assertRaisesRegex(ValueError,'checksum mismatch'):updater.download_update(info,temp)
   self.assertEqual(len(list((Path(temp)/'updates').iterdir())),1)
 def test_install_blocked_by_any_other_running_profile(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(qt_app,'CACHE',Path(temp)/'cache'):
   manager=HostManager(app,qt_app.Bridge);manager.setServersRoot(str(Path(temp)/'servers'));first=manager.active
   manager.addProfile('Other');manager.active.server=Mock();manager.active.server.poll.return_value=None
   manager.selectProfile(0);manager.update_download=('installer.exe','a'*64)
   with patch.object(updater,'launch_after_exit') as launch:
    manager.update_action('install_update');launch.assert_not_called();self.assertIn('Stop all',manager.update_status)
   for session in manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
 def test_install_confirmation_then_save_before_handoff(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(qt_app,'CACHE',Path(temp)/'cache'):
   manager=HostManager(app,qt_app.Bridge);manager.update_download=('installer.exe','a'*64)
   with patch.object(updater,'launch_after_exit') as launch,patch.object(manager,'_exit') as exit_app:
    manager.update_action('install_update');launch.assert_not_called();self.assertIn('verified installer',manager.s['dialog'])
    manager.active.answer(False);launch.assert_not_called()
    manager.update_action('install_update');manager.active.answer(True)
    launch.assert_called_once_with('installer.exe','a'*64);exit_app.assert_called_once()
   for session in manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
if __name__=='__main__':unittest.main()
