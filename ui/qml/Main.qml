import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: root
    visible: true
    width:        1280
    height:        800
    minimumWidth:  960
    minimumHeight: 640
    title: "AETHER"
    color: "#0A0A16"

    // ── Design Tokens ─────────────────────────────────────────────────────
    QtObject {
        id: theme
        readonly property color bg:           "#0A0A16"
        readonly property color bgPanel:      "#0D0D1A"
        readonly property color bgCard:       "#111120"
        readonly property color bgHover:      "#16162A"
        readonly property color bgSelected:   "#1A1A32"
        readonly property color border:       "#1E1E3A"
        readonly property color borderBright: "#2E2E55"
        readonly property color accent:       "#5B5BFF"
        readonly property color accentDim:    "#3A3A99"
        readonly property color accentGlow:   "#7070FF"
        readonly property color textPrimary:  "#EAEAFF"
        readonly property color textSec:      "#8888BB"
        readonly property color textMuted:    "#4A4A77"
        readonly property color success:      "#3EC97A"
        readonly property color warning:      "#F5A623"
        readonly property color error:        "#FF4D5E"
        readonly property color user:         "#7272FF"
        readonly property color assistant:    "#3EC97A"
        readonly property int   radius:       12
        readonly property int   radiusSm:      7
        readonly property int   radiusLg:     16
    }

    // ── State ─────────────────────────────────────────────────────────────
    property bool sidebarOpen:  true
    property bool settingsOpen: false
    property bool timelineOpen: false
    property bool memoryOpen:   false

    // FIXED MN-1: Track animation state with a plain bool property instead of
    // relying on NumberAnimation.running inside a Behavior (unreliable scope).
    property bool sidebarAnimating:  false
    property bool timelineAnimating: false

    // ── Bridge connections ─────────────────────────────────────────────────
    Connections {
        target: bridge

        function onStreamChunk(chunk)            { conversationPanel.appendStreamChunk(chunk) }
        function onStreamComplete()              { conversationPanel.finalizeStream() }
        function onStreamError(error)            { conversationPanel.showError(error) }
        function onMessageReceived(role, content){ conversationPanel.appendMessage(role, content) }
        function onConversationsLoaded(convs)    { sidebar.updateConversations(convs) }
        function onConversationLoaded(messages)  { conversationPanel.loadMessages(messages) }
        function onConversationCreated(id, title){ bridge.loadConversations() }
        function onSystemStatsUpdated(stats)     { topBar.updateStats(stats) }
        function onPluginsLoaded(plugins)        { /* lazy */ }
        function onTimelineEventAdded(event)     { timelinePanel.addEvent(event) }
        function onMemoriesLoaded(memories)      { memoryPanel.updateMemories(memories) }
        function onStatusMessage(msg)            { topBar.setStatus(msg) }
        function onErrorOccurred(err)            { topBar.setStatus("Error: " + err) }
    }

    // ── Root layout ────────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TopBar {
            id: topBar
            Layout.fillWidth:      true
            Layout.preferredHeight: 48
            themeObj: theme
            onToggleSidebar:  root.sidebarOpen  = !root.sidebarOpen
            onToggleTimeline: root.timelineOpen = !root.timelineOpen
            onToggleSettings: root.settingsOpen = !root.settingsOpen
            onToggleMemory:   root.memoryOpen   = !root.memoryOpen
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color:  theme.border
        }

        RowLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            spacing: 0

            // ── Sidebar — 260px ───────────────────────────────────────────
            Sidebar {
                id: sidebar

                // FIXED MN-1: visible uses a dedicated bool, not .running on Behavior
                Layout.preferredWidth: root.sidebarOpen ? 260 : 0
                Layout.fillHeight: true
                clip: true
                visible: root.sidebarOpen || root.sidebarAnimating

                Behavior on Layout.preferredWidth {
                    NumberAnimation {
                        duration: 220
                        easing.type: Easing.OutCubic
                        onRunningChanged: root.sidebarAnimating = running
                    }
                }

                themeObj: theme
                onConversationSelected: (convId) => bridge.loadConversation(convId)
                onNewConversation: bridge.newConversation()
            }

            // Sidebar separator — visible only when sidebar open
            // FIXED MN-2: Use opacity instead of width animation to avoid gap snap
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color:   theme.border
                opacity: root.sidebarOpen ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 220 } }
            }

            // ── Conversation area ─────────────────────────────────────────
            ConversationPanel {
                id: conversationPanel
                Layout.fillWidth:  true
                Layout.fillHeight: true
                themeObj: theme
            }

            // Timeline separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color:   theme.border
                opacity: root.timelineOpen ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 220 } }
            }

            // ── Execution Timeline — 320px when open ──────────────────────
            ExecutionTimeline {
                id: timelinePanel

                Layout.preferredWidth: root.timelineOpen ? 320 : 0
                Layout.fillHeight: true
                clip: true
                visible: root.timelineOpen || root.timelineAnimating

                Behavior on Layout.preferredWidth {
                    NumberAnimation {
                        duration: 220
                        easing.type: Easing.OutCubic
                        onRunningChanged: root.timelineAnimating = running
                    }
                }

                themeObj: theme
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color:  theme.border
        }

        // ── Input bar — 56px ──────────────────────────────────────────────
        CommandInput {
            id: commandInput
            Layout.fillWidth:      true
            Layout.preferredHeight: 56
            themeObj: theme
            onSendMessage:   (text)          => bridge.sendMessage(text)
            onExecutePlugin: (name, payload) => bridge.executePlugin(name, payload)
        }
    }

    // ── Overlays (anchored directly to Window) ─────────────────────────────
    SettingsPanel {
        id: settingsPanel
        anchors.right:  parent.right
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        width: 360
        visible: root.settingsOpen
        themeObj: theme
        onClose: root.settingsOpen = false
    }

    MemoryPanel {
        id: memoryPanel
        anchors.right:  root.settingsOpen ? settingsPanel.left : parent.right
        anchors.top:    parent.top
        anchors.bottom: parent.bottom
        width: 320
        visible: root.memoryOpen
        themeObj: theme
        onClose: root.memoryOpen = false
    }

    Component.onCompleted: {
        bridge.loadConversations()
    }
}
