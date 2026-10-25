"""Saved host schedules using the PC's local wall clock; no missed-run replay."""
import calendar,json,os,tempfile,time,uuid
from datetime import datetime,timedelta
from pathlib import Path
OPERATIONS=('start','stop','save_world','backup','command')
REPEATS=('once','daily','weekdays','weekly','biweekly','monthly')


def validate_command(command):
    if not isinstance(command,str) or not command.strip() or len(command)>512 or any(c in command for c in '\r\n\x00'):
        raise ValueError('Enter one console command, up to 512 characters.')
    return command.strip()


def next_occurrence(anchor,repeat,after):
    first=datetime.fromisoformat(anchor)
    if repeat=='once':return first.timestamp() if first.timestamp()>after else None
    if repeat not in REPEATS:raise ValueError('Choose a supported repeat interval.')
    current=datetime.fromtimestamp(after)
    if repeat=='monthly':
        months=max(0,(current.year-first.year)*12+current.month-first.month)
        for offset in range(months,months+3):
            year,month=divmod(first.year*12+first.month-1+offset,12);month+=1
            candidate=first.replace(year=year,month=month,day=min(first.day,calendar.monthrange(year,month)[1]))
            if candidate.timestamp()>after:return candidate.timestamp()
    else:
        step=7 if repeat=='weekly' else 14 if repeat=='biweekly' else 1
        days=max(0,(current.date()-first.date()).days)
        base=days//step*step
        for offset in range(base,base+step*10,step):
            candidate=first+timedelta(days=offset)
            if repeat=='weekdays' and candidate.weekday()>=5:continue
            if candidate.timestamp()>after:return candidate.timestamp()
    raise ValueError('Could not find the next scheduled date.')

def anchor_from_time(hour,minute,meridiem,repeat,now=None):
    now=time.time() if now is None else now
    if type(hour) is not int or type(minute) is not int or not 1<=hour<=12 or not 0<=minute<=59 or meridiem not in ('AM','PM') or repeat not in REPEATS:
        raise ValueError('Choose an hour, minute, AM/PM and repeat interval.')
    current=datetime.fromtimestamp(now)
    candidate=current.replace(hour=(hour%12)+(12 if meridiem=='PM' else 0),minute=minute,second=0,microsecond=0)
    if candidate.timestamp()<=now:candidate+=timedelta(days=1)
    while repeat=='weekdays' and candidate.weekday()>=5:candidate+=timedelta(days=1)
    return candidate

class ScheduleStore:
 def __init__(self,path,now=None):
    self.path=Path(path);self.rows=[];self.warning='';now=time.time() if now is None else now
    try:
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data,list) or len(data)>100:raise ValueError('Invalid schedules file')
        seen=set()
        for row in data:
            if not isinstance(row,dict) or row['operation'] not in OPERATIONS or row['repeat'] not in REPEATS or not isinstance(row['profile'],str):raise ValueError('Invalid schedule')
            if not isinstance(row['id'],str) or row['id'] in seen:raise ValueError('Invalid schedule identifier')
            datetime.fromisoformat(row['anchor']);seen.add(row['id'])
            if row['operation']=='command':validate_command(row.get('command',''))
            if row.get('enabled') and float(row.get('next_due') or 0)<=now:
                row['next_due']=next_occurrence(row['anchor'],row['repeat'],now);row['enabled']=row['next_due'] is not None;row['last_status']='Missed while Nova was closed'
        self.rows=data
        if self.rows:self.save()
    except FileNotFoundError:pass
    except (OSError,ValueError,KeyError,TypeError,OverflowError):
        self.rows=[];self.warning='Saved schedules could not be loaded. The original file is preserved.'
 def save(self):
    self.path.parent.mkdir(parents=True,exist_ok=True);name=None
    try:
        with tempfile.NamedTemporaryFile('w',dir=self.path.parent,prefix='.schedule-',delete=False,encoding='utf-8') as f:
            name=f.name;json.dump(self.rows,f,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(name,self.path)
    finally:
        if name:Path(name).unlink(missing_ok=True)
 def add(self,profile,server,operation,date,clock,repeat,now=None,command=''):
    now=time.time() if now is None else now
    if operation not in OPERATIONS or repeat not in REPEATS:raise ValueError('Choose a supported host task and repeat interval.')
    if operation=='command':command=validate_command(command)
    if len(self.rows)>=100:raise ValueError('Keep at most 100 schedules.')
    try:anchor=datetime.strptime(date.strip()+' '+clock.strip(),'%Y-%m-%d %H:%M')
    except ValueError:raise ValueError('Use a date YYYY-MM-DD and a 24-hour time HH:MM.') from None
    if anchor.timestamp()<=now:raise ValueError('Choose a future first run date and time.')
    normalized=datetime.fromtimestamp(anchor.timestamp())
    if normalized!=anchor:raise ValueError('That local time does not exist because of a clock change. Choose another time.')
    row=dict(id=uuid.uuid4().hex,profile=profile,server=server,operation=operation,command=command,repeat=repeat,anchor=anchor.isoformat(),next_due=next_occurrence(anchor.isoformat(),repeat,now),enabled=True,last_status='Scheduled')
    self.rows.append(row)
    try:self.save()
    except Exception:self.rows.pop();raise
    return row
 def due(self,now=None,paused=False):
    now=time.time() if now is None else now;ready=[];changed=False
    before=[dict(row) for row in self.rows]
    for row in self.rows:
        if not row.get('enabled') or float(row.get('next_due') or 0)>now:continue
        changed=True
        if not paused:ready.append(dict(row))
        row['last_status']='Skipped while paused' if paused else 'Queued'
        row['last_run']=now;row['next_due']=next_occurrence(row['anchor'],row['repeat'],now);row['enabled']=row['next_due'] is not None
    if changed:
        try:self.save()
        except Exception:self.rows=before;raise
    return ready,changed
 def enable(self,identifier,enabled,now=None):
    now=time.time() if now is None else now
    row=next(r for r in self.rows if r['id']==identifier);old=dict(row)
    row['enabled']=bool(enabled)
    if enabled:
        row['next_due']=next_occurrence(row['anchor'],row['repeat'],now)
        if row['next_due'] is None:row.update(old);raise ValueError('This one-time date has passed. Add a new schedule.')
    try:self.save()
    except Exception:row.update(old);raise
 def remove(self,identifier):
    old=self.rows;self.rows=[r for r in self.rows if r['id']!=identifier]
    try:self.save()
    except Exception:self.rows=old;raise
