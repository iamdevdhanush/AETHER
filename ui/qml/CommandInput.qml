import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    height: 52
    radius: 28
    color: "#08FFFFFF"
    border.color: "#0FFFFFFF"
    border.width: 1

    signal messageSent(string text)

    Row {
        anchors.fill: parent
        anchors.leftMargin: 24
        anchors.rightMargin: 6
        anchors.topMargin: 6
        anchors.bottomMargin: 6
        spacing: 12

        TextInput {
            id: inputField
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 60
            color: "#FFFFFF"
            font.pixelSize: 14
            font.family: "Inter"
            clip: true
            focus: true

            Text {
                anchors.fill: parent
                text: "Ask AETHER anything..."
                color: "#66FFFFFF"
                font: parent.font
                visible: !inputField.text.length && !inputField.focus
            }

            Keys.onReturnPressed: sendMessage()
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 32
            height: 32
            radius: 16
            color: "#1AA8D8FF"

            Text {
                anchors.centerIn: parent
                text: "→"
                color: "#A8D8FF"
                font.pixelSize: 14
                font.weight: Font.Bold
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sendMessage()
            }
        }
    }

    function sendMessage() {
        var text = inputField.text.trim()
        if (text.length > 0) {
            root.messageSent(text)
            inputField.text = ""
        }
    }
}
