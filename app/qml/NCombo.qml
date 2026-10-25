import QtQuick
import QtQuick.Controls
ComboBox {
    id: c
    property var soundBus: ApplicationWindow.window ? ApplicationWindow.window.uiSounds : null
    hoverEnabled: true
    onHoveredChanged: if(hovered && enabled && soundBus) soundBus.play('hover')
    Connections { target: c; function onActivated() { if(c.enabled && c.soundBus) c.soundBus.play('click') } }
    property var choices: []
    property string choicesSignature: ''
    model: []
    onChoicesChanged: {
        const signature=JSON.stringify(choices)
        if(signature!==choicesSignature) {
            choicesSignature=signature
            model=choices
        }
    }
    popup.height: Math.min(360, popup.contentItem.implicitHeight + popup.topPadding + popup.bottomPadding)
    implicitHeight: 44; implicitWidth: 190
    font.pixelSize: 13; palette.text: '#eeeeef'; palette.buttonText: '#eeeeef'; palette.base: '#191d27'; palette.highlight: '#48556f'; palette.highlightedText: '#ffffff'; palette.button: '#191d27'
    background: Rectangle { radius: 16; color: '#141821'; border.color: c.activeFocus ? '#a3b2cf' : '#303642' }
    contentItem: Text { text: c.displayText; color: '#eceef6'; font: c.font; leftPadding: 14; rightPadding: 32; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
}

