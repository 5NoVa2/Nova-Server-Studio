import QtQuick
import QtQuick.Controls
import QtMultimedia
Rectangle {
    id: scene
    property bool reduced: false
    property bool playOnStart: true
    property bool soundEnabled: true
    property real soundVolume: 0.3
    property bool soundPending: false
    property bool active: false
    property real phase: 0
    signal finished()
    color: '#030507'; visible: active; opacity: active ? 1 : 0
    focus: active
    function begin() {
        if(reduced || !playOnStart) { active=false; finished(); return }
        active=true; opacity=1; phase=0; forceActiveFocus(); sequence.restart(); soundPending=soundEnabled && soundVolume>0; playSound()
    }
    function finish() { soundPending=false; introSound.stop(); sequence.stop(); active=false; opacity=1; finished() }
    function clamp(value) { return Math.max(0,Math.min(1,value)) }
    function playSound() {
        if(soundPending && active && soundEnabled && soundVolume>0 && introSound.status===SoundEffect.Ready) {
            // Do not start a delayed effect after its visual cue has passed.
            soundPending=false
            if(phase<0.08) introSound.play()
        }
    }
    onSoundEnabledChanged: if(!soundEnabled) { soundPending=false; introSound.stop() }
    onActiveChanged: if(!active) { soundPending=false; introSound.stop() }
    SoundEffect {
        id: introSound; objectName: 'startupAudio'
        source: Qt.resolvedUrl('../sounds/startup.wav')
        volume: scene.soundVolume
        onStatusChanged: scene.playSound()
    }
    onReducedChanged: if(reduced && active) finish()
    Keys.onEscapePressed: finish()
    Keys.onSpacePressed: finish()
    MouseArea { anchors.fill: parent }
    Canvas {
        id: cosmos; anchors.fill: parent; renderStrategy: Canvas.Threaded
        onWidthChanged: if(scene.active) requestPaint()
        onHeightChanged: if(scene.active) requestPaint()
        onPaint: {
            const c=getContext('2d'); c.reset()
            const p=scene.phase, w=width, h=height, cx=w/2, cy=h*0.43
            const unit=Math.min(w/1260,h/850)
            const settle=scene.clamp((p-0.22)/0.38), dissipate=scene.clamp((p-0.65)/0.22)
            const haze=1-dissipate*0.85
            // A soft diagonal cloud, with no bitmap or video asset to load.
            c.save(); c.translate(cx,cy); c.rotate(-0.38)
            c.scale(1,0.27)
            let mist=c.createRadialGradient(0,0,0,0,0,w*0.62)
            mist.addColorStop(0,'rgba(154,174,191,'+(0.18*haze)+')')
            mist.addColorStop(0.38,'rgba(92,112,131,'+(0.09*haze)+')')
            mist.addColorStop(1,'rgba(0,0,0,0)')
            c.fillStyle=mist; c.fillRect(-w,-h,w*2,h*2);c.restore()
            // Deterministic stars rush toward the viewer, then slow to a drift.
            const travel=p<0.31 ? p*2.8 : 0.868+(p-0.31)*0.065
            for(let i=0;i<420;i++) {
                const a=i*2.39996323
                const seed=((i*73)%419)/419
                const depth=(seed+travel)%1
                const r=(0.035+depth*depth)*Math.max(w,h)*0.8
                const x=cx+Math.cos(a)*r, y=cy+Math.sin(a)*r*0.72
                const brightness=(0.10+seed*0.42)*(1-dissipate*0.65)
                const trail=(1-settle)*(8+depth*depth*68)*unit
                c.strokeStyle='rgba(210,223,236,'+brightness+')';c.lineWidth=(i%13===0?1.5:0.7)*unit
                c.beginPath();c.moveTo(x,y);c.lineTo(x+Math.cos(a)*trail,y+Math.sin(a)*trail*0.72);c.stroke()
            }
            // Silver contour lines resolve into the familiar ringed planet.
            const appear=scene.clamp((p-0.13)/0.17)*(1-scene.clamp((p-0.58)/0.17))
            if(appear>0) {
                c.save();c.translate(cx,cy);c.rotate(-0.34)
                const scale=(1.35-settle*0.35)*unit
                c.scale(scale,scale)
                const distortion=(1-settle)*31
                const ink=c.createLinearGradient(-165,-80,165,80)
                ink.addColorStop(0,'#576573');ink.addColorStop(0.35,'#eff5fa');ink.addColorStop(0.55,'#8e9daa');ink.addColorStop(0.8,'#dde7ef');ink.addColorStop(1,'#455360')
                c.globalAlpha=appear;c.strokeStyle=ink
                for(let ring=0;ring<7;ring++) {
                    c.lineWidth=ring%3===0?1.9:0.8;c.beginPath()
                    for(let j=0;j<=160;j++) {
                        const a=j/160*Math.PI*2
                        const wave=distortion*(Math.sin(a*7+p*24+ring*0.4)*0.55+Math.cos(a*11-p*16)*0.45)
                        const x=Math.cos(a)*(125+ring*5+wave)
                        const y=Math.sin(a)*(36+ring*1.5+wave*0.4)
                        if(j===0)c.moveTo(x,y);else c.lineTo(x,y)
                    }
                    c.stroke()
                }
                for(let ring=0;ring<3;ring++) {
                    c.lineWidth=ring===1?1.8:0.8;c.beginPath()
                    for(let j=0;j<=140;j++) {
                        const a=j/140*Math.PI*2
                        const wave=distortion*0.42*Math.sin(a*8+p*20+ring)
                        const r=61+ring*2+wave
                        const x=Math.cos(a)*r,y=Math.sin(a)*r-7
                        if(j===0)c.moveTo(x,y);else c.lineTo(x,y)
                    }
                    c.stroke()
                }
                c.restore()
            }
            // Small glass-like droplets disperse around the forming logo.
            const droplets=scene.clamp((p-0.23)/0.14)*(1-scene.clamp((p-0.58)/0.20))
            if(droplets>0) for(let i=0;i<64;i++) {
                const a=i*2.39996323,r=(85+(i*47)%240+(p-0.3)*140)*unit
                const x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r*0.7
                const size=(1.3+(i*7)%6)*unit
                c.strokeStyle='rgba(199,216,229,'+(droplets*(0.16+(i%4)*0.09))+')';c.lineWidth=0.8*unit
                c.beginPath();c.arc(x,y,size,0,Math.PI*2);c.stroke()
                c.fillStyle='rgba(232,242,250,'+(droplets*0.3)+')';c.beginPath();c.arc(x-size*0.24,y-size*0.3,size*0.22,0,Math.PI*2);c.fill()
            }
        }
    }
    Timer { interval: 33; repeat: true; running: scene.active; onTriggered: cosmos.requestPaint() }
    Item {
        anchors.horizontalCenter: parent.horizontalCenter
        y: scene.height*0.43-height/2; width: 360; height: 270
        opacity: scene.clamp((scene.phase-0.48)/0.19)
        scale: 1.04-scene.clamp((scene.phase-0.48)/0.22)*0.04
        SaturnMark { anchors.fill: parent }
    }
    Column {
        anchors.horizontalCenter: parent.horizontalCenter; y: scene.height*0.43+128
        spacing: 15; opacity: scene.clamp((scene.phase-0.55)/0.17)
        Text { text: 'SATURN'; color: '#e0e7ed'; font.pixelSize: 29; font.weight: Font.Light; font.letterSpacing: 12; anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: 'SERVER LAUNCHER'; color: '#7c8998'; font.pixelSize: 10; font.letterSpacing: 4; anchors.horizontalCenter: parent.horizontalCenter }
        Rectangle { width: 80; height: 1; color: '#3a4653'; anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: 'Created by Nova'; color: '#94a0ae'; font.pixelSize: 11; anchors.horizontalCenter: parent.horizontalCenter }
    }
    Text { anchors.bottom: parent.bottom; anchors.bottomMargin: 46; anchors.horizontalCenter: parent.horizontalCenter; text: 'YOUR WORLD. YOUR RULES.'; font.pixelSize: 10; font.letterSpacing: 3; color: '#677383'; opacity: scene.clamp((scene.phase-0.65)/0.15) }
    NButton { objectName: 'skipStartup'; text: 'Skip intro'; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 28; onClicked: scene.finish() }
    SequentialAnimation { id: sequence; objectName: 'startupSequence'
        NumberAnimation { target: scene; property: 'phase'; from: 0; to: 1; duration: 4200 }
        NumberAnimation { target: scene; property: 'opacity'; from: 1; to: 0; duration: 550; easing.type: Easing.InOutQuad }
        ScriptAction { script: { scene.active=false; scene.opacity=1; scene.finished() } }
    }
}
