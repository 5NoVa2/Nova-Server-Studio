#!/bin/bash
set -euo pipefail
if [ "$(id -u)" != 0 ]; then echo 'Run as root.'; exit 1; fi
. /etc/os-release
if [ "$ID" != ubuntu ] || [ "$VERSION_ID" != 24.04 ]; then
    echo "This setup supports Ubuntu 24.04; detected $PRETTY_NAME. No changes made."; exit 1
fi
SSHD=/usr/sbin/sshd
"$SSHD" -t
STAMP=$(date +%Y%m%d-%H%M%S)-$$
BACKUP=/root/mc-tunnel-backup-$STAMP
mkdir -m 700 "$BACKUP"
cp -a /etc/ssh/sshd_config "$BACKUP/sshd_config"
rollback() {
    cp -a "$BACKUP/sshd_config" /etc/ssh/sshd_config
    echo "SSH changes rolled back. Original config: $BACKUP"
}
trap 'rollback' ERR
# Append a per-user Match block after existing global settings. Never place
# Match blocks ahead of global settings in a drop-in directory.
python3 - <<'PYCONF'
from pathlib import Path
p=Path('/etc/ssh/sshd_config')
s=p.read_text()
start='# BEGIN MC SERVER SWITCHER TUNNEL'
end='# END MC SERVER SWITCHER TUNNEL'
if start in s:
    before, rest=s.split(start,1)
    if end not in rest:
        raise SystemExit('Incomplete managed block; refusing to edit.')
    s=before+rest.split(end,1)[1]
s=s.rstrip()+"\n\n"+start+"\n"+"""Match User root
    GatewayPorts clientspecified
    AllowTcpForwarding remote
    PermitListen 0.0.0.0:25565
"""+end+"\n"
p.write_text(s)
PYCONF
"$SSHD" -t
EFFECTIVE=$("$SSHD" -T -C user=root,host=localhost,addr=127.0.0.1)
printf '%s\n' "$EFFECTIVE" | grep -qx 'gatewayports clientspecified'
printf '%s\n' "$EFFECTIVE" | grep -qx 'allowtcpforwarding remote'
printf '%s\n' "$EFFECTIVE" | grep -qx 'permitlisten 0.0.0.0:25565'
if printf '%s\n' "$EFFECTIVE" | grep -qx 'disableforwarding yes'; then
    echo 'DisableForwarding is enabled elsewhere. Refusing to weaken it.'; false
fi
systemctl reload ssh
trap - ERR
if command -v ufw >/dev/null && ufw status | grep -q 'Status: active'; then
    ufw allow 25565/tcp comment 'Minecraft reverse SSH tunnel'
    ufw allow 19132/udp comment 'Nova Bedrock UDP relay'
fi
echo
echo "VPS setup complete. SSH configuration backup: $BACKUP"
echo 'Port 25565 will listen publicly only while the PC tunnel is connected.'
echo 'Bedrock relay requires inbound UDP 19132; Java requires TCP 25565.'
echo 'Allow the matching port in any external provider firewall too.'
echo 'Next: start the local server and then start the tunnel in the Windows app.'
