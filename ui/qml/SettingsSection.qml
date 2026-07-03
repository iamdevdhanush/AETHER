import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    implicitHeight: layout.implicitHeight
    implicitWidth: parent ? parent.width : 300

    required property var themeObj
    required property string title

    default property alias content: contentContainer.data

    ColumnLayout {
        id: layout
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        // Section title
        Text {
            text: root.title
            color: root.themeObj.textMuted
            font.pixelSize: 10
            font.letterSpacing: 1
            font.weight: Font.Medium
            Layout.leftMargin: 16
            Layout.topMargin: 20
            Layout.bottomMargin: 10
        }

        // Content area
        Item {
            id: contentContainer
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.bottomMargin: 12
            implicitHeight: childrenRect.height
        }

        // Bottom separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }
    }
}
