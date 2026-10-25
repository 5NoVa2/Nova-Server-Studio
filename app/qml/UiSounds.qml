import QtQuick
import QtMultimedia
Item {
    id: bus
    objectName: 'uiSounds'
    property bool soundsEnabled: true
    property bool interactive: true
    property real masterVolume: 0.3
    property real lastHover: 0
    property real lastClick: 0
    property real lastTransition: 0
    signal requested(string kind)
    function stop() { hoverSound.stop(); clickSound.stop(); transitionSound.stop() }
    onSoundsEnabledChanged: if(!soundsEnabled) stop()
    onInteractiveChanged: if(!interactive) stop()
    onMasterVolumeChanged: if(masterVolume<=0) stop()
    function play(kind) {
        if(!soundsEnabled || !interactive || masterVolume<=0) return
        const now=Date.now()
        if(kind==='hover') {
            if(now-lastHover<110 || now-lastClick<150 || now-lastTransition<150) return
            lastHover=now
        } else if(kind==='click') {
            if(now-lastClick<100) return
            lastClick=now; hoverSound.stop()
        } else {
            if(now-lastTransition<160) return
            lastTransition=now; hoverSound.stop()
        }
        requested(kind)
        const effect=kind==='hover' ? hoverSound : kind==='click' ? clickSound : transitionSound
        // Never queue a sound to play after its interaction has finished.
        if(effect.status===SoundEffect.Ready) { effect.stop(); effect.play() }
    }
    SoundEffect { id: hoverSound; source: Qt.resolvedUrl('../sounds/hover.wav'); volume: bus.masterVolume*0.32 }
    SoundEffect { id: clickSound; source: Qt.resolvedUrl('../sounds/click.wav'); volume: bus.masterVolume*0.38 }
    SoundEffect { id: transitionSound; source: Qt.resolvedUrl('../sounds/transition.wav'); volume: bus.masterVolume*0.25 }
}
