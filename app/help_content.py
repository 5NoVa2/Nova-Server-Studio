"""In-app troubleshooting from real setup issues. No account-specific defaults."""
TOPICS=[
 {'id': 'ssh-startup',
 'category': 'VPS & SSH',
 'title': 'First-time VPS & SSH setup — commands, failed logins and listening ports',
 'body': 'Start here for a fresh Ubuntu 24.04 VPS. Follow the numbered steps in order; each command says where to run it. '
         'Commands are copied only, never executed by Saturn. Examples use placeholders and sample ports, not your saved '
         'credentials.',
 'steps': [{'title': '1. Open your provider’s web console',
            'where': 'VPS · Ubuntu terminal',
            'text': 'Use your VPS provider’s browser console (for example, RackNerd’s console) and log into the VPS account. '
                    'These examples use root and SSH port 22; replace root, VPS_IP and every port with your own values. For the '
                    'key-install commands, be logged in as the same account you will use for SSH. A non-root account needs sudo; '
                    'Configure VPS in Saturn needs root or passwordless sudo. Keep this console open while testing.',
            'command': 'whoami',
            'expected': 'Shows the account you are setting up. Password prompts may show no characters while typing.',
            'failure': 'If the console login fails, check the provider’s initial credentials or recovery options. The '
                       'web-console login is separate from SSH authentication.'},
           {'title': '2. Check or install the SSH server',
            'where': 'VPS · Ubuntu terminal',
            'text': 'Most VPS images already include SSH. Check it first. Ubuntu 24.04 may use ssh.socket, so an inactive '
                    'ssh.service alone does not prove SSH is unavailable.',
            'command': "sudo systemctl status ssh.service ssh.socket --no-pager\nsudo ss -lntp 'sport = :22'",
            'expected': 'A LISTEN row on your SSH port; sshd or systemd can own the listener. Replace 22 if your provider uses '
                        'another SSH port.',
            'failure': 'If OpenSSH is missing or there is no listener, run the repair commands below from the provider console. '
                       'If a listener exists but the PC cannot connect, check the VPS IP, SSH port and provider firewall.',
            'repair': 'sudo apt update\n'
                      'sudo apt install openssh-server\n'
                      'sudo /usr/sbin/sshd -t && sudo systemctl enable --now ssh.service\n'
                      'sudo journalctl -u ssh.service -u ssh.socket -n 50 --no-pager'},
           {'title': '3. Create a key on your hosting PC',
            'where': 'THIS PC · Windows PowerShell',
            'text': 'Use a dedicated filename to avoid replacing an existing key. If this filename already exists, reuse it or '
                    'choose a new filename; do not overwrite a key you still need. Enter a passphrase when asked. A passphrase '
                    'protects the private key and is different from the VPS account password.',
            'command': 'ssh-keygen -t ed25519 -f "$env:USERPROFILE\\.ssh\\saturn_ed25519"\n'
                       'Get-Content "$env:USERPROFILE\\.ssh\\saturn_ed25519.pub"',
            'expected': 'Two files: saturn_ed25519 is PRIVATE and stays on your PC; saturn_ed25519.pub is PUBLIC and is the line '
                        'to copy to the VPS.',
            'failure': 'If ssh-keygen is not recognized, install Windows OpenSSH Client through Windows Optional Features. Never '
                       'share the private key or paste its contents into the VPS.'},
           {'title': '4. Install the public key on the VPS',
            'where': 'VPS · Ubuntu terminal · logged in as the SSH account',
            'text': 'Run these commands as the account you checked with whoami. In nano, paste the entire public line starting '
                    'ssh-ed25519 on its own new line. Keep any existing keys. Press Ctrl+O, Enter to save, then Ctrl+X to exit. '
                    'Run chmod after closing nano.',
            'command': 'mkdir -p ~/.ssh\nchmod 700 ~/.ssh\nnano ~/.ssh/authorized_keys\nchmod 600 ~/.ssh/authorized_keys',
            'expected': 'Your public key is in that account’s authorized_keys. Installing a key does not normally require an SSH '
                        'restart.',
            'failure': 'Permission denied (publickey): check the username, private key selected on the PC, full public-key line '
                       'and account ownership. Do not enable root password login to work around a key mismatch. Use the '
                       'diagnostics below; configuration includes or Match blocks can affect the result.',
            'repair': 'ls -ld ~ ~/.ssh ~/.ssh/authorized_keys\n'
                      'sudo /usr/sbin/sshd -t\n'
                      'sudo /usr/sbin/sshd -T | grep -E '
                      '"^(port|pubkeyauthentication|authorizedkeysfile|permitrootlogin|passwordauthentication) "\n'
                      'sudo journalctl -u ssh.service -n 50 --no-pager'},
           {'title': '5. Verify the VPS identity and test SSH',
            'where': 'VPS console, then THIS PC · Windows PowerShell',
            'text': 'In the trusted VPS console, inspect the host fingerprint with the first command. Then run the ssh command '
                    'on your PC. Compare the offered fingerprint before accepting; use the matching host-key type if the prompt '
                    'shows RSA or ECDSA instead. known_hosts remembers the VPS identity; it is not your private key.',
            'command': 'sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub',
            'pcCommand': 'ssh -i "$env:USERPROFILE\\.ssh\\saturn_ed25519" -p 22 root@VPS_IP',
            'expected': 'A successful SSH session opens a terminal on the VPS. The key passphrase unlocks the local key; an '
                        'account password prompt is a different credential.',
            'failure': 'Permission denied, please try again: verify the account/password in the provider console; a working '
                       'console password may still be disabled for SSH. publickey: return to step 4. Timeout/refused: return to '
                       'step 2 and check provider firewall TCP 22. A changed fingerprint must be verified through the provider '
                       'console before updating known_hosts. For detailed connection errors, use the diagnostic command below '
                       'and redact addresses/paths before sharing logs.',
            'repair': 'ssh -v -i "$env:USERPROFILE\\.ssh\\saturn_ed25519" -p 22 root@VPS_IP'},
           {'title': '6. Connect Saturn and start the tunnel',
            'where': 'SATURN · Settings, then Server',
            'text': 'In Settings → VPS connection, enter the VPS IP, SSH username, SSH port and the PRIVATE key path (no .pub). '
                    'Enter its passphrase if needed. Test SSH connection, then stop any existing tunnel and choose Configure '
                    'VPS. Select the profile’s Java or Bedrock tunnel, start the Minecraft server and connect its tunnel. Wait '
                    'for the game startup-complete message. SSH reachable/authenticated is not a game connection test.',
            'expected': 'Saturn logs the selected PUBLIC VPS port forwarding to this PC’s LOCAL port. Note both ports before the '
                        'checks below.',
            'failure': 'If Configure VPS fails, check the exact log and root/passwordless-sudo requirement. If forwarding fails, '
                       'check for a duplicate public port, stop the other tunnel or choose an unused port, then run Configure '
                       'VPS again.'},
           {'title': '7. Is the game listening locally?',
            'where': 'THIS PC · Windows PowerShell',
            'text': 'Examples below use LOCAL Java TCP 25565 and LOCAL Bedrock UDP 19132. Replace them with this profile’s LOCAL '
                    'ports. Run the matching check after Minecraft finishes starting.',
            'command': 'Get-NetTCPConnection -State Listen -LocalPort 25565\nGet-NetUDPEndpoint -LocalPort 19132',
            'expected': 'Java: a Listen row on the local TCP port. Bedrock: a UDP endpoint row (UDP has no TCP-style LISTEN '
                        'state). You only need the check for the engine you are hosting.',
            'failure': 'No matching objects/rows usually means no local listener on that port. Check the game console for '
                       'startup errors and verify server.properties and the selected profile’s local port. Test joining locally '
                       'before checking the public VPS port.'},
           {'title': '8. Is the public game port listening on the VPS?',
            'where': 'VPS · Ubuntu terminal',
            'text': 'Examples below use PUBLIC Java TCP 25566 and PUBLIC Bedrock UDP 19132. Replace them with this profile’s '
                    'PUBLIC ports. These game listeners exist only while the corresponding Saturn tunnel/relay is running. They '
                    'are separate from SSH port 22.',
            'command': "sudo ss -lntp 'sport = :25566'\nsudo ss -lnup 'sport = :19132'\nsudo ufw status verbose",
            'expected': 'Java: LISTEN on 0.0.0.0:25566 or the configured public interface. Bedrock: a bound UDP endpoint, often '
                        'UNCONN, on the public UDP port. A listener bound only to 127.0.0.1 is not publicly reachable. UFW '
                        'inactive does not mean the provider firewall is open.',
            'failure': 'No row: reconnect the matching tunnel/relay and check its log. Loopback-only Java listener: stop the '
                       'tunnel, run Configure VPS and reconnect. Port already in use: identify the listed process before '
                       'changing profiles; do not kill unrelated processes. A listener is necessary but does not prove firewall '
                       'or game connectivity. If UFW is active, allow the matching public game port with the commands below. '
                       'Also allow SSH and these game ports in the provider firewall; do not enable UFW blindly during '
                       'troubleshooting.',
            'repair': 'sudo ufw allow 25566/tcp\nsudo ufw allow 19132/udp'},
           {'title': '9. Test the path before DNS',
            'where': 'THIS PC · Windows PowerShell, then Minecraft',
            'text': 'Java only: test the VPS IP and PUBLIC TCP port from the PC. Then join with the matching Minecraft client '
                    'and required mods. Once the IP works, test the domain. Bedrock: use a real Bedrock client with the VPS IP '
                    'and PUBLIC UDP port; Test-NetConnection is a TCP test and cannot verify UDP.',
            'command': 'Test-NetConnection -ComputerName VPS_IP -Port 25566',
            'expected': 'TcpTestSucceeded : True confirms a TCP connection to the public listener. It does not confirm Minecraft '
                        'login, correct mods, or that the tunnel can reach the local server.',
            'failure': 'False with a VPS listener present: check public binding, VPS/provider firewalls and the address/port. '
                       'True but Minecraft fails: check the tunnel destination, local server readiness, protocol/version/mods. '
                       'If VPS IP works but domain fails, check the A record, stale AAAA records and DNS-only mode. At your '
                       'domain panel, point the join hostname to the VPS IP; enter the same domain in Settings → Domain & '
                       'display.'}]},
 {'id':'first-connection','category':'Connections','title':'Start here: local works, but friends cannot join','body':
 '1. Start the selected server and wait for Ready or the server’s normal startup-complete message.\n'
 '2. From the hosting PC, test 127.0.0.1 with this profile’s LOCAL game port. From another device on the same LAN, use the hosting PC’s LAN IP.\n'
 '3. Start the matching tunnel. Its log should show the PUBLIC VPS port forwarding to this PC’s LOCAL port.\n'
 '4. Test the VPS IP with the PUBLIC game port before testing your domain. If the IP works and the domain does not, check DNS.\n'
 '5. Use the matching Java/Bedrock client, version and required mods. A successful SSH login alone does not prove Minecraft is reachable.'},
 {'id':'refused','category':'Connections','title':'Connection refused / getsockopt, even though VPS says connected','body':
 '“Connection refused” often means nothing is accepting connections at the address/port, or a firewall is actively rejecting it. A timeout can indicate filtering or a routing problem.\n'
 'Check that Minecraft is running, the tunnel is still connected, and its destination matches the LOCAL game port. The SSH port (often 22) is for VPS login; it is not the Minecraft port.\n'
 'A log such as “VPS TCP 25566 → this PC 127.0.0.1:25566” means players must reach VPS-IP:25566 or domain:25566. A domain alone normally uses the client’s default game port.\n'
 '“Reachable” or “SSH authenticated” only proves the specific test succeeded. It does not prove a Java/Bedrock client can complete a game connection.'},
 {'id':'ports','category':'Connections','title':'Which ports do players use? Multiple profiles and port ranges','body':
 'LOCAL = where Minecraft listens on your hosting PC. PUBLIC = where players connect on the VPS. They can differ; the tunnel connects them.\n'
 'Each simultaneous profile needs a separate server folder and unique local ports. Profiles using the same VPS also need distinct public ports for the same protocol. New profiles allocate unused ports; check Settings before starting.\n'
 'Settings → Ports & ranges accepts inclusive ranges and commas. Save preferences, then Configure VPS to apply forwarding/UFW rules. Also allow the same public ports and protocol in your VPS provider’s firewall. A DNS A record does not open ports.\n'
 'A range allows multiple assigned listeners; it does not make one Minecraft instance listen on every port.'},
 {'id':'bedrock','category':'Connections','title':'Java vs Bedrock / TCP vs UDP','body':
 'Java and Bedrock clients use different server protocols. Choose the correct server engine and tunnel type for the profile. Java uses TCP. Bedrock uses UDP at its public game port; Saturn relays that UDP through SSH/TCP internally.\n'
 'Allow TCP for the Java public port and UDP for the Bedrock public port in provider and VPS firewall rules. A TCP-only web port checker cannot confirm a Bedrock UDP connection.\n'
 'Use the actual public port shown by the profile. Java clients cannot directly join a native Bedrock server, and Bedrock clients cannot directly join a Java server without a separately configured bridge.'},
 {'id':'publickey','category':'VPS & SSH','title':'Permission denied (publickey)','body':
 'The VPS did not accept a usable key for the selected SSH user. Confirm the VPS host, username and SSH port in Settings.\n'
 'In the app choose your PRIVATE key file, such as id_ed25519, not its .pub file. Keep that private key on your PC. The matching PUBLIC key belongs in the chosen VPS user’s ~/.ssh/authorized_keys.\n'
 'Your provider’s web console can help install the public key if SSH is locked out. On the VPS, the SSH directory should be owned by that user, with ~/.ssh normally mode 700 and authorized_keys mode 600.\n'
 'Do not paste private-key contents into the app, chat, or support tickets. A successful web-console password login does not prove SSH password authentication is enabled.'},
 {'id':'password','category':'VPS & SSH','title':'Permission denied, please try again / password or passphrase?','body':
 'The SSH password belongs to the selected VPS account. A key passphrase unlocks your private key; it can be different from the VPS password.\n'
 'Confirm the SSH username. Ubuntu providers may use root or another account depending on the image. Test the account in the provider’s web console if needed.\n'
 'If the VPS allows key-only SSH, entering the correct account password still will not enable password login. Use the matching key instead. Avoid repeatedly guessing passwords.\n'
 'Terminal password prompts often show no letters or dots while you type. This is normal. Saturn’s password fields are masked, and passwords/passphrases remain in memory rather than being saved.'},
 {'id':'host-key','category':'VPS & SSH','title':'Known hosts / SSH fingerprint changed','body':
 'The host fingerprint identifies the VPS, not your personal login key. Saturn remembers accepted host keys.\n'
 'On first connection, compare the shown fingerprint with one confirmed through your provider’s trusted console before accepting. After a VPS reinstall or replacement, its host key may legitimately change.\n'
 'A changed key can also indicate the wrong host or an intercepted connection. Verify the new VPS identity before updating its remembered key. Do not blindly remove known-host entries just to make a warning disappear.\n'
 'Use Settings to select the correct VPS host/account/key when moving servers.'},
 {'id':'forwarding','category':'VPS & SSH','title':'SSH connects, but remote forwarding fails','body':
 'Check whether another profile or program already uses the selected public port. Pick a free port and avoid starting duplicate tunnels.\n'
 'Stop the tunnel before Configure VPS. The configured VPS account needs root or passwordless sudo for that setup operation. It applies the forwarding configuration and active UFW rules; the provider’s separate firewall still needs the public game port.\n'
 'SSH must permit the requested reverse listener and public binding. The selected profile’s public port must match the permitted listener configuration. Rerun Configure VPS after adding profiles or changing public ports.\n'
 'Check the console for the exact forwarding error. Leaving SSH port 22 open alone does not expose your Minecraft listener.'},
 {'id':'domain','category':'Domains','title':'Domain setup at your domain panel','body':
 'At your domain panel, create an A record for your chosen join hostname pointing to the VPS IPv4 address. Use @ for the root domain, or a label such as play for play.example.com. The VPS handles public traffic; do not point this record at your PC’s LAN address.\n'
 'If the provider asks for TTL in hours, 1 hour is a reasonable choice. DNS changes may be cached until the previous TTL expires. Remove or correct stale conflicting address records, including an AAAA record if you have not configured working IPv6 hosting.\n'
 'Enter the same plain hostname in Saturn’s Join domain / address field, then Save join address. This changes the address Saturn displays and copies. It does not update DNS at your provider.\n'
 'An A record carries an IP address, not a port. Players may need hostname:public-port. For Java, an appropriately configured Minecraft SRV record is another option to investigate with your DNS provider.'},
 {'id':'cloudflare','category':'Domains','title':'Cloudflare proxy / orange cloud / WireGuard','body':
 'For an ordinary Saturn SSH tunnel, use a DNS-only record (grey cloud) for the Minecraft join hostname. Cloudflare’s normal web proxy is not a generic Minecraft TCP/UDP proxy. Cloudflare Spectrum is a separate service with its own configuration and availability.\n'
 'Cloudflare is optional: your existing DNS provider can point the domain at the VPS. WireGuard is also not required for Saturn’s built-in SSH tunnel.\n'
 'If the VPS IP and game port work but the domain refuses connections, check the address records, proxy setting, stale IPv6 records and the port entered in the Minecraft client.'},
 {'id':'community-wifi','category':'Connections','title':'Renters, community WiFi and no router access','body':
 'Saturn initiates an outbound SSH connection to your VPS, so you normally do not need inbound router port forwarding on the hosting PC’s network. The network must still permit the outbound connection and game traffic.\n'
 'Your PC runs Minecraft and must stay on with an internet connection. The VPS forwards traffic and has its own bandwidth limits and provider rules.\n'
 'Players use the VPS address or your domain. This avoids publishing your home IP as the join address, but is not a guarantee of anonymity: providers, server plugins or other services may still see network information.'},
 {'id':'installer','category':'App & servers','title':'Installer integrity check failed / application will not open','body':
 'For an NSIS installer integrity error, obtain a fresh installer from the official GitHub release and extract it into a new folder. We fixed an incomplete installer in an earlier preview; use the repaired release. Compare the file’s SHA-256 with the release checksums if needed.\n'
 'Exit Saturn from the system tray before upgrading. Closing the window normally keeps hosting active. Install over the existing location to retain profiles and worlds.\n'
 'The standalone GitHub edition needs compatible 64-bit Python with pip and downloads Qt on first launch. If the process runs without a window, check app.log in the MCServerSwitcher folder under your local application data. Redact credentials and personal addresses before sharing logs.\n'
 'A SmartScreen publisher warning is different from an installer integrity failure.'},
 {'id':'java','category':'App & servers','title':'Java version errors or a modded server will not start','body':
 'Read the first meaningful console error. Minecraft and mod loaders can require specific Java versions; a newer Java is not always compatible with an older pack.\n'
 'Settings → Environment defaults to Auto, using the runtime chosen during installation. To override it, select a Java version, prepare it, then start the stopped server. A missing prepared runtime gives an instruction rather than silently using a different version.\n'
 'Use a server-ready modpack release and matching client version/mods. Not every CurseForge release includes dedicated server files. Adjust RAM to suit the server while leaving memory for Windows and your game.\n'
 'Installing/switching replaces server files after confirmation. Make a backup before changing an existing world.'},
 {'id':'tasks-backups','category':'App & servers','title':'Saving files, scheduled backups, or the app in the tray','body':
 'Save All / Ctrl+S saves pending file and server-setting edits. The file browser uses single clicks; binary files cannot be edited as text.\n'
 'Tasks can schedule Start, Stop, Save world, Backup or a custom Minecraft console command. Times use the hosting PC’s timezone. Saturn and the PC must be running; missed occurrences are skipped.\n'
 'A backup task cleanly stops a running server, copies its files, then restarts and reconnects. A stopped server stays stopped. Failures pause the queue and can leave a server stopped; check the console before resuming.\n'
 'Closing minimizes to the tray. Right-click the tray icon and choose Exit Saturn to stop owned processes. Sleep-on-join is not implemented.'},
]
