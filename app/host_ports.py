"""Render VPS permissions for all configured ports, scoped to one SSH user."""
from connection_settings import port,username,setup_script
from port_ranges import compact

def vps_script(source,user,java_ports,bedrock_ports):
    user=username(user);java=sorted({port(p) for p in java_ports});bedrock=sorted({port(p) for p in bedrock_ports})
    script=setup_script(source,user)
    listeners=' '.join('0.0.0.0:'+str(p) for p in java)
    script=script.replace('PermitListen 0.0.0.0:25565','PermitListen '+listeners)
    script=script.replace("grep -qx 'permitlisten 0.0.0.0:25565'","grep -qx 'permitlisten "+listeners+"'")
    script=script.replace("    ufw allow 25565/tcp comment 'Minecraft reverse SSH tunnel'",'\n'.join("    ufw allow "+str(p)+"/tcp comment 'Saturn Java tunnel'" for p in compact(java,':')))
    script=script.replace("    ufw allow 19132/udp comment 'Saturn Bedrock UDP relay'",'\n'.join("    ufw allow "+str(p)+"/udp comment 'Saturn Bedrock relay'" for p in compact(bedrock,':')))
    # Separate managed blocks let different SSH users retain their own listeners.
    begin='# BEGIN MC SERVER SWITCHER TUNNEL';end='# END MC SERVER SWITCHER TUNNEL'
    script=script.replace("start='"+begin+"'", "start='"+begin+" USER "+user+"'")
    script=script.replace("end='"+end+"'", "end='"+end+" USER "+user+"'")
    migration="""legacy_start='# BEGIN MC SERVER SWITCHER TUNNEL'
legacy_end='# END MC SERVER SWITCHER TUNNEL'
if legacy_start+'\\n' in s:
    before,rest=s.split(legacy_start+'\\n',1)
    block,separator,after=rest.partition(legacy_end)
    if not separator:raise SystemExit('Incomplete legacy managed block.')
    if 'Match User USERNAME\\n' in block:s=before+after
""".replace('USERNAME',user)
    script=script.replace('if start in s:',migration+"if start+'\\n' in s:")
    script=script.replace('before, rest=s.split(start,1)',"before, rest=s.split(start+'\\n',1)")
    script=script.replace("echo 'Port 25565 will listen publicly only while the PC tunnel is connected.'", "echo 'Configured Java TCP ports: "+', '.join(map(str,java))+"'")
    script=script.replace("echo 'Bedrock relay requires inbound UDP 19132; Java requires TCP 25565.'", "echo 'Configured Bedrock UDP ports: "+', '.join(map(str,bedrock))+"'")
    return script
