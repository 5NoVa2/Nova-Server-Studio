"""Per-user preferences; atomic writes, no passwords or private-key contents."""
from connection_settings import DEFAULTS as CONNECTION_DEFAULTS,host,username,port
import json
import os
import tempfile
import uuid
from pathlib import Path

DEFAULT_FOLDER = str(Path.home()/'MinecraftServer')
DEFAULTS = {'folder': DEFAULT_FOLDER, 'version': 'latest', 'ram': 4, 'java_version':'Auto', 'key': '', 'engine': 'Vanilla', 'loader': 'recommended', 'cf_pack': {}, 'friends': [], 'auto_whitelist_friends': True, 'auto_backup_enabled':False, 'auto_backup_minutes':30, 'startup_animation':True, 'startup_sound':True, 'sound_enabled':True, 'sound_volume':0.3, 'tunnel_type':'Auto', 'use_vps':True, 'use_playit':False, 'direct_join_address':'', 'direct_java_port':25565, 'direct_bedrock_port':19132, 'java_port_ranges':'', 'bedrock_port_ranges':'', 'local_java_port':25565, 'remote_java_port':25565, 'local_bedrock_port':19132, 'remote_bedrock_port':19132, 'bedrock_ipv6_port':19133, **CONNECTION_DEFAULTS}


def validated(data):
    result = dict(DEFAULTS)
    if not isinstance(data, dict):
        return result
    from friends import normalized_friends
    result['friends']=normalized_friends(data.get('friends',[]))
    result['auto_whitelist_friends']=data.get('auto_whitelist_friends',True) is True
    from port_ranges import RANGE_KEYS,normalize
    for key in RANGE_KEYS:
        try:result[key]=normalize(data.get(key,''))
        except ValueError:pass
    if data.get('java_version') in ('Auto','8','11','17','21','25'):result['java_version']=data['java_version']
    result['sound_enabled']=bool(data.get('sound_enabled',True))
    result['startup_sound']=bool(data.get('startup_sound',True))
    volume=data.get('sound_volume',0.3)
    if isinstance(volume,(int,float)) and not isinstance(volume,bool) and 0<=volume<=1:result['sound_volume']=float(volume)
    result['startup_animation']=bool(data.get('startup_animation',True))
    result['auto_backup_enabled']=bool(data.get('auto_backup_enabled',False))
    minutes=data.get('auto_backup_minutes',30)
    if isinstance(minutes,int) and not isinstance(minutes,bool) and 5<=minutes<=1440:result['auto_backup_minutes']=minutes
    result['reduced']=bool(data.get('reduced',False))
    result['use_playit']=data.get('use_playit',False) is True
    result['use_vps']=data.get('use_vps',True) if isinstance(data.get('use_vps',True),bool) else True
    if result['use_playit']:result['use_vps']=False
    for key in ('direct_java_port','direct_bedrock_port'):
        try:result[key]=port(data.get(key,DEFAULTS[key]))
        except ValueError:pass
    try:result['direct_join_address']=host(data['direct_join_address']) if data.get('direct_join_address') else ''
    except (ValueError,UnicodeError):pass
    if data.get('tunnel_type') in ('Auto','Java','Bedrock'):result['tunnel_type']=data['tunnel_type']
    for key in ('local_java_port','remote_java_port','local_bedrock_port','remote_bedrock_port','bedrock_ipv6_port'):
        try:result[key]=port(data.get(key,DEFAULTS[key]))
        except ValueError:pass
    for name in ('folder', 'version', 'key'):
        value = data.get(name)
        if isinstance(value, str) and (value.strip() or name == 'key'):
            result[name] = value
    if data.get('engine') in ('Vanilla','Paper','Spigot','Forge','CurseForge','Bedrock'):
        result['engine'] = data['engine']
    if isinstance(data.get('loader'),str):result['loader'] = data['loader']
    pack=data.get('cf_pack')
    if isinstance(pack,dict) and all(isinstance(pack.get(k),int) and pack[k]>0 for k in ('project_id','file_id')):
        result['cf_pack']={k:pack[k] for k in ('project_id','file_id')}
        for k in ('name','release'):
            result['cf_pack'][k]=pack.get(k,'') if isinstance(pack.get(k,''),str) else ''
    artwork=pack.get('artwork','') if isinstance(pack,dict) else ''
    if isinstance(artwork,str) and artwork.startswith('https://') and len(artwork)<2048 and result['cf_pack']:
        result['cf_pack']['artwork']=artwork
    for key,validator in [('vps_host',host),('ssh_username',username),('ssh_port',port),('join_address',host)]:
        if key in data:
            try:result[key]=validator(data[key])
            except (ValueError,UnicodeError):pass
    value = data.get('ram')
    if isinstance(value, int) and not isinstance(value, bool) and 2 <= value <= 16:
        result['ram'] = value
    return result


class SettingsStore:
    def __init__(self, path):
        self.path = Path(path)
        self.warning = ''
        self.data = dict(DEFAULTS)
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                raise ValueError('Expected a settings object')
            self.data = validated(raw)
        except FileNotFoundError:
            # Upgrade from v2: recover the default server's installed settings.
            try:
                old = json.loads((Path(DEFAULT_FOLDER)/'switcher-server.json').read_text(encoding='utf-8'))
                self.data = validated(old)
            except (OSError, ValueError, TypeError):
                pass
        except (ValueError, UnicodeError):
            try:
                backup = self.path.with_name('settings.corrupt-'+uuid.uuid4().hex[:8]+'.json')
                self.path.rename(backup)
                self.warning = 'Unreadable settings were kept at '+str(backup)+'. Defaults loaded.'
            except OSError as e:
                self.warning = 'Could not read settings: '+str(e)
        except OSError as e:
            self.warning = 'Could not read settings: '+str(e)

    def save(self, data):
        clean = validated(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                             prefix='.settings-', suffix='.tmp', delete=False) as f:
                name = f.name
                json.dump(clean, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, self.path)
            self.data = clean
        finally:
            if name:
                Path(name).unlink(missing_ok=True)
