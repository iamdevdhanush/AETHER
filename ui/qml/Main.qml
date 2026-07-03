import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: root
    visible: true
    width: 1280
    height: 800
    minimumWidth: 900
    minimumHeight: 600
    title: "AETHER"
    color: "#0A0A16"

    // ── Theme / Design Tokens ────────────────────────────────────────────
    QtObject {
        id: theme
        readonly property color bg:          "#0A0A16"
        readonly property color bgPanel:     "#0F0F1E"
        readonly property color bgCard:      "#141428"
        readonly property color bgHover:     "#1A1A30"
        readonly property color bgSelected:  "#1E1E38"
        readonly property color border:      "#252540"
        readonly property color borderBright:"#353565"
        readonly property color accent:      "#5B5BFF"
        readonly property color accentDim:   "#3A3A99"
        readonly property color accentGlow:  "#7070FF"
        readonly property color textPrimary: "#E8E8FF"
        readonly property color textSec:     "#9090CC"
        readonly property color textMuted:   "#5A5A88"
        readonly property color success:     "#40CC80"
        readonly property color warning:     "#FFAA40"
        readonly property color error:       "#FF5566"
        readonly property color user:        "#7B7BFF"
        readonly property color assistant:   "#40CC80"
        readonly property int   radius:      10
        readonly property int   radiusSm:    6
        readonly property int   radiusLg:    14
    }

    // ── State ────────────────────────────────────────────────────────────
    property bool sidebarOpen:      true
    property bool settingsOpen:     false
    property bool timelineOpen:     false
    property bool memoryOpen:       false
    property string currentSection: "conversation"

    // ── Bridge connections ───────────────────────────────────────────────
    Connections {
        target: bridge

        function onStreamChunk(chunk) {
            conversationPanel.appendStreamChunk(chunk)
        }
        function onStreamComplete() {
            conversationPanel.finalizeStream()
        }
        function onStreamError(error) {
            conversationPanel.showError(error)
        }
        function onMessageReceived(role, content) {
            conversationPanel.appendMessage(role, content)
        }
        function onConversationsLoaded(conversations) {
            sidebar.updateConversations(conversations)
        }
        function onConversationLoaded(messages) {
            conversationPanel.loadMessages(messages)
        }
        function onConversationCreated(id, title) {
            bridge.loadConversations()
        }
        function onSystemStatsUpdated(stats) {
            topBar.updateStats(stats)
        }
        function onPluginsLoaded(plugins) {
            if (pluginsPanel.visible) {
                pluginsPanel.updatePlugins(plugins)
            }
        }
        function onTimelineEventAdded(event) {
            timelinePanel.addEvent(event)
        }
        function onMemoriesLoaded(memories) {
            memoryPanel.updateMemories(memories)
        }
        function onStatusMessage(msg) {
            topBar.setStatus(msg)
        }
        function onErrorOccurred(err) {
            topBar.setStatus("Error: " + err)
        }
    }

    // ── Root Layout ──────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Top Bar
        TopBar {
            id: topBar
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            themeObj: theme
            onToggleSidebar: root.sidebarOpen = !root.sidebarOpen
            onToggleTimeline: root.timelineOpen = !root.timelineOpen
            onToggleSettings: root.settingsOpen = !root.settingsOpen
            onToggleMemory: root.memoryOpen = !root.memoryOpen
        }

        // Thin separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: theme.border
        }

        // Main Content Area
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Sidebar
            Sidebar {
                id: sidebar
                Layout.preferredWidth: root.sidebarOpen ? 260 : 0
                Layout.fillHeight: true
                visible: root.sidebarOpen
                themeObj: theme

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
                }

                onConversationSelected: (convId) => {
                    bridge.loadConversation(convId)
                }
                onNewConversation: {
                    bridge.newConversation()
                }
            }

            // Sidebar separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: theme.border
                visible: root.sidebarOpen
            }

            // Conversation
            ConversationPanel {
                id: conversationPanel
                Layout.fillWidth: true
                Layout.fillHeight: true
                themeObj: theme
            }

            // Execution Timeline
            Rectangle {
                width: 1
                Layout.fillHeight: true
                color: theme.border
                visible: root.timelineOpen
            }

            ExecutionTimeline {
                id: timelinePanel
                Layout.preferredWidth: root.timelineOpen ? 280 : 0
                Layout.fillHeight: true
                visible: root.timelineOpen
                themeObj: theme

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
                }
            }
        }

        // Separator above input
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: theme.border
        }

        // Command Input
        CommandInput {
            id: commandInput
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            themeObj: theme
            onSendMessage: (text) => {
                bridge.sendMessage(text)
            }
            onExecutePlugin: (name, payload) => {
                bridge.executePlugin(name, payload)
            }
        }
    }

    // ── Overlays ─────────────────────────────────────────────────────────

    // Settings panel (slide in from right)
    SettingsPanel {
        id: settingsPanel
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 360
        visible: root.settingsOpen
        themeObj: theme
        onClose: root.settingsOpen = false
    }

    // Memory panel (slide in from right)
    MemoryPanel {
        id: memoryPanel
        anchors.right: root.settingsOpen ? settingsPanel.left : parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 320
        visible: root.memoryOpen
        themeObj: theme
        onClose: root.memoryOpen = false
    }

    // ── Startup ──────────────────────────────────────────────────────────
    Component.onCompleted: {
        bridge.loadConversations()
        bridge.loadPlugins()
    }
}
