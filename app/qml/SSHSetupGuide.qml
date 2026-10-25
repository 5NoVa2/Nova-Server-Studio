import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ColumnLayout {
    id: guide
    property var steps: []
    spacing: 18
    component CommandBlock: ColumnLayout {
        id: block
        property string command: ''
        property string label: ''
        property string commandId: ''
        Layout.fillWidth: true; spacing: 6
        Text { text: block.label; color: '#a9b8ce'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
        Rectangle {
            Layout.fillWidth: true; implicitHeight: code.implicitHeight+24
            radius: 12; color: '#0b0f16'; border.color: '#303741'
            TextArea {
                id: code; objectName: 'helpCommand_'+block.commandId
                anchors.fill: parent; anchors.margins: 10; padding: 2
                text: block.command; readOnly: true; selectByMouse: true
                wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText
                color: '#dce7f5'; selectionColor: '#435a77'; font.family: 'Consolas'; font.pixelSize: 13
                background: null
            }
        }
        NButton {
            objectName: 'copyHelpCommand_'+block.commandId
            property bool copied: false
            text: copied ? 'Copied' : 'Copy commands'
            onClicked: { nova.copyHelpCommand(block.command); copied=true; feedback.restart() }
            Timer { id: feedback; interval: 1600; onTriggered: parent.copied=false }
        }
    }
    Repeater {
        model: guide.steps
        ColumnLayout {
            id: step
            required property var modelData
            required property int index
            Layout.fillWidth: true; spacing: 10
            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: '#303741'; Layout.topMargin: 4; Layout.bottomMargin: 4 }
            Text { text: step.modelData.title; color: '#e4ecf8'; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Text { text: step.modelData.where; color: '#93abc8'; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Text { text: step.modelData.text; color: '#afbbce'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
            CommandBlock { visible: !!step.modelData.command; command: step.modelData.command || ''; label: step.modelData.where; commandId: step.index+'_main' }
            CommandBlock { visible: !!step.modelData.pcCommand; command: step.modelData.pcCommand || ''; label: 'THIS PC · Windows PowerShell'; commandId: step.index+'_pc' }
            Text { text: 'EXPECTED: '+step.modelData.expected; color: '#a7c8b5'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
            Text { text: 'IF IT FAILS: '+step.modelData.failure; color: '#d2bca2'; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText }
            CommandBlock { visible: !!step.modelData.repair; command: step.modelData.repair || ''; label: step.index===4 ? 'DIAGNOSTIC · THIS PC · Windows PowerShell' : 'REPAIR / DIAGNOSTIC · VPS · Ubuntu terminal'; commandId: step.index+'_repair' }
        }
    }
}
