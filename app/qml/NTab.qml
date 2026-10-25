import QtQuick
import QtQuick.Controls
TabButton {
    id: tab
    property var soundBus: ApplicationWindow.window ? ApplicationWindow.window.uiSounds : null
    hoverEnabled: true
    onHoveredChanged: if(hovered && enabled && soundBus) soundBus.play('hover')
    Connections { target: tab; function onClicked() { if(tab.enabled && tab.soundBus) tab.soundBus.play('click') } }
    implicitHeight: 42
    contentItem: Text { text: tab.text; color: tab.checked ? '#f1f4fb' : '#8d98ad'; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle { radius: 10; color: tab.checked ? '#303a4d' : tab.hovered ? '#202735' : '#131821'; border.color: tab.checked ? '#54647f' : '#292f3d' }
}
