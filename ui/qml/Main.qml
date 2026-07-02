import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    id: appWindow
    visible: true
    title: "AETHER"
    width: 1280
    height: 800
    minimumWidth: 900
    minimumHeight: 600
    color: "#050505"

    // View stack: splash -> main
    property bool showSplash: true
    property string currentView: "home"

    Component.onCompleted: {
        // Connect bridge signals
        bridge.splashFinished.connect(function() {
            showSplash = false
        })
        bridge.viewChanged.connect(function(view) {
            currentView = view
        })
    }

    // === SPLASH SCREEN ===
    Splash {
        id: splashScreen
        anchors.fill: parent
        visible: showSplash
        opacity: showSplash ? 1.0 : 0.0
        z: 100

        Behavior on opacity { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }

        onFinished: {
            bridge.finish_splash()
        }
    }

    // === MAIN APP ===
    Rectangle {
        anchors.fill: parent
        color: "#050505"
        visible: !showSplash
        opacity: showSplash ? 0.0 : 1.0

        Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }

        Column {
            anchors.fill: parent
            spacing: 0

            TopBar {
                id: topBar
                width: parent.width
            }

            Row {
                width: parent.width
                height: parent.height - topBar.height

                Sidebar {
                    id: sidebar
                    height: parent.height
                    activeItem: currentView
                }

                Rectangle {
                    width: parent.width - sidebar.width
                    height: parent.height
                    color: "transparent"

                    Loader {
                        anchors.fill: parent
                        sourceComponent: {
                            switch (currentView) {
                                case "home": return homeComponent
                                case "chat": return chatComponent
                                case "dashboard": return dashboardComponent
                                case "plugins": return pluginsComponent
                                case "settings": return settingsComponent
                                case "projects": return projectsComponent
                                default: return homeComponent
                            }
                        }
                    }
                }
            }
        }
    }

    Component {
        id: homeComponent
        Home { anchors.fill: parent }
    }

    Component {
        id: chatComponent
        Chat { anchors.fill: parent }
    }

    Component {
        id: dashboardComponent
        Dashboard { anchors.fill: parent }
    }

    Component {
        id: pluginsComponent
        Plugins { anchors.fill: parent }
    }

    Component {
        id: settingsComponent
        Settings { anchors.fill: parent }
    }

    Component {
        id: projectsComponent
        Projects { anchors.fill: parent }
    }
}
