import unittest
from unittest.mock import Mock
from test_public_build import ROOT
from server_stats import ServerStats

class ServerStatsTests(unittest.TestCase):
 def test_cpu_normalization_throttling_and_stopping(self):
  clock=Mock(return_value=0);reader=Mock(side_effect=[(10,1024),(12,2048)])
  process=Mock();process.poll.return_value=None
  stats=ServerStats(reader,clock,cores=4)
  self.assertEqual(stats.sample(process),{'cpuLoad':None,'ramBytes':1024})
  clock.return_value=1;stats.sample(process);self.assertEqual(reader.call_count,1)
  clock.return_value=2;self.assertEqual(stats.sample(process),{'cpuLoad':25.0,'ramBytes':2048})
  process.poll.return_value=0;self.assertEqual(stats.sample(process),{'cpuLoad':None,'ramBytes':None})
 def test_new_process_and_failed_samples_reset_baseline(self):
  clock=Mock(return_value=0);reader=Mock(side_effect=[(10,1024),None,(50,2048),(100,4096)])
  first=Mock();first.poll.return_value=None;second=Mock();second.poll.return_value=None
  stats=ServerStats(reader,clock,cores=2);stats.sample(first)
  clock.return_value=2;self.assertIsNone(stats.sample(first)['ramBytes'])
  clock.return_value=4;self.assertIsNone(stats.sample(first)['cpuLoad'])
  self.assertEqual(stats.sample(second),{'cpuLoad':None,'ramBytes':4096})
