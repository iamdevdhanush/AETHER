import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQml 2.15

Rectangle {
    id: root
    color: themeObj.bgPanel
    clip: true

    required property var themeObj

    signal conversationSelected(string convId)
    signal newConversation()

    property var    conversations: []
    property string activeConversationId: ""
    property string sortMode: "newest"   // newest | oldest | alphabetical | recent
    property string searchQuery: ""
    property bool   isSearching: false

    // ── Public API called from Main.qml bridge connections ───────────────

    function updateConversations(convs) {
        conversations = convs
        if (searchQuery.length > 0 && isSearching) {
            bridge.searchConversations(searchQuery)
            return
        }
        _populateModel(convs, sortMode)
    }

    function updateConversationTitle(convId, newTitle) {
        for (var i = 0; i < conversationModel.count; i++) {
            if (conversationModel.get(i).id === convId) {
                conversationModel.setProperty(i, "title", newTitle)
                break
            }
        }
    }

    function showSearchResults(results) {
        isSearching = true
        _populateModel(results, sortMode)
    }

    function clearSearch() {
        searchQuery = ""
        isSearching = false
        searchInput.text = ""
        searchInput.focus = false
        _populateModel(conversations, sortMode)
    }

    // ── Model population ─────────────────────────────────────────────────

    function _populateModel(items, sort) {
        conversationModel.clear()
        if (!items || items.length === 0) return

        var sorted = _sortItems(items, sort)
        for (var i = 0; i < sorted.length; i++) {
            var item = sorted[i]
            var group = _dateGroup(item.updated_at || item.created_at)
            conversationModel.append({
                "id": item.id,
                "title": item.title || "New Conversation",
                "created_at": item.created_at || "",
                "updated_at": item.updated_at || item.created_at || "",
                "last_message": item.last_message || "",
                "message_count": item.message_count || 0,
                "pinned": item.pinned || 0,
                "group": group,
            })
        }
    }

    function _sortItems(items, sort) {
        var arr = items.slice()
        switch (sort) {
            case "oldest":
                arr.sort(function(a, b) {
                    return (a.created_at || "").localeCompare(b.created_at || "")
                })
                break
            case "alphabetical":
                arr.sort(function(a, b) {
                    return (a.title || "").localeCompare(b.title || "")
                })
                break
            case "recent":
                arr.sort(function(a, b) {
                    return (b.updated_at || "").localeCompare(a.updated_at || "")
                })
                break
            default: // newest
                arr.sort(function(a, b) {
                    return (b.updated_at || "").localeCompare(a.updated_at || "")
                })
        }
        return arr
    }

    function _dateGroup(dateStr) {
        if (!dateStr) return "older"
        var d = new Date(dateStr)
        if (isNaN(d.getTime())) return "older"

        var now = new Date()
        var today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        var target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
        var diffDays = Math.round((today - target) / (1000 * 60 * 60 * 24))

        if (diffDays === 0) return "today"
        if (diffDays === 1) return "yesterday"
        if (diffDays <= 7) return "last7"
        if (diffDays <= 30) return "last30"
        return "older"
    }

    function _groupLabel(group) {
        switch (group) {
            case "today":      return "Today"
            case "yesterday":  return "Yesterday"
            case "last7":      return "Last 7 Days"
            case "last30":     return "Last Month"
            default:           return "Older"
        }
    }

    function _formatTimestamp(dateStr) {
        if (!dateStr) return ""
        var d = new Date(dateStr)
        if (isNaN(d.getTime())) return ""
        var now = new Date()
        var diff = now - d
        var mins = Math.floor(diff / 60000)
        if (mins < 1) return "now"
        if (mins < 60) return mins + "m"
        var hours = Math.floor(mins / 60)
        if (hours < 24) return hours + "h"
        var days = Math.floor(hours / 24)
        if (days < 7) return days + "d"
        return d.toLocaleDateString()
    }

    function _previewText(text) {
        if (!text) return "No messages"
        var clean = text.replace(/\n/g, " ").trim()
        return clean.length > 80 ? clean.substring(0, 77) + "..." : clean
    }

    // ── Inline rename state ──────────────────────────────────────────────

    property string renamingId: ""
    property string renameBuffer: ""

    function startRename(convId, currentTitle) {
        renamingId = convId
        renameBuffer = currentTitle
    }

    function confirmRename() {
        if (renamingId && renameBuffer.trim().length > 0) {
            bridge.renameConversation(renamingId, renameBuffer.trim())
        }
        renamingId = ""
        renameBuffer = ""
    }

    function cancelRename() {
        renamingId = ""
        renameBuffer = ""
    }

    // ── Context / three-dot menu state ───────────────────────────────────

    property string menuTargetId: ""
    property string menuTargetTitle: ""

    // ── UI ───────────────────────────────────────────────────────────────

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Header ───────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            Layout.leftMargin:  16
            Layout.rightMargin: 8
            spacing: 4

            Text {
                text: "Chats"
                color: root.themeObj.textMuted
                font.pixelSize: 11
                font.letterSpacing: 1.2
                font.weight: Font.Medium
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
            }

            // Sort mode indicator
            Rectangle {
                id: sortBtn
                implicitWidth: 28
                implicitHeight: 28
                radius: 6
                color: sortHover.containsMouse ? root.themeObj.bgHover : "transparent"
                visible: conversationModel.count > 0
                Behavior on color { ColorAnimation { duration: 120 } }

                Text {
                    anchors.centerIn: parent
                    text: {
                        switch (root.sortMode) {
                            case "oldest":       return "↑"
                            case "alphabetical": return "A"
                            case "recent":       return "◷"
                            default:             return "↓"
                        }
                    }
                    font.pixelSize: 13
                    color: root.themeObj.textSec
                }

                ToolTip.visible: sortHover.containsMouse
                ToolTip.text: "Sort: " + {
                    "newest": "Newest First",
                    "oldest": "Oldest First",
                    "alphabetical": "Alphabetical",
                    "recent": "Last Active",
                }[root.sortMode]
                ToolTip.delay: 500

                MouseArea {
                    id: sortHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var modes = ["newest", "oldest", "alphabetical", "recent"]
                        var idx = modes.indexOf(root.sortMode)
                        root.sortMode = modes[(idx + 1) % modes.length]
                        _populateModel(isSearching ? [] : conversations, root.sortMode)
                        if (isSearching && searchQuery.length > 0)
                            bridge.searchConversations(searchQuery)
                    }
                }
            }

            // New conversation button
            Rectangle {
                id: newBtn2
                implicitWidth:  32
                implicitHeight: 32
                radius: root.themeObj.radiusSm
                color: newBtnArea2.containsMouse
                    ? root.themeObj.bgHover
                    : "transparent"
                Layout.alignment: Qt.AlignVCenter
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "✚"
                    font.pixelSize: 15
                    color: newBtnArea2.containsMouse
                        ? root.themeObj.accentGlow
                        : root.themeObj.accent
                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                ToolTip.visible: newBtnArea2.containsMouse
                ToolTip.text:   "New Conversation"
                ToolTip.delay:  500

                MouseArea {
                    id: newBtnArea2
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.newConversation()
                        root.activeConversationId = ""
                        clearSearch()
                    }
                }
            }
        }

        // ── Search bar ───────────────────────────────────────────────
        Rectangle {
            id: searchContainer
            Layout.fillWidth: true
            Layout.leftMargin:  12
            Layout.rightMargin: 12
            Layout.preferredHeight: 34
            color: root.themeObj.bgCard
            radius: 8
            border.width: searchInput.activeFocus ? 1 : 0
            border.color: searchInput.activeFocus ? root.themeObj.accent : "transparent"
            Behavior on border.color { ColorAnimation { duration: 120 } }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin:  10
                anchors.rightMargin: 8
                spacing: 6

                Text {
                    text: "⌕"
                    font.pixelSize: 14
                    color: root.themeObj.textMuted
                }

                TextInput {
                    id: searchInput
                    Layout.fillWidth: true
                    color: root.themeObj.textPrimary
                    font.pixelSize: 12
                    font.family: "Segoe UI, system-ui, sans-serif"
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true

                    property string placeholder: "Search conversations..."

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: searchInput.placeholder
                        color: root.themeObj.textMuted
                        font.pixelSize: 12
                        visible: !searchInput.text.length
                        opacity: 0.6
                    }

                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Escape) {
                            if (searchInput.text.length > 0) {
                                clearSearch()
                            }
                            searchInput.focus = false
                            event.accepted = true
                        }
                    }

                    onTextChanged: {
                        root.searchQuery = text
                        if (text.length > 0) {
                            bridge.searchConversations(text)
                        } else {
                            root.isSearching = false
                            _populateModel(conversations, root.sortMode)
                        }
                    }
                }

                // Clear search
                Rectangle {
                    implicitWidth:  18
                    implicitHeight: 18
                    radius: 9
                    color: clearSearchHover.containsMouse
                        ? root.themeObj.textMuted : "transparent"
                    visible: searchInput.text.length > 0
                    Behavior on color { ColorAnimation { duration: 120 } }

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        font.pixelSize: 9
                        color: clearSearchHover.containsMouse
                            ? root.themeObj.textPrimary : root.themeObj.textMuted
                    }

                    MouseArea {
                        id: clearSearchHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: clearSearch()
                    }
                }
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
            Layout.topMargin: 8
        }

        // ── Conversation list ────────────────────────────────────────
        ListView {
            id: convList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            reuseItems: true
            model: ListModel { id: conversationModel }
            spacing: 1
            topMargin:    6
            bottomMargin: 8
            leftMargin:   8
            rightMargin:  8

            // Section / date grouping
            section.property: "group"
            section.delegate: Item {
                width: convList.width - convList.leftMargin - convList.rightMargin
                height: 28

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    text: _groupLabel(section)
                    color: root.themeObj.textMuted
                    font.pixelSize: 10
                    font.letterSpacing: 0.8
                    font.weight: Font.Medium
                    opacity: 0.7
                }
            }

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    color: root.themeObj.borderBright
                    radius: 2
                    implicitWidth: 3
                    opacity: 0.5
                }
                background: Rectangle { color: "transparent" }
            }

            delegate: Item {
                id: convDelegate
                width:  convList.width - convList.leftMargin - convList.rightMargin
                height: 52

                readonly property string convId: model.id
                readonly property string convTitle: model.title
                readonly property bool   isActive: model.id === root.activeConversationId
                readonly property bool   isRenaming: root.renamingId === model.id

                // ── Background ───────────────────────────────────────
                Rectangle {
                    id: bgRect
                    anchors.fill: parent
                    radius: 12
                    color: convDelegate.isActive
                        ? root.themeObj.bgSelected
                        : (hoverArea.containsMouse || threeDotHover.containsMouse || menuTargetId === model.id
                           ? root.themeObj.bgHover : "transparent")
                    Behavior on color { ColorAnimation { duration: 120 } }

                    border.width: convDelegate.isActive ? 1 : 0
                    border.color: convDelegate.isActive
                        ? root.themeObj.accent + "50" : "transparent"
                    Behavior on border.color { ColorAnimation { duration: 180 } }
                }

                // ── Active accent bar ────────────────────────────────
                Rectangle {
                    anchors.left:          parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width:   3
                    height:  20
                    radius:  2
                    color:   root.themeObj.accent
                    opacity: convDelegate.isActive ? 1.0 : 0.0
                    Behavior on opacity { NumberAnimation { duration: 180 } }
                }

                // ── Inline rename field ──────────────────────────────
                TextField {
                    id: renameField
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    anchors.right: parent.right
                    anchors.rightMargin: 40
                    anchors.verticalCenter: parent.verticalCenter
                    visible: convDelegate.isRenaming
                    height: 28
                    color: root.themeObj.textPrimary
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    font.family: "Segoe UI, system-ui, sans-serif"
                    background: Rectangle {
                        color: root.themeObj.bgCard
                        radius: 6
                        border.width: 1
                        border.color: root.themeObj.accent
                    }
                    text: root.renameBuffer
                    verticalAlignment: TextInput.AlignVCenter
                    leftPadding: 8
                    rightPadding: 8

                    onVisibleChanged: {
                        if (visible) {
                            forceActiveFocus()
                            selectAll()
                        }
                    }

                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            root.confirmRename()
                            event.accepted = true
                        } else if (event.key === Qt.Key_Escape) {
                            root.cancelRename()
                            event.accepted = true
                        }
                    }

                    onEditingFinished: {
                        root.confirmRename()
                    }
                }

                // ── Title + preview (hidden during rename) ───────────
                ColumnLayout {
                    anchors.left:         parent.left
                    anchors.right:        parent.right
                    anchors.rightMargin:  36
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin:   16
                    spacing: 1
                    visible: !convDelegate.isRenaming

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: model.title || "New Conversation"
                            color: convDelegate.isActive
                                ? root.themeObj.textPrimary
                                : root.themeObj.textSec
                            font.pixelSize: 13
                            font.weight: convDelegate.isActive ? Font.DemiBold : Font.Medium
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            Behavior on color { ColorAnimation { duration: 120 } }
                        }

                        Text {
                            text: _formatTimestamp(model.updated_at)
                            color: root.themeObj.textMuted
                            font.pixelSize: 10
                            opacity: 0.6
                            visible: !searchInput.text.length
                        }
                    }

                    Text {
                        text: _previewText(model.last_message)
                        color: root.themeObj.textMuted
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        opacity: 0.5
                        visible: !searchInput.text.length
                    }
                }

                // ── Three-dot menu button (visible on hover) ─────────
                Rectangle {
                    id: threeDotBtn
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    width:  24
                    height: 24
                    radius: 6
                    color: threeDotHover.containsMouse || threeDotPopup.opened
                        ? root.themeObj.bgHover : "transparent"
                    visible: (hoverArea.containsMouse || threeDotPopup.opened
                              || menuTargetId === model.id)
                             && !convDelegate.isRenaming
                    Behavior on color { ColorAnimation { duration: 120 } }

                    Text {
                        anchors.centerIn: parent
                        text: "⋮"
                        font.pixelSize: 14
                        font.weight: Font.Bold
                        color: root.themeObj.textSec
                    }

                    MouseArea {
                        id: threeDotHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.menuTargetId = model.id
                            root.menuTargetTitle = model.title || "Conversation"
                            threeDotPopup.open()
                        }
                    }
                }

                // ── Three-dot popup menu ─────────────────────────────
                Popup {
                    id: threeDotPopup
                    y: -threeDotPopup.implicitHeight - 4
                    x: parent.width - threeDotPopup.implicitWidth
                    width: 180
                    padding: 4
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    background: Rectangle {
                        color: root.themeObj.bgCard
                        radius: 10
                        border.width: 1
                        border.color: root.themeObj.border
                    }

                    contentItem: ColumnLayout {
                        spacing: 2

                        Repeater {
                            model: [
                                { icon: "✎", text: "Rename",         action: "rename" },
                                { icon: "⧉", text: "Duplicate",       action: "duplicate" },
                                { icon: "",  text: "",                 action: "separator" },
                                { icon: "📄", text: "Export Markdown", action: "export_md" },
                                { icon: "📋", text: "Export JSON",     action: "export_json" },
                                { icon: "",  text: "",                 action: "separator" },
                                { icon: "🗑", text: "Delete",          action: "delete" },
                            ]

                            delegate: Item {
                                Layout.fillWidth: true
                                Layout.preferredHeight: item.action === "separator" ? 8 : 30
                                visible: !(item.action === "separator" && index === 2)

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 6
                                    visible: !(item.action === "separator")
                                    color: menuItemHover.containsMouse
                                        ? (item.action === "delete"
                                           ? "#FF4D5E20" : root.themeObj.bgHover)
                                        : "transparent"
                                    Behavior on color { ColorAnimation { duration: 80 } }

                                    RowLayout {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        visible: item.action !== "separator"

                                        Text {
                                            text: item.icon
                                            font.pixelSize: 13
                                            color: item.action === "delete"
                                                ? root.themeObj.error : root.themeObj.textSec
                                        }

                                        Text {
                                            text: item.text
                                            color: item.action === "delete"
                                                ? root.themeObj.error : root.themeObj.textPrimary
                                            font.pixelSize: 12
                                        }
                                    }

                                    MouseArea {
                                        id: menuItemHover
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            threeDotPopup.close()
                                            _handleMenuAction(item.action,
                                                root.menuTargetId, root.menuTargetTitle)
                                        }
                                    }
                                }

                                // Separator line
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 8
                                    anchors.right: parent.right
                                    anchors.rightMargin: 8
                                    height: 1
                                    color: root.themeObj.border
                                    visible: item.action === "separator"
                                    opacity: 0.5
                                }
                            }
                        }
                    }
                }

                // ── Right-click context menu ─────────────────────────
                Popup {
                    id: contextPopup
                    x: contextMenuMouse.mouseX
                    y: contextMenuMouse.mouseY - height - 10
                    width: 190
                    padding: 4
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    background: Rectangle {
                        color: root.themeObj.bgCard
                        radius: 10
                        border.width: 1
                        border.color: root.themeObj.border
                    }

                    contentItem: ColumnLayout {
                        spacing: 2

                        Repeater {
                            model: [
                                { icon: "✎", text: "Rename",         action: "rename" },
                                { icon: "⧉", text: "Duplicate",       action: "duplicate" },
                                { icon: "",  text: "",                 action: "separator" },
                                { icon: "📄", text: "Export Markdown", action: "export_md" },
                                { icon: "📋", text: "Export JSON",     action: "export_json" },
                                { icon: "",  text: "",                 action: "separator" },
                                { icon: "🗑", text: "Delete",          action: "delete" },
                            ]

                            delegate: Item {
                                Layout.fillWidth: true
                                Layout.preferredHeight: item.action === "separator" ? 8 : 30

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 6
                                    visible: !(item.action === "separator")
                                    color: ctxItemHover.containsMouse
                                        ? (item.action === "delete"
                                           ? "#FF4D5E20" : root.themeObj.bgHover)
                                        : "transparent"
                                    Behavior on color { ColorAnimation { duration: 80 } }

                                    RowLayout {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        visible: item.action !== "separator"

                                        Text {
                                            text: item.icon
                                            font.pixelSize: 13
                                            color: item.action === "delete"
                                                ? root.themeObj.error : root.themeObj.textSec
                                        }

                                        Text {
                                            text: item.text
                                            color: item.action === "delete"
                                                ? root.themeObj.error : root.themeObj.textPrimary
                                            font.pixelSize: 12
                                        }
                                    }

                                    MouseArea {
                                        id: ctxItemHover
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            contextPopup.close()
                                            _handleMenuAction(item.action,
                                                model.id, model.title)
                                        }
                                    }
                                }

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 8
                                    anchors.right: parent.right
                                    anchors.rightMargin: 8
                                    height: 1
                                    color: root.themeObj.border
                                    visible: item.action === "separator"
                                    opacity: 0.5
                                }
                            }
                        }
                    }
                }

                // ── MouseArea for click, hover, right-click ──────────
                MouseArea {
                    id: hoverArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.LeftButton | Qt.RightButton

                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            root.menuTargetId = model.id
                            root.menuTargetTitle = model.title || "Conversation"
                            contextMenuMouse.mouseX = mouse.x
                            contextMenuMouse.mouseY = mouse.y
                            contextPopup.open()
                            return
                        }
                        if (convDelegate.isRenaming) return
                        root.activeConversationId = model.id
                        root.conversationSelected(model.id)
                    }

                    onDoubleClicked: {
                        if (!convDelegate.isRenaming) {
                            root.startRename(model.id, model.title || "Conversation")
                        }
                    }
                }
            }
        }

        // ── Empty state ─────────────────────────────────────────────
        Item {
            anchors.fill: parent
            visible: conversationModel.count === 0
            z: -1

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 16
                width: Math.min(200, parent.width - 32)

                // Large illustration
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 80

                    Rectangle {
                        anchors.centerIn: parent
                        width: 72; height: 72
                        radius: 36
                        color: root.themeObj.accent + "14"
                        border.color: root.themeObj.accent + "30"
                        border.width: 1
                    }

                    Text {
                        anchors.centerIn: parent
                        text: "⬡"
                        font.pixelSize: 32
                        color: root.themeObj.accent
                        opacity: 0.8
                    }
                }

                Text {
                    text: isSearching ? "No results found"
                                      : "Start your first conversation"
                    color: root.themeObj.textSec
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    text: isSearching ? "Try a different search term"
                                      : "Type a message or tap the button below"
                    color: root.themeObj.textMuted
                    font.pixelSize: 11
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.6
                }

                // New Chat button (only when not searching)
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    implicitWidth: 140
                    implicitHeight: 36
                    radius: 18
                    visible: !isSearching
                    color: emptyNewBtn.containsMouse
                        ? root.themeObj.accentGlow : root.themeObj.accent
                    Behavior on color { ColorAnimation { duration: 120 } }

                    Text {
                        anchors.centerIn: parent
                        text: "✚  New Chat"
                        color: "white"
                        font.pixelSize: 13
                        font.weight: Font.Medium
                    }

                    MouseArea {
                        id: emptyNewBtn
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.newConversation()
                            root.activeConversationId = ""
                        }
                    }
                }
            }
        }

        // ── Bottom separator ────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.themeObj.border
        }

        // ── Version footer ──────────────────────────────────────────
        Text {
            Layout.leftMargin:   16
            Layout.topMargin:    8
            Layout.bottomMargin: 8
            text: "AETHER v1.0.0"
            color: root.themeObj.textMuted
            font.pixelSize: 10
            opacity: 0.4
        }
    }

    // ── Helper to process menu actions ──────────────────────────────
    function _handleMenuAction(action, convId, convTitle) {
        switch (action) {
            case "rename":
                startRename(convId, convTitle)
                break
            case "duplicate":
                bridge.duplicateConversation(convId)
                break
            case "export_md":
                bridge.exportConversationMarkdown(convId)
                break
            case "export_json":
                bridge.exportConversationJSON(convId)
                break
            case "delete":
                _confirmDelete(convId)
                break
        }
    }

    // ── Delete confirmation dialog ──────────────────────────────────
    property bool deleteDialogOpen: false
    property string deleteTargetId: ""

    function _confirmDelete(convId) {
        deleteTargetId = convId
        deleteDialogOpen = true
    }

    // Delete confirmation overlay
    Rectangle {
        id: deleteOverlay
        anchors.fill: parent
        color: "#00000000"
        visible: deleteDialogOpen

        MouseArea {
            anchors.fill: parent
            onClicked: deleteDialogOpen = false
        }

        Rectangle {
            anchors.centerIn: parent
            width: parent.width - 32
            height: deleteDialog.implicitHeight + 32
            color: root.themeObj.bgCard
            radius: 14
            border.width: 1
            border.color: root.themeObj.border

            ColumnLayout {
                id: deleteDialog
                anchors.centerIn: parent
                width: parent.width - 32
                spacing: 16

                Text {
                    text: "Delete this conversation?"
                    color: root.themeObj.textPrimary
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Messages, timeline events, and memory references\nwill be permanently removed."
                    color: root.themeObj.textMuted
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                    lineHeight: 1.4
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: 8
                        color: cancelDelBtn.containsMouse
                            ? root.themeObj.bgHover : "transparent"
                        border.width: 1
                        border.color: root.themeObj.border
                        Behavior on color { ColorAnimation { duration: 120 } }

                        Text {
                            anchors.centerIn: parent
                            text: "Cancel"
                            color: root.themeObj.textSec
                            font.pixelSize: 12
                        }

                        MouseArea {
                            id: cancelDelBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: deleteDialogOpen = false
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: 8
                        color: confirmDelBtn.containsMouse
                            ? "#FF4D5E" : root.themeObj.error
                        Behavior on color { ColorAnimation { duration: 120 } }

                        Text {
                            anchors.centerIn: parent
                            text: "Delete"
                            color: "white"
                            font.pixelSize: 12
                            font.weight: Font.Medium
                        }

                        MouseArea {
                            id: confirmDelBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                bridge.deleteConversation(deleteTargetId)
                                deleteDialogOpen = false
                                deleteTargetId = ""
                                if (deleteTargetId === root.activeConversationId) {
                                    root.activeConversationId = ""
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Invisible helper to capture right-click position
    Item {
        id: contextMenuMouse
        property int mouseX: 0
        property int mouseY: 0
    }
}
