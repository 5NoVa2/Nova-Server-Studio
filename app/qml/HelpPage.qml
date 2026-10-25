import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ScrollView {
    id: help
    objectName: 'helpPage'
    property var snapshot: ({})
    property var topics: []
    property string topicsSignature: ''
    onSnapshotChanged: { const value=JSON.stringify(snapshot.helpTopics || []); if(value!==topicsSignature) { topicsSignature=value; topics=snapshot.helpTopics || [] } }
    property var matches: topics.filter(row=>(!category || category.currentIndex===0 || row.category===category.currentText) && (row.title+' '+row.body+' '+row.category+' '+JSON.stringify(row.steps || [])).toLowerCase().includes((search ? search.text : '').toLowerCase().trim()))
    contentWidth: availableWidth; clip: true
    ColumnLayout { width: help.availableWidth-52; x: 26; spacing: 16
        Text { text: 'Let’s get you connected.'; color: '#f0f1f7'; font.pixelSize: 29; font.weight: Font.DemiBold; Layout.fillWidth: true }
        Text { text: 'Common fixes from setting up Saturn, especially VPS hosting. Help applies to the selected server profile.'; color: '#a4adbe'; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        RowLayout { Layout.fillWidth: true
            NField { id: search; objectName: 'helpSearch'; placeholderText: 'Search: publickey, connection refused, DNS…'; Layout.fillWidth: true }
            NCombo { id: category; objectName: 'helpCategory'; choices: ['All topics','VPS & SSH','Connections','Domains','App & servers']; Layout.preferredWidth: 190 }
        }
        Text { objectName: 'helpResultCount'; text: help.matches.length+' help topics'; color: '#8e96a8'; font.pixelSize: 12 }
        Repeater { model: help.matches
            Panel { id: topic; required property var modelData; objectName: 'helpTopic_'+modelData.id; property bool expanded: false
                Layout.fillWidth: true; implicitHeight: topicColumn.implicitHeight+32
                ColumnLayout { id: topicColumn; anchors.fill: parent; anchors.margins: 16; spacing: 12
                    NButton { objectName: 'helpTopicToggle_'+topic.modelData.id; text: topic.modelData.title+(topic.expanded ? '   −' : '   +'); Layout.fillWidth: true; onClicked: { topic.expanded=!topic.expanded; if(ApplicationWindow.window.uiSounds) ApplicationWindow.window.uiSounds.play('transition') } }
                    Text { visible: topic.expanded; text: topic.modelData.body; color: '#afbbce'; font.pixelSize: 13; wrapMode: Text.WordWrap; textFormat: Text.PlainText; Layout.fillWidth: true }
                    SSHSetupGuide { visible: topic.expanded && !!topic.modelData.steps; steps: topic.modelData.steps || []; Layout.fillWidth: true }
                }
            }
        }
        Text { visible: !help.matches.length; text: 'No matching topics. Try “SSH”, “ports”, “domain” or clear the search.'; color: '#a4adbe'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
        Text { text: 'UPSTREAM GUIDES'; color: '#8e96a8'; font.pixelSize: 12; font.letterSpacing: 1.3; Layout.topMargin: 12 }
        RowLayout {
            NButton { text: 'Ubuntu SSH guide'; onClicked: Qt.openUrlExternally('https://ubuntu.com/server/docs/how-to/security/openssh-server/') }
            NButton { text: 'Cloudflare Spectrum'; onClicked: Qt.openUrlExternally('https://www.cloudflare.com/products/spectrum-for-minecraft/') }
        }
        Item { implicitHeight: 24 }
    }
}
