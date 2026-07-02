import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "transparent"

    property string greeting: "Good Evening"
    property string aiState: bridge.aiState
    property real aiAmplitude: 0.0

    Component.onCompleted: {
        var hour = new Date().getHours()
        if (hour < 12) greeting = "Good Morning"
        else if (hour < 17) greeting = "Good Afternoon"
        else greeting = "Good Evening"

        bridge.aiStateChanged.connect(function(state) {
            aiState = state
        })
        bridge.amplitudeChanged.connect(function(amp) {
            aiAmplitude = amp
        })
    }

    Timer {
        id: amplitudeTimer
        interval: 100
        repeat: true
        running: aiState === "listening" || aiState === "speaking"
        onTriggered: {
            aiAmplitude = Math.random() * 0.5 + 0.1
        }
    }

    Row {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24

        Item {
            width: 224
            height: parent.height

            Column {
                width: parent.width
                spacing: 16

                ConversationList {
                    id: convList
                    width: parent.width
                    height: 200
                }

                Rectangle {
                    width: parent.width
                    height: 120
                    color: "#08FFFFFF"
                    radius: 28
                    border.color: "#0FFFFFFF"
                    border.width: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        Text {
                            text: "Running Tasks"
                            color: "#80FFFFFF"
                            font.pixelSize: 10
                            font.letterSpacing: 1.5
                            font.weight: Font.Medium
                        }

                        Text {
                            text: "No active tasks"
                            color: "#669A9A9A"
                            font.pixelSize: 12
                            font.family: "Inter"
                        }
                    }
                }

                QuickActions {
                    width: parent.width
                    height: 160
                }
            }
        }

        Item {
            width: parent.width - 224 - 224 - 48
            height: parent.height

            Column {
                anchors.centerIn: parent
                spacing: 8

                AICore {
                    id: aiCore
                    anchors.horizontalCenter: parent.horizontalCenter
                    aiState: root.aiState
                    amplitude: root.aiAmplitude
                }

                Item { width: 1; height: 16 }

                Column {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 4

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: root.greeting + ", Sir."
                        color: "#FFFFFF"
                        font.pixelSize: 28
                        font.weight: Font.Thin
                        font.letterSpacing: 1
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "How may I assist you today?"
                        color: "#9A9A9A"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        font.letterSpacing: 0.5
                    }
                }

                Item { width: 1; height: 16 }

                Row {
                    id: waveform
                    anchors.horizontalCenter: parent.horizontalCenter
                    height: 32
                    spacing: 3
                    visible: aiState === "listening" || aiState === "speaking"

                    Repeater {
                        model: 48
                        Rectangle {
                            width: 2
                            height: {
                                var base = 4
                                var amp = aiAmplitude * 24
                                var sin = Math.sin(index * 0.3 + Date.now() * 0.005)
                                return base + Math.abs(sin) * amp
                            }
                            radius: 1
                            color: "#99A8D8FF"
                            anchors.verticalCenter: parent.verticalCenter

                            Behavior on height { NumberAnimation { duration: 80 } }
                        }
                    }
                }

                Item { width: 1; height: 24 }

                CommandInput {
                    id: commandInput
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 512

                    onMessageSent: function(text) {
                        bridge.send_message(text, "")
                    }
                }
            }
        }

        Item {
            width: 224
            height: parent.height

            SystemMonitor {
                id: sysMonitor
                width: parent.width
                height: parent.height
            }
        }
    }
}
