"""One-level server browsing and conflict-checked text editing."""
import json
from pathlib import Path
from server_files import ServerFiles,EXTENSIONS,atomic_write,fingerprint
TEXT_EXTENSIONS=EXTENSIONS|{'.log','.md','.bat','.sh','.ps1'}

class FileBrowser(ServerFiles):
 def listing(self,relative=''):
  directory=self.root if not relative else self.path(relative)
  if not directory.is_dir():raise ValueError('Choose a server folder.')
  rows=[]
  for child in directory.iterdir():
   name=child.relative_to(self.root).as_posix()
   try:path=self.path(name);info=path.stat()
   except (OSError,ValueError):continue
   folder=path.is_dir()
   rows.append(dict(name=child.name,path=name,folder=folder,size=0 if folder else info.st_size,modified=info.st_mtime,editable=not folder and path.suffix.lower() in TEXT_EXTENSIONS and info.st_size<=2*1024**2))
  return sorted(rows,key=lambda row:(not row['folder'],row['name'].casefold()))
 def read_text(self,relative):
  path=self.path(relative)
  if path.suffix.lower() not in TEXT_EXTENSIONS:raise ValueError('This is a binary file. Choose a text configuration file to edit.')
  if path.stat().st_size>2*1024**2:raise ValueError('Editor limit is 2 MB.')
  raw=path.read_bytes()
  if b'\0' in raw:raise ValueError('Binary files cannot be edited as text.')
  try:return raw.decode('utf-8'),fingerprint(raw),'utf-8'
  except UnicodeDecodeError:return raw.decode('latin-1'),fingerprint(raw),'latin-1'
 def write_text(self,relative,text,expected,encoding):
  path=self.path(relative)
  if path.suffix.lower() not in TEXT_EXTENSIONS or '\0' in text:raise ValueError('Choose a text configuration file.')
  if relative in self.config_files():return self.write_config(relative,text,expected,encoding)
  if path.suffix.lower()=='.json':json.loads(text)
  if path.suffix.lower()=='.toml':
   try:import tomllib
   except ImportError:pass
   else:tomllib.loads(text)
  raw=text.encode(encoding)
  if len(raw)>2*1024**2:raise ValueError('Editor limit is 2 MB.')
  atomic_write(path,raw,expected);return fingerprint(raw)
