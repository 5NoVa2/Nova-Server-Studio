import QtQuick
import QtQuick.Controls
Rectangle {
    id: scene
    property bool reduced: false
    property bool playOnStart: true
    property bool active: false
    property real phase: 0
    signal finished()
    color: '#07090c'; visible: active; opacity: active ? 1 : 0
    focus: active
    function begin() {
        if(reduced || !playOnStart) { active=false; finished(); return }
        active=true; opacity=1; phase=0; sequence.restart()
    }
    function finish() { sequence.stop(); active=false; opacity=1; finished() }
    onReducedChanged: if(reduced && active) finish()
    Keys.onEscapePressed: finish()
    Keys.onSpacePressed: finish()
    MouseArea { anchors.fill: parent }
    Repeater { model: scene.active ? 28 : 0
        Rectangle { required property int index
            width: index%4===0 ? 18 : 2; height: width; radius: width/2
            color: width>2 ? 'transparent' : '#a9b4c4'; border.color: width>2 ? '#3f4a58' : 'transparent'
            x: ((index*197+70)%scene.width); y: ((index*113+41)%scene.height)-scene.phase*(10+index%5*8)
            opacity: Math.min(0.45,scene.phase*0.3)
        }
    }
    Column {
        anchors.centerIn: parent; spacing: 12
        opacity: Math.min(1,scene.phase*1.8); scale: 0.9+Math.min(1,scene.phase)*0.1
        NovaMark { width: 290; height: 218; anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: 'N O V A'; color: '#f0f3f8'; font.pixelSize: 32; font.letterSpacing: 10; anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: 'S E R V E R   S T U D I O'; color: '#788391'; font.pixelSize: 10; anchors.horizontalCenter: parent.horizontalCenter }
        Rectangle { width: 116; height: 1; color: '#323c49'; anchors.horizontalCenter: parent.horizontalCenter; anchors.topMargin: 12 }
        Text { text: 'Created by Nova'; color: '#9ca6b4'; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
    }
    Text { anchors.bottom: parent.bottom; anchors.bottomMargin: 46; anchors.horizontalCenter: parent.horizontalCenter; text: 'YOUR WORLD. YOUR RULES.'; font.pixelSize: 10; font.letterSpacing: 3; color: '#5d6877' }
    NButton { objectName: 'skipStartup'; text: 'Skip intro'; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 28; onClicked: scene.finish() }
    SequentialAnimation { id: sequence
        NumberAnimation { target: scene; property: 'phase'; from: 0; to: 1; duration: 850; easing.type: Easing.OutCubic }
        NumberAnimation { target: scene; property: 'phase'; to: 1.6; duration: 1250 }
        NumberAnimation { target: scene; property: 'opacity'; from: 1; to: 0; duration: 450; easing.type: Easing.InOutQuad }
        ScriptAction { script: { scene.active=false; scene.opacity=1; scene.finished() } }
    }
}
