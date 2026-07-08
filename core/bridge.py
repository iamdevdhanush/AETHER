"""
AETHER QML Bridge v2
All QML ↔ Python communication flows through this object.
Exposed to QML as `bridge`.

Routes through the new Agent Runtime:
  Intent → Tool/Plan → Reasoning Loop → Tool Execution → Observation → Reflection
"""

import logging
import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread

logger = logging.getLogger(__name__)


class AsyncWorker(QThread):
    """Runs a coroutine in a dedicated thread and emits result."""
    result = Signal(object)
    error = Signal(str)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro

    def run(self):
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro)
            self.result.emit(result)
        except Exception as e:
            logger.exception("AsyncWorker error")
            self.error.emit(str(e))
        finally:
            if loop is not None and not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    try:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    except Exception:
                        pass
                loop.close()


class QMLBridge(QObject):

    # ── Conversation signals ──────────────────────────────────────────────
    messageReceived = Signal(str, str)        # role, content
    streamChunk = Signal(str)                 # streaming token
    streamComplete = Signal()
    streamError = Signal(str)

    # ── Conversation list signals ─────────────────────────────────────────
    conversationsLoaded = Signal("QVariantList")
    conversationLoaded = Signal("QVariantList")
    conversationCreated = Signal(str, str)    # id, title

    # ── Conversation management signals ───────────────────────────────────
    conversationRenamed = Signal(str, str)    # id, new_title
    conversationDeleted = Signal(str)         # id
    conversationDuplicated = Signal(str, str) # new_id, title
    conversationMarkdownExported = Signal(str) # file_path
    conversationJSONExported = Signal(str)    # file_path
    conversationTitleGenerated = Signal(str, str) # id, title
    conversationSearchResults = Signal("QVariantList")

    # ── Plugin signals ────────────────────────────────────────────────────
    pluginResult = Signal(str, str)           # plugin_name, result
    pluginError = Signal(str, str)
    pluginsLoaded = Signal("QVariantList")

    # ── System monitor signals ────────────────────────────────────────────
    systemStatsUpdated = Signal("QVariantMap")

    # ── Memory signals ────────────────────────────────────────────────────
    memoriesLoaded = Signal("QVariantList")
    memoryAdded = Signal(str)

    # ── Execution timeline ────────────────────────────────────────────────
    timelineEventAdded = Signal("QVariantMap")

    # ── Agent reasoning signals ───────────────────────────────────────────
    reasoningStateChanged = Signal("QVariantMap")
    planCreated = Signal("QVariantMap")
    observationReady = Signal("QVariantMap")

    # ── General ──────────────────────────────────────────────────────────
    errorOccurred = Signal(str)
    statusMessage = Signal(str)

    def __init__(self, db, ollama, plugin_manager, conversation_service,
                 memory_service, system_monitor, project_root: Path,
                 agent_runtime=None):
        super().__init__()
        self.db = db
        self.ollama = ollama
        self.plugin_manager = plugin_manager
        self.conversation_service = conversation_service
        self.memory_service = memory_service
        self.system_monitor = system_monitor
        self.project_root = project_root
        self.agent_runtime = agent_runtime

        self._current_conversation_id: Optional[str] = None
        self._active_workers = []

        self.system_monitor.stats_ready.connect(self._on_system_stats)

        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(5000)
        self._stats_timer.timeout.connect(self.system_monitor.update)
        self._stats_timer.start()

    # ── Conversation ──────────────────────────────────────────────────────

    @Slot(str)
    def sendMessage(self, text: str):
        if not text.strip():
            return
        text = text.strip()
        logger.info("sendMessage: %s", text[:120])

        self._emit_timeline("user_message", f"User: {text[:80]}")

        worker = AsyncWorker(self._async_send_message(text))
        worker.error.connect(lambda e: self.streamError.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    async def _async_send_message(self, text: str):
        self._current_conversation_id = await self._ensure_conversation(text)
        if not self._current_conversation_id:
            return

        self.messageReceived.emit("user", text)

        await self.conversation_service.add_message(
            conversation_id=self._current_conversation_id,
            role="user", content=text,
        )

        if self.agent_runtime:
            try:
                result = await self.agent_runtime.process(text)
            except Exception as e:
                logger.exception("Agent runtime error")
                self.streamError.emit(str(e))
                return

            if result is not None:
                self.messageReceived.emit("assistant", result)
                self.streamComplete.emit()
                await self.conversation_service.add_message(
                    conversation_id=self._current_conversation_id,
                    role="assistant", content=result,
                )
                if self.memory_service:
                    await self.memory_service.extract_and_store(text, result)
                return

        await self._stream_chat(text)

    async def _ensure_conversation(self, text: str) -> Optional[str]:
        if not self._current_conversation_id:
            conv = await self.conversation_service.create_conversation(
                title=text[:50],
            )
            self._current_conversation_id = conv["id"]
            self.conversationCreated.emit(conv["id"], conv["title"])
        return self._current_conversation_id

    async def _stream_chat(self, text: str):
        history = await self.conversation_service.get_context_window(
            self._current_conversation_id, max_messages=20,
        )

        full_response = ""
        chunk_count = 0
        try:
            async for chunk in self.ollama.stream_chat(messages=history):
                chunk_count += 1
                self.streamChunk.emit(chunk)
                full_response += chunk
        except Exception as e:
            logger.error("Stream error: %s", e)
            self.streamError.emit(str(e))
            return

        self.streamComplete.emit()

        await self.conversation_service.add_message(
            conversation_id=self._current_conversation_id,
            role="assistant", content=full_response,
        )

        if self.memory_service:
            await self.memory_service.extract_and_store(text, full_response)
            await self.memory_service.summarize_and_store(
                self._current_conversation_id,
                [{"role": "user", "content": text},
                 {"role": "assistant", "content": full_response}],
            )

        self._emit_timeline("ai_response", f"AI responded ({len(full_response)} chars)")

    @Slot()
    def loadConversations(self):
        worker = AsyncWorker(self._async_load_conversations())
        worker.result.connect(lambda r: self.conversationsLoaded.emit(r))
        worker.error.connect(lambda e: self.errorOccurred.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    async def _async_load_conversations(self):
        return await self.conversation_service.list_conversations()

    @Slot(str)
    def loadConversation(self, conversation_id: str):
        self._current_conversation_id = conversation_id
        worker = AsyncWorker(self._async_load_conversation(conversation_id))
        worker.result.connect(lambda r: self.conversationLoaded.emit(r))
        worker.error.connect(lambda e: self.errorOccurred.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    async def _async_load_conversation(self, conversation_id: str):
        return await self.conversation_service.get_messages(conversation_id)

    @Slot()
    def newConversation(self):
        self._current_conversation_id = None
        self.conversationLoaded.emit([])

    @Slot(str)
    def deleteConversation(self, conversation_id: str):
        """Cascade delete conversation + messages + timeline + memory refs."""
        worker = AsyncWorker(
            self.conversation_service.delete_conversation(conversation_id)
        )
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.finished.connect(lambda: self.conversationDeleted.emit(conversation_id))
        worker.finished.connect(self.loadConversations)
        if conversation_id == self._current_conversation_id:
            self._current_conversation_id = None
        self._active_workers.append(worker)
        worker.start()

    @Slot(str, str)
    def renameConversation(self, conversation_id: str, new_title: str):
        worker = AsyncWorker(
            self.conversation_service.rename_conversation(conversation_id, new_title)
        )
        def _on_rename_result(ok: bool):
            if ok:
                self.conversationRenamed.emit(conversation_id, new_title)
                self.loadConversations()
        worker.result.connect(_on_rename_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def duplicateConversation(self, conversation_id: str):
        worker = AsyncWorker(
            self.conversation_service.duplicate_conversation(conversation_id)
        )
        def _on_duplicate_result(new_conv):
            if new_conv:
                self.conversationDuplicated.emit(new_conv["id"], new_conv["title"])
                self.loadConversations()
        worker.result.connect(_on_duplicate_result)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def exportConversationMarkdown(self, conversation_id: str):
        worker = AsyncWorker(
            self.conversation_service.export_conversation_markdown(conversation_id)
        )
        def _save(result):
            try:
                conv = self.db.get_conversation(conversation_id)
                safe_title = conv["title"] if conv else "conversation"
                safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in safe_title)
                path = self.project_root / "exports"
                path.mkdir(exist_ok=True)
                filepath = path / f"{safe_title}_{conversation_id[:8]}.md"
                filepath.write_text(result, encoding="utf-8")
                self.conversationMarkdownExported.emit(str(filepath))
                self.statusMessage.emit(f"Exported: {filepath.name}")
            except Exception as e:
                self.errorOccurred.emit(f"Export failed: {e}")
            self._cleanup_worker(worker)
        worker.result.connect(_save)
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def exportConversationJSON(self, conversation_id: str):
        worker = AsyncWorker(
            self.conversation_service.export_conversation_json(conversation_id)
        )
        def _save(result):
            try:
                conv = self.db.get_conversation(conversation_id)
                safe_title = conv["title"] if conv else "conversation"
                safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in safe_title)
                path = self.project_root / "exports"
                path.mkdir(exist_ok=True)
                filepath = path / f"{safe_title}_{conversation_id[:8]}.json"
                filepath.write_text(result, encoding="utf-8")
                self.conversationJSONExported.emit(str(filepath))
                self.statusMessage.emit(f"Exported: {filepath.name}")
            except Exception as e:
                self.errorOccurred.emit(f"Export failed: {e}")
            self._cleanup_worker(worker)
        worker.result.connect(_save)
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def searchConversations(self, query: str):
        worker = AsyncWorker(
            self.conversation_service.search_conversations(query)
        )
        worker.result.connect(lambda r: self.conversationSearchResults.emit(r))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    # ── Plugins ───────────────────────────────────────────────────────────

    @Slot()
    def loadPlugins(self):
        plugins = self.plugin_manager.get_plugin_list()
        self.pluginsLoaded.emit(plugins)

    @Slot(str, str)
    def executePlugin(self, plugin_name: str, payload: str):
        self._emit_timeline("plugin_execute", f"Plugin: {plugin_name}")
        worker = AsyncWorker(self._async_execute_plugin(plugin_name, payload))
        worker.result.connect(
            lambda r: self.pluginResult.emit(plugin_name, str(r))
        )
        worker.error.connect(
            lambda e: self.pluginError.emit(plugin_name, e)
        )
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    async def _async_execute_plugin(self, plugin_name: str, payload: str):
        tool = self.plugin_manager.get_plugin(plugin_name)
        if not tool:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        obs = await tool.execute({"input": payload})
        return obs.stdout[:500]

    # ── Memory ────────────────────────────────────────────────────────────

    @Slot()
    def loadMemories(self):
        worker = AsyncWorker(self.memory_service.get_all_memories())
        worker.result.connect(lambda r: self.memoriesLoaded.emit(r))
        worker.error.connect(lambda e: self.errorOccurred.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def deleteMemory(self, memory_id: str):
        worker = AsyncWorker(self.memory_service.delete_memory(memory_id))
        worker.finished.connect(self.loadMemories)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    # ── System Monitor ────────────────────────────────────────────────────

    def _on_system_stats(self, stats: dict):
        self.systemStatsUpdated.emit(stats)

    # ── Ollama Model Management ───────────────────────────────────────────

    @Slot()
    def loadModels(self):
        worker = AsyncWorker(self.ollama.list_models())
        worker.result.connect(lambda r: self.statusMessage.emit(f"Models: {r}"))
        worker.error.connect(lambda e: self.errorOccurred.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    @Slot(str)
    def setModel(self, model_name: str):
        self.ollama.set_model(model_name)
        self.statusMessage.emit(f"Model set to {model_name}")

    # ── Agent Runtime Integration ─────────────────────────────────────────

    def on_reasoning_state(self, state):
        """Called by AgentRuntime on each reasoning step."""
        self.reasoningStateChanged.emit({
            "thought": state.thought,
            "tool": state.selected_tool or "",
            "parameters": json.dumps(state.parameters),
            "reflection": state.reflection,
            "is_complete": state.is_complete,
        })

    def on_plan_created(self, plan):
        self.planCreated.emit({
            "goal": plan.goal,
            "steps": [s.__dict__ for s in plan.steps],
        })

    def on_observation(self, observation: dict):
        self.observationReady.emit({
            "tool": observation.get("tool", ""),
            "stdout": observation.get("stdout", "")[:500],
            "stderr": observation.get("stderr", "")[:200],
            "exit_code": observation.get("exit_code", 0),
            "execution_time_ms": observation.get("execution_time_ms", 0),
            "success": observation.get("success", False),
        })

    # ── Utilities ─────────────────────────────────────────────────────────

    def _emit_timeline(self, event_type: str, description: str,
                        metadata: dict = None):
        ev = {
            "type": event_type,
            "description": description,
            "timestamp": int(time.time() * 1000),
        }
        if metadata:
            ev["metadata"] = metadata
        self.timelineEventAdded.emit(ev)

    @Slot(result=str)
    def currentConversationId(self) -> str:
        return self._current_conversation_id or ""

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    def cleanup(self):
        self._stats_timer.stop()
        for worker in list(self._active_workers):
            if worker.isRunning():
                worker.quit()
                if not worker.wait(3000):
                    worker.terminate()
                    worker.wait()
        self._active_workers.clear()

    @Slot(result=str)
    def currentModel(self) -> str:
        return self.ollama.current_model
