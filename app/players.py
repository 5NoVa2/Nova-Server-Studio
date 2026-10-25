"""Parse vanilla/Paper/Forge and Bedrock console player announcements."""
import re
class PlayerTracker:
    def __init__(self):self.names=set();self.expect_names=False
    def consume(self,line):
        text=re.sub(r'\x1b\[[0-9;]*m','',line).strip()
        match=re.search(r'There are (\d+)(?: of a max of \d+|/\d+) players online:?\s*(.*)',text,re.I)
        if match:
            count=int(match[1]);tail=match[2].strip()
            self.names=set(n.strip() for n in tail.split(',') if n.strip()) if count else set()
            self.expect_names=bool(count and not tail)
        elif self.expect_names:
            # Bedrock emits names on the following timestamped INFO line.
            tail=re.sub(r'^.*?INFO\]\s*','',text)
            if tail and not any(x in tail for x in ('Player connected:','Player disconnected:')):
                self.names=set(n.strip() for n in tail.split(',') if n.strip());self.expect_names=False
        else:
            match=re.search(r'([A-Za-z0-9_]{1,16}) (joined|left) the game',text)
            if match:
                if match[2]=='joined':self.names.add(match[1])
                else:self.names.discard(match[1])
            match=re.search(r'Player (connected|disconnected): (.*?)(?:, xuid:|$)',text)
            if match:
                if match[1]=='connected':self.names.add(match[2].strip())
                else:self.names.discard(match[2].strip())
        return sorted(self.names,key=str.casefold)

def player_command(operation,name,bedrock=False):
    commands={'refresh':'list','whitelist_on':'allowlist on' if bedrock else 'whitelist on','whitelist_off':'allowlist off' if bedrock else 'whitelist off'}
    if operation in commands:return commands[operation]
    valid=(1<=len(name)<=32 and all(c.isalnum() or c in ' _.-#' for c in name)) if bedrock else bool(re.fullmatch(r'[A-Za-z0-9_]{1,16}',name))
    if not valid:raise ValueError('Enter a valid player name.')
    if bedrock and operation in ('ban','pardon'):raise ValueError('Bedrock has no native ban/pardon command. Use allowlist and kick.')
    prefixes={'kick':'kick','ban':'ban','pardon':'pardon','op':'op','deop':'deop','allow':'allowlist add' if bedrock else 'whitelist add','unallow':'allowlist remove' if bedrock else 'whitelist remove'}
    if operation not in prefixes:raise ValueError('Unknown player action.')
    return prefixes[operation]+' '+('"'+name+'"' if bedrock else name)
