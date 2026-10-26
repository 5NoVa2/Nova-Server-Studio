"""Saved friends are scoped to a server profile and Minecraft edition."""
from players import player_command

MAX_FRIENDS = 100

def friend_entry(name, edition):
    if not isinstance(name, str) or edition not in ('Java', 'Bedrock'):
        raise ValueError('Choose Java or Bedrock and enter a valid player name.')
    name = name.strip()
    player_command('allow', name, edition == 'Bedrock')
    return dict(name=name, edition=edition)

def friend_key(entry):
    return entry['edition'], entry['name'].casefold()

def normalized_friends(rows):
    result = []; seen = set()
    if not isinstance(rows, list): return result
    for row in rows:
        if not isinstance(row, dict): continue
        try: entry = friend_entry(row.get('name'), row.get('edition'))
        except (ValueError, TypeError): continue
        key = friend_key(entry)
        if key not in seen:
            seen.add(key); result.append(entry)
        if len(result) == MAX_FRIENDS: break
    return result
