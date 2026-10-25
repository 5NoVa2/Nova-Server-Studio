import QtQuick
Canvas {
    id: mark
    implicitWidth: 240; implicitHeight: 180
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c=getContext('2d'); c.reset(); c.scale(width/240,height/180)
        let glow=c.createRadialGradient(120,86,8,120,86,100)
        glow.addColorStop(0,'#29313b'); glow.addColorStop(1,'#0029313b')
        c.fillStyle=glow; c.fillRect(0,0,240,180)
        c.save(); c.translate(120,90); c.rotate(-0.34); c.scale(1,0.31)
        for(let i=0;i<4;i++) { c.beginPath(); c.arc(0,0,86+i*5,0,Math.PI*2); c.strokeStyle=i===1?'#b6c0cc':'#53606e'; c.lineWidth=i===1?2:1; c.stroke() }
        c.restore()
        let sphere=c.createLinearGradient(85,48,158,130)
        sphere.addColorStop(0,'#e5e9ef'); sphere.addColorStop(0.3,'#788594'); sphere.addColorStop(0.7,'#232b34'); sphere.addColorStop(1,'#0b1017')
        c.beginPath(); c.arc(120,86,42,0,Math.PI*2); c.fillStyle=sphere; c.fill(); c.strokeStyle='#86929f'; c.lineWidth=1; c.stroke()
        c.beginPath(); c.moveTo(106,104); c.lineTo(106,69); c.lineTo(134,104); c.lineTo(134,69); c.lineWidth=3; c.lineCap='round'; c.lineJoin='round'; c.strokeStyle='#f6f8fc'; c.stroke()
        c.save(); c.translate(120,90); c.rotate(-0.34); c.scale(1,0.31)
        c.beginPath(); c.arc(0,0,96,0,Math.PI); c.strokeStyle='#c8d0da'; c.lineWidth=2; c.stroke(); c.restore()
    }
}
