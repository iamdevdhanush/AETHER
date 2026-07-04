"""
AETHER QML Bridge
All QML ↔ Python communication flows through this object.
Exposed to QML as `bridge`.

Every user message routes through the Agent Runtime:
  Intent → Selected Tool → Executing → Result
"""

import logging
import asyncio
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QThread

logger = logging.getLogger(__name__)


class AsyncWorker(QThread):
    """Runs a coroutine and emits result."""
    result = Signal(object)
    error = Signal(str)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def run(self):
        loop = None
        try:
            loop = asyncio.new_event_loop()
            self._loop = loop
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
            self._loop = None


class QMLBridge(QObject):
    """
    Central bridge between QML UI and Python backend.
    Routes through AgentRuntime for intent→tool→result flow.
    """

    # ── Conversation signals ──────────────────────────────────────────────
    messageReceived = Signal(str, str)        # role, content
    streamChunk = Signal(str)                 # streaming token
    streamComplete = Signal()
    streamError = Signal(str)

    # ── Conversation list signals ─────────────────────────────────────────
    conversationsLoaded = Signal("QVariantList")
    conversationLoaded = Signal("QVariantList")
    conversationCreated = Signal(str, str)    # id, title

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

        # Connect system monitor updates
        self.system_monitor.stats_ready.connect(self._on_system_stats)

        # Poll system stats every 2 seconds
        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(2000)
        self._stats_timer.timeout.connect(self.system_monitor.update)
        self._stats_timer.start()

    # ── Conversation ──────────────────────────────────────────────────────

    @Slot(str)
    def sendMessage(self, text: str):
        """
        Entry point for all user messages from QML.
        Routes through Agent Runtime for intent classification.
        """
        if not text.strip():
            return

        text = text.strip()
        logger.info("sendMessage: %s", text[:120])

        self._emit_timeline_event("user_message", f"User: {text[:80]}")

        worker = AsyncWorker(self._async_send_message(text))
        worker.error.connect(lambda e: self.streamError.emit(e))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    async def _async_send_message(self, text: str):
        """
        Process message through Agent Runtime first.
        Falls back to streaming chat for conversation intents.
        """
        self.messageReceived.emit("user", text)

        conv_id = await self._ensure_conversation(text)
        if not conv_id:
            return

        await self.conversation_service.add_message(
            conversation_id=conv_id, role="user", content=text,
        )

        memories = await self.memory_service.get_relevant_memories(text)

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
                    conversation_id=conv_id,
                    role="assistant",
                    content=result,
                )
                await self.memory_service.extract_and_store(text, result)
                return

        await self._stream_chat(text, conv_id, memories)

    async def _ensure_conversation(self, text: str) -> Optional[str]:
        if not self._current_conversation_id:
            conv = await self.conversation_service.create_conversation(
                title=text[:50],
            )
            self._current_conversation_id = conv["id"]
            self.conversationCreated.emit(conv["id"], conv["title"])
        return self._current_conversation_id

    async def _stream_chat(self, text: str, conv_id: str,
                           memories: list[dict]):
        """Stream a conversational AI response through Ollama."""
        history = await self.conversation_service.get_messages(conv_id)

        full_response = ""
        chunk_count = 0
        try:
            async for chunk in self.ollama.stream_chat(
                messages=history,
                memories=memories,
            ):
                chunk_count += 1
                self.streamChunk.emit(chunk)
                full_response += chunk
        except Exception as e:
            logger.error("Stream error after %s chunks: %s", chunk_count, e)
            self.streamError.emit(str(e))
            return

        logger.info(
            "Stream complete: %s chunks, %s chars",
            chunk_count, len(full_response),
        )
        self.streamComplete.emit()

        await self.conversation_service.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=full_response,
        )

        await self.memory_service.extract_and_store(text, full_response)

        self._emit_timeline_event(
            "ai_response",
            f"AI responded ({len(full_response)} chars)",
        )

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
        worker = AsyncWorker(
            self.conversation_service.delete_conversation(conversation_id)
        )
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.finished.connect(self.loadConversations)
        self._active_workers.append(worker)
        worker.start()

    # ── Plugins ───────────────────────────────────────────────────────────

    @Slot()
    def loadPlugins(self):
        plugins = self.plugin_manager.get_plugin_list()
        self.pluginsLoaded.emit(plugins)

    @Slot(str, str)
    def executePlugin(self, plugin_name: str, payload: str):
        """Execute a plugin by name with a string payload."""
        self._emit_timeline_event("plugin_execute", f"Plugin: {plugin_name}")
        worker = AsyncWorker(
            self._async_execute_plugin(plugin_name, payload)
        )
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
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        return await plugin.execute({"input": payload})

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

    # ── Utilities ─────────────────────────────────────────────────────────

    def _emit_timeline_event(self, event_type: str, description: str):
        import time
        self.timelineEventAdded.emit({
            "type": event_type,
            "description": description,
            "timestamp": int(time.time() * 1000),
        })

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)

    @Slot(result=str)
    def currentConversationId(self) -> str:
        return self._current_conversation_id or ""

    def cleanup(self):
        """Shut down workers, timers, and connections."""
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
