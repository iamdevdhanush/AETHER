import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property string title: ""
    property string subtitle: ""
    property bool clickable: false
    signal clicked()

    height: cardColumn.height + 40

    Rectangle {
        id: cardBg
        anchors.fill: parent
        anchors.margins: 0
        radius: 28
        color: "#08FFFFFF"
        border.color: "#0FFFFFFF"
        border.width: 1

        MouseArea {
            anchors.fill: parent
            hoverEnabled: root.clickable
            cursorShape: root.clickable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (root.clickable) root.clicked()
            onEntered: {
                if (root.clickable) {
                    cardBg.color = "#14FFFFFF"
                    cardBg.border.color = "#1AFFFFFF"
                }
            }
            onExited: {
                if (root.clickable) {
                    cardBg.color = "#08FFFFFF"
                    cardBg.border.color = "#0FFFFFFF"
                }
            }
        }
    }

    Column {
        id: cardColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 4

        Text {
            text: root.title
            font.pixelSize: 13
            font.family: "Inter"
            font.weight: Font.Medium
            color: "#FFFFFF"
            visible: root.title.length > 0
        }
        Text {
            text: root.subtitle
            font.pixelSize: 11
            font.family: "Inter"
            color: "#9A9A9A"
            visible: root.subtitle.length > 0
        }
    }
}
