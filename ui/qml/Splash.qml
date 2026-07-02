import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#050505"

    property var steps: [
        {label: "Loading AI Engine", status: "pending"},
        {label: "Connecting to Ollama", status: "pending"},
        {label: "Initializing Voice Engine", status: "pending"},
        {label: "Loading Memory", status: "pending"},
        {label: "Loading Plugins", status: "pending"},
        {label: "System Ready", status: "pending"}
    ]

    signal finished()

    Component.onCompleted: {
        loadTimer.start()
    }

    Timer {
        id: loadTimer
        interval: 100
        repeat: true
        property int stepIndex: 0
        property int phase: 0  // 0 = loading, 1 = done

        onTriggered: {
            if (phase === 0) {
                steps[stepIndex].status = "loading"
                stepRepeater.itemAt(stepIndex).updateStatus("loading")
                phase = 1
                interval = 500
            } else {
                steps[stepIndex].status = "done"
                stepRepeater.itemAt(stepIndex).updateStatus("done")
                stepIndex++
                phase = 0
                interval = 400

                if (stepIndex >= steps.length) {
                    loadTimer.stop()
                    completeTimer.start()
                }
            }
        }
    }

    Timer {
        id: completeTimer
        interval: 600
        onTriggered: {
            root.opacity = 0
            fadeOutAnimation.start()
        }
    }

    NumberAnimation {
        id: fadeOutAnimation
        target: root
        property: "opacity"
        to: 0
        duration: 500
        easing.type: Easing.OutCubic
        onFinished: root.finished()
    }

    Rectangle {
        id: ambientGlow
        width: 500
        height: 500
        radius: 250
        anchors.centerIn: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0FA8D8FF" }
            GradientStop { position: 0.7; color: "transparent" }
        }
        opacity: 0.6
    }

    Column {
        anchors.centerIn: parent
        spacing: 48

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 16

            Rectangle {
                id: orb
                anchors.horizontalCenter: parent.horizontalCenter
                width: 64
                height: 64
                radius: 32
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#CCA8D8FF" }
                    GradientStop { position: 0.6; color: "#33A8D8FF" }
                    GradientStop { position: 0.8; color: "transparent" }
                }
                NumberAnimation on scale {
                    loops: Animation.Infinite
                    from: 1.0
                    to: 1.05
                    duration: 3000
                    easing.type: Easing.InOutSine
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "AETHER"
                color: "#FFFFFF"
                font.pixelSize: 30
                font.weight: Font.DemiBold
                font.family: "Schibsted Grotesk"
                font.letterSpacing: -1
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Initializing..."
                color: "#A0A0A0"
                font.pixelSize: 14
                font.family: "Inter"
            }
        }

        Column {
            id: stepList
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 12

            Repeater {
                id: stepRepeater
                model: root.steps

                Item {
                    id: stepItem
                    width: 260
                    height: 20
                    property string currentStatus: "pending"

                    function updateStatus(status) {
                        currentStatus = status
                    }

                    Row {
                        spacing: 12
                        anchors.verticalCenter: parent.verticalCenter

                        Item {
                            width: 16
                            height: 16
                            anchors.verticalCenter: parent.verticalCenter

                            Rectangle {
                                anchors.fill: parent
                                radius: 8
                                visible: currentStatus === "pending"
                                color: "transparent"
                                border.color: "#1AFFFFFF"
                                border.width: 1.5
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: 8
                                visible: currentStatus === "loading"
                                color: "transparent"
                                border.color: "#4DA8D8FF"
                                border.width: 2
                                NumberAnimation on rotation {
                                    loops: Animation.Infinite
                                    from: 0
                                    to: 360
                                    duration: 1000
                                }
                            }

                            Text {
                                anchors.centerIn: parent
                                visible: currentStatus === "done"
                                text: "✓"
                                color: "#00D27A"
                                font.pixelSize: 12
                                font.weight: Font.Bold
                            }
                        }

                        Text {
                            text: modelData.label
                            color: currentStatus === "done" ? "#00D27A" :
                                   currentStatus === "loading" ? "#A8D8FF" : "#A0A0A0"
                            font.pixelSize: 13
                            font.family: "Inter"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }
    }
}
