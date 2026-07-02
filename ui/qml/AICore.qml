import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    width: 320
    height: 320

    property string aiState: "idle"
    property real amplitude: 0.0
    property color stateColor: getStateColor()

    function getStateColor() {
        switch (aiState) {
            case "listening":
            case "thinking":
            case "speaking":
                return "#A8D8FF"
            case "executing":
            case "success":
                return "#00D27A"
            case "error":
                return "#FF5A5A"
            default:
                return "#8CFFFFFF"
        }
    }

    onAiStateChanged: stateColor = getStateColor()

    Rectangle {
        id: glowRing
        anchors.centerIn: parent
        width: root.width * 0.9
        height: root.height * 0.9
        radius: width / 2
        color: "transparent"
        border.color: stateColor
        border.width: 0
        opacity: 0.3

        SequentialAnimation on border.width {
            id: ringAnim
            running: aiState === "executing"
            loops: Animation.Infinite
            NumberAnimation { to: 4; duration: 1500; easing.type: Easing.InOutSine }
            NumberAnimation { to: 0; duration: 1500; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: outerGlow
        anchors.centerIn: parent
        width: root.width * 0.8
        height: root.height * 0.8
        radius: width / 2
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(stateColor.r, stateColor.g, stateColor.b, 0.15) }
            GradientStop { position: 1.0; color: "transparent" }
        }
        scale: aiState === "listening" || aiState === "speaking" ? 1.0 + amplitude * 1.5 : 1.0
        Behavior on scale { NumberAnimation { duration: 100 } }
    }

    Rectangle {
        id: orb
        anchors.centerIn: parent
        width: root.width * 0.5
        height: root.height * 0.5
        radius: width / 2
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.8) }
            GradientStop { position: 0.4; color: stateColor }
            GradientStop { position: 1.0; color: "transparent" }
        }

        property real breatheOffset: 0.0

        SequentialAnimation on breatheOffset {
            loops: Animation.Infinite
            NumberAnimation { to: 3; duration: 2000; easing.type: Easing.InOutSine }
            NumberAnimation { to: -3; duration: 2000; easing.type: Easing.InOutSine }
        }

        scale: {
            var base = 1.0 + breatheOffset / width
            if (aiState === "listening" || aiState === "speaking")
                base += amplitude * 1.5
            return base
        }
        Behavior on scale { NumberAnimation { duration: 100 } }
    }

    Canvas {
        id: particlesCanvas
        anchors.fill: parent
        visible: aiState === "thinking" || aiState === "listening"

        property var particles: []
        property real time: 0

        Timer {
            running: parent.visible
            interval: 50
            repeat: true
            onTriggered: {
                particlesCanvas.time += 0.05
                if (particlesCanvas.particles.length < 40) {
                    particlesCanvas.particles.push({
                        x: Math.random() * particlesCanvas.width,
                        y: Math.random() * particlesCanvas.height,
                        size: Math.random() * 3 + 1,
                        speedX: (Math.random() - 0.5) * 0.5,
                        speedY: (Math.random() - 0.5) * 0.5,
                        opacity: Math.random() * 0.5 + 0.2
                    })
                }
                particlesCanvas.requestPaint()
            }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            for (var i = 0; i < particles.length; i++) {
                var p = particles[i]
                p.x += p.speedX
                p.y += p.speedY

                if (p.x < 0) p.x = width
                if (p.x > width) p.x = 0
                if (p.y < 0) p.y = height
                if (p.y > height) p.y = 0

                ctx.globalAlpha = p.opacity * (0.5 + 0.5 * Math.sin(time + i))
                ctx.fillStyle = stateColor
                ctx.beginPath()
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
                ctx.fill()
            }
            ctx.globalAlpha = 1.0
        }
    }

    Text {
        id: stateLabel
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: orb.bottom
        anchors.topMargin: 12
        text: {
            switch (aiState) {
                case "listening": return "Listening"
                case "thinking": return "Thinking"
                case "executing": return "Executing"
                case "speaking": return "Speaking"
                case "error": return "Error"
                default: return ""
            }
        }
        color: stateColor
        font.pixelSize: 12
        font.family: "Inter"
        font.weight: Font.Medium
        visible: text.length > 0
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 300 } }
    }
}
