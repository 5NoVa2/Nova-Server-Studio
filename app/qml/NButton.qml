import QtQuick
import QtQuick.Controls
Button {
    id: b
    property bool primary: false
    property bool danger: false
    property bool motion: true
    implicitHeight: 44
    implicitWidth: Math.max(100, label.implicitWidth+32)
    hoverEnabled: true
    font.pixelSize: 13
    font.weight: Font.DemiBold
    opacity: enabled ? 1 : 0.4
    scale: down ? 0.97 : hovered ? 1.015 : 1
    Behavior on scale { NumberAnimation { duration: b.motion ? 120 : 0 } }
    contentItem: Text { id: label; text: b.text; font: b.font; color: b.primary ? '#101115' : b.danger ? '#ffadb6' : '#e5e6ed'; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle {
        radius: 13; color: b.primary ? (b.hovered ? '#ffffff' : '#dce0ed') : b.hovered ? '#292d38' : '#191c24'
        border.color: b.primary ? '#ffffff' : b.hovered ? '#626979' : '#303440'
        Behavior on color { ColorAnimation { duration: b.motion ? 140 : 0 } }
    }
    ToolTip.visible: hovered && ToolTip.text.length>0
}
