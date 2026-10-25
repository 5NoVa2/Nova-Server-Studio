import QtQuick
import QtQuick.Controls
TextField {
    id: field
    color: '#eceef6'; selectionColor: '#687797'; selectedTextColor: '#ffffff'
    placeholderTextColor: '#757c8c'; font.pixelSize: 13
    implicitHeight: 44; leftPadding: 14; rightPadding: 14
    background: Rectangle { radius: 12; color: '#10131a'; border.color: field.activeFocus ? '#b0bcd6' : '#303642' }
}
