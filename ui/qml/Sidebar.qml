import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    width: 224
    color: "transparent"

    property string activeItem: "home"
    property var sections: [
        {
            name: "Workspace",
            items: [
                {id: "home", icon: "🏠", label: "Home"},
                {id: "chat", icon: "💬", label: "Conversations"},
                {id: "dashboard", icon: "📊", label: "Dashboard"},
                {id: "plugins", icon: "🔌", label: "Plugins"},
                {id: "settings", icon: "⚙️", label: "Settings"}
            ]
        }
    ]

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: 24
        spacing: 16

        Repeater {
            model: sections

            Column {
                width: parent.width
                spacing: 4

                Text {
                    x: 16
                    text: modelData.name
                    color: "#6A6A6A"
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                    font.weight: Font.Medium
                    visible: modelData.name.length > 0
                }

                Repeater {
                    model: modelData.items

                    Item {
                        width: parent.width
                        height: 36

                        Rectangle {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            radius: 8
                            color: modelData.id === activeItem ? "#1AA8D8FF" : "transparent"
                        }

                        Row {
                            anchors.left: parent.left
                            anchors.leftMargin: 16
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 10

                            Text {
                                text: modelData.icon
                                font.pixelSize: 14
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: modelData.label
                                color: modelData.id === activeItem ? "#A8D8FF" : "#9A9A9A"
                                font.pixelSize: 13
                                font.weight: modelData.id === activeItem ? Font.Medium : Font.Normal
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                activeItem = modelData.id
                                bridge.set_view(modelData.id)
                            }
                        }
                    }
                }
            }
        }
    }
}
