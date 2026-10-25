import tempfile,unittest,json
from pathlib import Path
from datetime import datetime
from schedules import ScheduleStore,next_occurrence

def stamp(text):return datetime.fromisoformat(text).timestamp()
class ScheduleTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'schedules.json';self.store=ScheduleStore(self.path,now=stamp('2026-01-01T00:00:00'))
 def tearDown(self):self.temp.cleanup()
 def test_daily_weekly_biweekly_and_weekdays(self):
  anchor='2026-01-02T14:30:00'
  for repeat,expected in [('daily','2026-01-03T14:30:00'),('weekdays','2026-01-05T14:30:00'),('weekly','2026-01-09T14:30:00'),('biweekly','2026-01-16T14:30:00')]:
   self.assertEqual(next_occurrence(anchor,repeat,stamp(anchor)),stamp(expected))
 def test_monthly_restores_anchor_day_after_short_month(self):
  anchor='2026-01-31T10:00:00'
  self.assertEqual(next_occurrence(anchor,'monthly',stamp(anchor)),stamp('2026-02-28T10:00:00'))
  self.assertEqual(next_occurrence(anchor,'monthly',stamp('2026-02-28T10:00:00')),stamp('2026-03-31T10:00:00'))
 def add(self,repeat='daily',operation='backup',command=''):
  return self.store.add('main','My server',operation,'2026-01-02','14:30',repeat,now=stamp('2026-01-01T00:00:00'),command=command)
 def test_persistence_and_due_run_is_not_repeated(self):
  row=self.add();due=stamp('2026-01-02T14:30:00');loaded=ScheduleStore(self.path,now=due-1)
  ready,_=loaded.due(due);self.assertEqual(len(ready),1)
  self.assertEqual(loaded.due(due)[0],[]);again=ScheduleStore(self.path,now=due+1);self.assertEqual(again.rows[0]['next_due'],stamp('2026-01-03T14:30:00'))
 def test_closed_runs_are_skipped_not_replayed(self):
  self.add();loaded=ScheduleStore(self.path,now=stamp('2026-01-05T17:00:00'))
  self.assertEqual(loaded.rows[0]['next_due'],stamp('2026-01-06T14:30:00'));self.assertIn('Missed',loaded.rows[0]['last_status'])
 def test_one_time_and_pause(self):
  row=self.add('once');self.store.due(stamp('2026-01-02T14:30:00'),paused=True)
  self.assertFalse(row['enabled']);self.assertIn('paused',row['last_status'])
 def test_custom_command_is_saved(self):
  self.add(operation='command',command='say Scheduled notice');self.assertEqual(json.loads(self.path.read_text())[0]['command'],'say Scheduled notice')
 def test_validation_and_toggle_remove(self):
  with self.assertRaises(ValueError):self.store.add('main','Server','stop','invalid','25:00','daily')
  with self.assertRaises(ValueError):self.store.add('main','Server','stop','2020-01-01','12:00','once')
  row=self.add();self.store.enable(row['id'],False);self.assertFalse(self.store.rows[0]['enabled']);self.store.remove(row['id']);self.assertEqual(self.store.rows,[])
 def test_dateless_time_picker_handles_am_pm_and_rollover(self):
  from schedules import anchor_from_time
  now=stamp('2026-01-02T10:00:00')
  self.assertEqual(anchor_from_time(12,0,'PM','daily',now).timestamp(),stamp('2026-01-02T12:00:00'))
  self.assertEqual(anchor_from_time(12,5,'AM','daily',now).timestamp(),stamp('2026-01-03T00:05:00'))
  self.assertEqual(anchor_from_time(1,5,'PM','weekly',now).timestamp(),stamp('2026-01-02T13:05:00'))
 def test_dateless_weekdays_skip_weekend(self):
  from schedules import anchor_from_time
  self.assertEqual(anchor_from_time(9,30,'AM','weekdays',stamp('2026-01-02T10:00:00')).timestamp(),stamp('2026-01-05T09:30:00'))
 def test_time_picker_rejects_invalid_values(self):
  from schedules import anchor_from_time
  for values in [(0,30,'AM'),(13,30,'PM'),(1,60,'AM'),(1,0,'xx')]:
   with self.assertRaises(ValueError):anchor_from_time(*values,'daily')
