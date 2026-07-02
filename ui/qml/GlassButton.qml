import QtQuick 2.15
import QtQuick.Controls 2.15

Button {
    id: root
    property string variant: "default"
    property string btnSize: "md"

    implicitWidth: _implicitWidth
    implicitHeight: _implicitHeight

    readonly property real _implicitWidth: btnSize === "sm" ? 80 : (btnSize === "lg" ? 160 : 120)
    readonly property real _implicitHeight: btnSize === "sm" ? 28 : (btnSize === "lg" ? 44 : 36)

    background: Rectangle {
        radius: 28
        color: {
            if (!root.enabled) return "#04FFFFFF"
            if (root.variant === "primary") return "#1AA8D8FF"
            if (root.variant === "danger") return "#1AFF5A5A"
            if (root.variant === "ghost") return "transparent"
            return "#08FFFFFF"
        }
        border.color: {
            if (!root.enabled) return "#04FFFFFF"
            if (root.variant === "primary") return "#4DA8D8FF"
            if (root.variant === "danger") return "#4DFF5A5A"
            if (root.variant === "ghost") return "transparent"
            return "#0FFFFFFF"
        }
        border.width: 1

        Behavior on color { ColorAnimation { duration: 200 } }
        Behavior on border.color { ColorAnimation { duration: 200 } }
    }

    contentItem: Text {
        text: root.text
        color: {
            if (!root.enabled) return "#60FFFFFF"
            if (root.variant === "primary") return "#A8D8FF"
            if (root.variant === "danger") return "#FF5A5A"
            if (root.variant === "ghost") return "#9A9A9A"
            return "#FFFFFF"
        }
        font.pixelSize: btnSize === "sm" ? 11 : 13
        font.family: "Inter"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    scale: pressed ? 0.98 : (hovered ? 1.02 : 1.0)
    Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
}
