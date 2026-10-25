import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: setup
    property var snapshot: ({})
    property bool bedrock: (snapshot.installedEngine || snapshot.engine)==='Bedrock'
    property int localPort: Number(bedrock ? snapshot.local_bedrock_port : snapshot.local_java_port)
    property var publicAddress: (snapshot.playitMappings || {})[String(localPort)]
    spacing: 12
    Text { text: 'PLAYIT.GG · NO VPS OR ROUTER PORT FORWARDING'; color: '#aab9cf'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    Text { objectName: 'playitAgentStatus'; text: 'Agent: '+(setup.snapshot.playitStatus || 'Not started'); color: '#d8e4f4'; font.pixelSize: 14; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
    Text { text: '1. Prepare the verified official agent.\n2. Start setup and approve this agent in your browser.\n3. In playit.gg, create a Minecraft '+(setup.bedrock ? 'Bedrock / UDP' : 'Java')+' tunnel assigned to this agent, targeting 127.0.0.1:'+setup.localPort+'.\n4. Start hosting in Saturn. Its public join address appears after the agent reports the matching tunnel.'; color: '#aebbcf'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    RowLayout {
        NButton { objectName: 'preparePlayitButton'; text: setup.snapshot.playitReady ? 'Repair / verify agent' : 'Prepare playit'; enabled: !setup.snapshot.busy && !setup.snapshot.playitRunning && !setup.snapshot.exiting; onClicked: nova.action('playit_prepare') }
        NButton { objectName: 'startPlayitButton'; text: 'Start playit setup'; primary: true; enabled: setup.snapshot.playitReady && !setup.snapshot.playitRunning && !setup.snapshot.busy && !setup.snapshot.exiting; onClicked: nova.action('playit_start') }
        NButton { objectName: 'claimPlayitButton'; text: 'Approve agent'; enabled: !!setup.snapshot.playitClaimUrl; onClicked: Qt.openUrlExternally(setup.snapshot.playitClaimUrl) }
    }
    RowLayout {
        NButton { text: 'Open playit dashboard'; onClicked: Qt.openUrlExternally('https://playit.gg/account/tunnels') }
        NButton { objectName: 'stopPlayitButton'; text: 'Stop shared agent'; enabled: setup.snapshot.playitRunning; onClicked: nova.action('playit_stop') }
    }
    Text { objectName: 'playitTarget'; text: 'LOCAL TARGET: 127.0.0.1:'+setup.localPort+' · '+(setup.bedrock ? 'UDP' : 'TCP'); color: '#afc7e5'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    Text { text: setup.publicAddress ? 'PUBLIC: '+setup.publicAddress.host+(setup.publicAddress.port ? ':'+setup.publicAddress.port : '') : 'No matching active game tunnel reported yet. Check agent approval, tunnel type and local target.'; color: '#c1d1e6'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
    Text { text: 'The free tier currently supports Minecraft Java. For free Bedrock, use RakNet where supported (transport=raknet in server.properties); NetherNet currently requires Premium. Account/tunnel limits, region options and other paid features are controlled by playit.gg. You complete account approval and tunnel creation on their website.'; color: '#c9b99f'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    Text { text: 'One hidden agent is shared across profiles. Create a separate game tunnel for each local port. Stopping the shared agent disconnects every playit profile; Stop all and Exit Saturn stop the agent. Your PC must stay on. Agent credentials stay in your local app-data folder, outside server worlds/backups.'; color: '#96a5ba'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    NButton { text: 'Bedrock / free-tier details'; onClicked: Qt.openUrlExternally('https://playit.gg/support/minecraft-bedrock-nethernet/') }
}
