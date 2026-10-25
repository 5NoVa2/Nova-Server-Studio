import QtQuick
Rectangle {
    radius: 24; color: '#13171d'; border.color: '#303741'
    gradient: Gradient { GradientStop { position: 0; color: '#20252d' } GradientStop { position: 0.48; color: '#13171e' } GradientStop { position: 1; color: '#0f1319' } }
    Rectangle { anchors.top: parent.top; anchors.topMargin: 1; anchors.horizontalCenter: parent.horizontalCenter; width: parent.width-48; height: 1; color: '#ffffff'; opacity: 0.07 }
}
