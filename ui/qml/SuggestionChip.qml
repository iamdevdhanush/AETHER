import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    implicitHeight: 34
    implicitWidth: chipText.implicitWidth + 24
    radius: 17
    color: chipHover.containsMouse ? themeObj.bgSelected : themeObj.bgCard
    border.color: chipHover.containsMouse ? themeObj.accent : themeObj.border
    border.width: 1

    required property var themeObj
    required property string text

    signal clicked()

    Behavior on color { ColorAnimation { duration: 120 } }
    Behavior on border.color { ColorAnimation { duration: 120 } }

    Text {
        id: chipText
        anchors.centerIn: parent
        text: root.text
        color: chipHover.containsMouse ? root.themeObj.textPrimary : root.themeObj.textSec
        font.pixelSize: 12
    }

    MouseArea {
        id: chipHover
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
