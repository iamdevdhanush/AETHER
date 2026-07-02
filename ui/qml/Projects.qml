import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "transparent"

    Flickable {
        anchors.fill: parent
        anchors.margins: 32
        contentHeight: projectsColumn.height + 48
        clip: true

        Column {
            id: projectsColumn
            width: parent.width
            spacing: 24

            Text {
                text: "Projects"
                color: "#FFFFFF"
                font.pixelSize: 24
                font.family: "Inter"
                font.weight: Font.Light
            }

            GlassCard {
                width: parent.width
                height: 100
                title: "No projects yet"
                subtitle: "Projects will appear here once created"
                clickable: false
            }
        }
    }
}
