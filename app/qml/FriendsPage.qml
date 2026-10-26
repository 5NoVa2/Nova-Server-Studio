import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: friendsPage
    objectName: 'friendsPage'
    property var snapshot: ({})
    spacing: 14
    Text { text: 'Save friends for this server profile. Java and Bedrock names are kept separately.'; color: '#a4adbe'; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
    RowLayout {
        Layout.fillWidth: true
        NField { id: friendName; objectName: 'friendNameField'; placeholderText: 'Minecraft username / Xbox gamertag'; maximumLength: 32; Layout.fillWidth: true; enabled: !friendsPage.snapshot.exiting
            onAccepted: if(nova.addFriend(text,friendEdition.currentText)) text=''
        }
        NCombo { id: friendEdition; objectName: 'friendEditionSelector'; choices: ['Java','Bedrock']; currentIndex: friendsPage.snapshot.friendEdition==='Bedrock' ? 1 : 0; Layout.preferredWidth: 135; enabled: !friendsPage.snapshot.exiting }
        NButton { objectName: 'addFriendButton'; text: 'Add friend'; primary: true; enabled: !!friendName.text.trim() && !friendsPage.snapshot.exiting; onClicked: if(nova.addFriend(friendName.text,friendEdition.currentText)) friendName.clear() }
    }
    RowLayout {
        Layout.fillWidth: true
        CheckBox { objectName: 'autoWhitelistFriendsToggle'; text: 'Auto-add friends to this server’s whitelist'; checked: friendsPage.snapshot.auto_whitelist_friends!==false; enabled: !friendsPage.snapshot.exiting; palette.windowText: '#c0c8d8'; onClicked: nova.autoWhitelistFriends(checked) }
        Item { Layout.fillWidth: true }
        NButton { objectName: 'syncFriendsButton'; text: 'Sync now / retry'; enabled: friendsPage.snapshot.server==='Ready' && !friendsPage.snapshot.busy && !friendsPage.snapshot.exiting; onClicked: nova.syncFriendsNow() }
    }
    Text { text: 'Friends added while stopped are queued. Commands run when this profile’s matching server is ready and are re-applied after restart. This does not enable whitelist-only mode or grant operator permissions.'; color: '#a4adbe'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    Panel {
        Layout.fillWidth: true; Layout.fillHeight: true
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 18; spacing: 12
            Text { text: 'SAVED FRIENDS · '+(friendsPage.snapshot.friendRows || []).length; color: '#8e96a8'; font.pixelSize: 12; font.letterSpacing: 1 }
            Text { visible: !(friendsPage.snapshot.friendRows || []).length; text: 'No friends yet. Add an exact Java username or Bedrock gamertag above.'; color: '#a4adbe'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            ListView {
                objectName: 'friendsList'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 10; model: friendsPage.snapshot.friendRows || []
                delegate: RowLayout {
                    required property var modelData
                    width: ListView.view.width; height: Math.max(50,friendDetails.implicitHeight)
                    ColumnLayout { id: friendDetails; Layout.fillWidth: true; spacing: 5
                        Text { text: modelData.name+' · '+modelData.edition; color: '#edf1f7'; font.pixelSize: 15; textFormat: Text.PlainText; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text { text: modelData.status; color: '#94abc8'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
                    }
                    NButton { text: 'Forget'; enabled: !friendsPage.snapshot.exiting; onClicked: nova.forgetFriend(modelData.name,modelData.edition) }
                }
                ScrollBar.vertical: ScrollBar {}
            }
        }
    }
    Text { text: '“Command sent” means Saturn sent the request; check the console for Minecraft’s result. Use Sync now / retry if a name was rejected. Forget removes only the saved friend: existing whitelist entries remain. To revoke access, use Online players → Remove from allowlist.'; color: '#96a5ba'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
}
