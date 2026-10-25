"""Four host actions, serialized execution and persisted calendar schedules."""
import time,uuid
from PySide6.QtCore import QObject,QTimer
from schedules import ScheduleStore
LABELS={'start':'Start','stop':'Stop','save_world':'Save world','backup':'Backup','command':'Custom command'}

class HostTaskQueue(QObject):
 def __init__(self,owner):
  super().__init__(owner);self.owner=owner;self.rows=[];self.current=None;self.running=False;self.paused=False;self.phase='';self.deadline=0;self.restore_tunnel=False;self.was_running=False
  self.schedules=ScheduleStore(owner.cache/'task-schedules.json')
  if self.schedules.warning:owner.active.log(self.schedules.warning)
  self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(250)
 def add(self,profile,operation,automatic=False,schedule_id='',command=''):
  if operation not in LABELS:raise ValueError('Choose Start, Stop, Save world, Backup or Custom command.')
  if operation=='command':
   from schedules import validate_command
   command=validate_command(command)
  if len(self.rows)>=100:self.rows=[r for r in self.rows if r['status'] in ('Queued','Running')]
  if len(self.rows)>=100:raise ValueError('Keep at most 100 queued tasks.')
  entry=next(e for e in self.owner.entries if e['id']==profile)
  self.rows.append(dict(id=uuid.uuid4().hex,profile=profile,server=entry['name'],operation=operation,label=LABELS[operation],command=command,status='Queued',detail='',automatic=automatic,schedule_id=schedule_id));self.owner.changed.emit()
 def references(self,profile):return any(r['profile']==profile and r['status'] in ('Queued','Running') for r in self.rows) or any(r['profile']==profile and r.get('enabled') for r in self.schedules.rows)
 def remove(self,identifier):
  self.rows=[r for r in self.rows if r['id']!=identifier or r['status']=='Running'];self.owner.changed.emit()
 def finish(self,error=''):
  row=self.current;row.update(status='Failed' if error else 'Completed',detail=str(error) if error else row.get('detail',''));self.current=None
  for schedule in self.schedules.rows:
   if schedule['id']==row.get('schedule_id'):schedule['last_status']=row['status']+(': '+str(error) if error else '')
  try:self.schedules.save()
  except OSError as failure:self.owner.active.log('Could not save schedule result: '+str(failure))
  if error:self.running=False;self.paused=True
  self.owner.changed.emit()
 def phase_to(self,value,seconds=300):self.phase=value;self.deadline=time.monotonic()+seconds
 def begin_backup(self,session):self.phase_to('backup_copy',3600);session.action('backup')
 def dispatch(self,session,operation):
  session.publish(error='');self.restore_tunnel=False;self.was_running=session.active(session.server)
  if operation=='command':
   self.phase_to('instant',120);session.command(self.current['command']);self.current['detail']='Command sent; check the console for its result.'
  elif operation=='stop':self.phase_to('stopping',120);session.stop()
  elif operation=='backup':
   self.restore_tunnel=session.active(session.tunnel)
   if self.was_running or self.restore_tunnel:self.phase_to('stopping',120);session.stop()
   else:self.begin_backup(session)
  elif operation=='save_world':
   if not self.was_running:raise ValueError('Start the server before saving its world.')
   if session.running_engine=='Bedrock':
    self.restore_tunnel=session.active(session.tunnel);self.phase_to('stopping',120);session.stop()
   else:self.phase_to('saving',120);session.world_saved.clear();session.command('save-all flush')
  else:
   self.restore_tunnel=bool(session.s.get('vps_host'));self.phase_to('starting');session.action('start')
 def schedule(self):
  try:
   ready,changed=self.schedules.due(paused=self.paused)
   for row in ready:
    if row['profile'] not in self.owner.sessions:row['last_status']='Profile missing';continue
    if any(r.get('schedule_id')==row['id'] and r['status'] in ('Queued','Running') for r in self.rows):continue
    self.add(row['profile'],row['operation'],True,row['id'],row.get('command',''))
   if changed:self.owner.changed.emit()
  except Exception as error:self.paused=True;self.running=False;self.owner.active.error('Schedule error: '+str(error))
 def tick(self):
  if self.owner.exiting:self.running=False;return
  self.schedule()
  if self.current is None:
   if self.paused:return
   row=next((r for r in self.rows if r['status']=='Queued' and (self.running or r.get('automatic'))),None)
   if row is None:
    if self.running:self.running=False;self.owner.changed.emit()
    return
   session=self.owner.sessions.get(row['profile'])
   if session is None:self.current=row;self.finish('Server profile no longer exists.');return
   if session.s['busy'] or session.s['dialog'] or session.pending:return
   self.current=row;row['status']='Running';self.owner.changed.emit()
   try:self.dispatch(session,row['operation'])
   except Exception as error:self.finish(error);return
  session=self.owner.sessions[self.current['profile']]
  if session.s['error']:self.finish(session.s['error']);return
  if time.monotonic()>self.deadline:self.finish('Task timed out. Check the server console before resuming.');return
  if session.s['busy'] or session.s['dialog']:return
  op=self.current['operation']
  if self.phase=='stopping':
   if session.active(session.server) or session.active(session.tunnel):return
   if op=='backup':self.begin_backup(session);return
   if op=='save_world':
    self.phase_to('starting')
    try:session.start_server()
    except Exception as error:self.finish(error)
    return
  elif self.phase=='backup_copy':
   if self.was_running:
    self.phase_to('starting')
    try:session.start_server()
    except Exception as error:self.finish(error)
    return
  elif self.phase=='saving':
   if not session.active(session.server):self.finish('Server stopped before save confirmation.');return
   if not session.world_saved.is_set():return
  elif self.phase=='starting':
   if not session.active(session.server):self.finish('Server exited before becoming ready. Check its console.');return
   if not session.ready.is_set():return
   if self.restore_tunnel:
    self.restore_tunnel=False;self.phase_to('reconnect')
    try:session.connect_tunnel()
    except Exception as error:self.finish(error)
    return
  elif self.phase=='reconnect' and not session.active(session.tunnel):self.finish('Tunnel did not reconnect.');return
  self.finish()
