"""Validated additional VPS game-port ranges and compact firewall rules."""
import re
from connection_settings import port

RANGE_KEYS=('java_port_ranges','bedrock_port_ranges')
MAX_PORTS=256


def parse_ranges(value):
    if not isinstance(value,str):raise ValueError('Enter port ranges as text, such as 25565-25575, 25580.')
    if not value.strip():return []
    ports=set()
    for token in value.split(','):
        match=re.fullmatch(r'\s*(\d+)\s*(?:-\s*(\d+)\s*)?',token)
        if not match:raise ValueError('Use ports or inclusive ranges separated by commas, such as 25565-25575, 25580.')
        first=port(match[1]);last=port(match[2]) if match[2] else first
        if last<first:raise ValueError('The end of a port range must be at least its start.')
        if last-first+1>MAX_PORTS:raise ValueError('Use at most 256 additional ports per protocol.')
        ports.update(range(first,last+1))
        if len(ports)>MAX_PORTS:raise ValueError('Use at most 256 additional ports per protocol.')
    return sorted(ports)


def compact(ports,separator='-'):
    values=sorted({port(p) for p in ports});result=[]
    if not values:return result
    first=last=values[0]
    for value in values[1:]:
        if value==last+1:last=value;continue
        result.append(str(first) if first==last else f'{first}{separator}{last}');first=last=value
    result.append(str(first) if first==last else f'{first}{separator}{last}')
    return result


def normalize(value):return ', '.join(compact(parse_ranges(value)))


def assign_remote(pool,used,fallback):
    if not pool:return fallback
    free=next((p for p in pool if p not in used),None)
    if free is None:raise ValueError('All ports in this VPS range are assigned. Expand the range before adding another server.')
    return free
