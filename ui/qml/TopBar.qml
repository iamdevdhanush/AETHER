import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    height: 48
    color: "#04FFFFFF"
    border.color: "#0FFFFFFF"
    border.width: 1

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        spacing: 16

        Text {
            text: "AETHER"
            color: "#FFFFFF"
            font.pixelSize: 15
            font.weight: Font.DemiBold
            font.family: "Schibsted Grotesk"
            anchors.verticalCenter: parent.verticalCenter
        }

        Rectangle {
            width: 1
            height: 16
            color: "#1AFFFFFF"
            anchors.verticalCenter: parent.verticalCenter
        }

        Row {
            spacing: 6
            anchors.verticalCenter: parent.verticalCenter
            Text {
                text: "✦"
                color: "#A8D8FF"
                font.pixelSize: 11
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: "Llama 3.2"
                color: "#A0A0A0"
                font.pixelSize: 11
                font.weight: Font.Medium
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    Row {
        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter
        spacing: 16

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: "#00D27A"
            anchors.verticalCenter: parent.verticalCenter
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                PropertyAnimation { to: 0.4; duration: 1000; easing.type: Easing.InOutSine }
                PropertyAnimation { to: 1.0; duration: 1000; easing.type: Easing.InOutSine }
            }
        }

        Text {
            text: "Ollama"
            color: "#00D27A"
            font.pixelSize: 11
            font.weight: Font.Medium
            anchors.verticalCenter: parent.verticalCenter
        }

        Rectangle {
            width: 1
            height: 12
            color: "#1AFFFFFF"
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: "Voice"
            color: "#A0A0A0"
            font.pixelSize: 11
            font.weight: Font.Medium
            anchors.verticalCenter: parent.verticalCenter
        }

        Rectangle {
            width: 1
            height: 12
            color: "#1AFFFFFF"
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: "Settings"
            color: "#A0A0A0"
            font.pixelSize: 11
            font.weight: Font.Medium
            anchors.verticalCenter: parent.verticalCenter

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: bridge.set_view("settings")
            }
        }
    }
}
