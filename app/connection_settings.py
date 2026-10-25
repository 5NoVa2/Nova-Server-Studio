"""Validated, non-secret VPS and player-address preferences."""
import ipaddress
import re
from dataclasses import dataclass

DEFAULTS={'vps_host':'','ssh_username':'root','ssh_port':22,'join_address':''}


def host(value):
    if not isinstance(value,str):raise ValueError('Address/username must be text.')
    value=value.strip()
    if value.startswith('[') and value.endswith(']'):value=value[1:-1]
    if not value:raise ValueError('Enter a VPS host or join address.')
    try:return str(ipaddress.ip_address(value))
    except ValueError:
        if re.fullmatch(r'[0-9]+(?:\.[0-9]+){3}',value):raise ValueError('Enter a valid IPv4 address.')
    value=value.rstrip('.').encode('idna').decode('ascii').lower()
    if len(value)>253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',label) for label in value.split('.')):
        raise ValueError('Enter a plain domain or IP address, without https://, a slash or a game port.')
    return value


def username(value):
    if not isinstance(value,str):raise ValueError('Address/username must be text.')
    value=value.strip()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}\$?',value):raise ValueError('Enter a valid SSH username, such as root or ubuntu.')
    return value


def port(value):
    if isinstance(value,float):raise ValueError('SSH port must be a whole number.')
    try:number=int(value)
    except (TypeError,ValueError):raise ValueError('SSH port must be a number from 1 to 65535.') from None
    if isinstance(value,bool) or not 1<=number<=65535:raise ValueError('SSH port must be from 1 to 65535.')
    return number


@dataclass(frozen=True)
class Connection:
    vps_host:str
    ssh_username:str
    ssh_port:int
    join_address:str
    @classmethod
    def parse(cls,values):
        remote=host(values.get('vps_host',DEFAULTS['vps_host']))
        return cls(remote,username(values.get('ssh_username',DEFAULTS['ssh_username'])),port(values.get('ssh_port',22)),host(values.get('join_address') or remote))
    def as_dict(self):return {key:getattr(self,key) for key in DEFAULTS}


def setup_script(script,user):
    user=username(user)
    return script.replace('Match User root\n','Match User '+user+'\n').replace('user=root,host=localhost','user='+user+',host=localhost')


def preferences(values):
    """Allow local-only profiles; validate populated connection preferences."""
    remote=str(values.get('vps_host','')).strip()
    address=str(values.get('join_address','')).strip()
    return {'vps_host':host(remote) if remote else '',
            'ssh_username':username(values.get('ssh_username','root')),
            'ssh_port':port(values.get('ssh_port',22)),
            'join_address':host(address) if address else ''}
