import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: editor
    property var snapshot: ({})
    property string draft: ''
    property bool dirty: false
    property string selectedProfile: ''
    property string feedback: ''
    spacing: 10
    onSnapshotChanged: {
        const profile=((snapshot.profileItems || [])[snapshot.profileIndex || 0] || {}).id || 'main'
        if(profile!==selectedProfile) { selectedProfile=profile; dirty=false; feedback='' }
        if(!dirty) draft=snapshot.join_address || ''
    }
    Text { text: 'Join domain / address'; color: '#dce4ef'; font.pixelSize: 13 }
    RowLayout { Layout.fillWidth: true
        NField { id: domainInput; objectName: 'helpJoinAddressField'; Layout.fillWidth: true; text: editor.draft; placeholderText: 'play.example.com'; enabled: !editor.snapshot.exiting
            onTextEdited: { editor.draft=text; editor.dirty=true; editor.feedback='' }
            onAccepted: saveAddress.clicked()
        }
        NButton { id: saveAddress; objectName: 'saveJoinAddressButton'; text: 'Save join address'; primary: true; enabled: editor.dirty && !editor.snapshot.exiting
            onClicked: {
                if(nova.setJoinAddress(editor.draft)) {
                    editor.dirty=false; editor.draft=nova.state.join_address || ''
                    editor.feedback='Saved for this profile. DNS records at your provider are unchanged.'
                } else editor.feedback=nova.state.error || 'Could not save the join address.'
            }
        }
    }
    Text { text: 'Use a plain domain or IP, without https:// or a port. Leave blank to use the VPS IP (or the local address without a VPS). This setting does not change DNS.'; color: '#98a5b8'; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    Text { visible: !!editor.feedback; text: editor.feedback; color: '#c1d4e8'; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true; textFormat: Text.PlainText }
}
