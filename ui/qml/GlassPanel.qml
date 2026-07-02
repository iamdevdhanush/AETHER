import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#08FFFFFF"
    radius: 28
    border.color: "#0FFFFFFF"
    border.width: 1

    property bool hoverEffect: false
    property bool glowEffect: false
    property string paddingSize: "md"

    onGlowEffectChanged: {
        if (glowEffect) {
            glowAnimation.start()
        } else {
            glowAnimation.stop()
            glowRect.color = "#00A8D8FF"
        }
    }

    Rectangle {
        id: glowRect
        anchors.fill: parent
        radius: root.radius
        color: "#00A8D8FF"
        z: -1
    }

    SequentialAnimation {
        id: glowAnimation
        loops: Animation.Infinite
        PropertyAnimation {
            target: glowRect
            property: "color"
            to: "#26A8D8FF"
            duration: 1500
            easing.type: Easing.InOutSine
        }
        PropertyAnimation {
            target: glowRect
            property: "color"
            to: "#00A8D8FF"
            duration: 1500
            easing.type: Easing.InOutSine
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: root.hoverEffect
        onEntered: {
            if (root.hoverEffect) {
                root.color = "#14FFFFFF"
                root.border.color = "#1AFFFFFF"
            }
        }
        onExited: {
            if (root.hoverEffect) {
                root.color = "#08FFFFFF"
                root.border.color = "#0FFFFFFF"
            }
        }
    }

    property real _padding: paddingSize === "sm" ? 12 : (paddingSize === "lg" ? 32 : 20)
}
