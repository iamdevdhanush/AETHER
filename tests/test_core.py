"""
AETHER Test Suite
Tests core components without requiring Qt or Ollama.
Run with: python -m pytest tests/ -v
"""

import asyncio
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Database Tests ────────────────────────────────────────────────────────

class TestDatabaseManager:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        from database.db_manager import DatabaseManager
        self.db = DatabaseManager(Path(self.tmp.name))
        self.db.initialize()

    def teardown_method(self):
        self.db.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_create_conversation(self):
        conv = self.db.create_conversation("Test conversation")
        assert conv["id"]
        assert conv["title"] == "Test conversation"

    def test_list_conversations(self):
        self.db.create_conversation("Conv 1")
        self.db.create_conversation("Conv 2")
        convs = self.db.list_conversations()
        assert len(convs) == 2

    def test_add_and_get_messages(self):
        conv = self.db.create_conversation("Msg test")
        self.db.add_message(conv["id"], "user", "Hello")
        self.db.add_message(conv["id"], "assistant", "Hi there!")
        msgs = self.db.get_messages(conv["id"])
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_delete_conversation_cascades(self):
        conv = self.db.create_conversation("Delete me")
        self.db.add_message(conv["id"], "user", "test")
        self.db.delete_conversation(conv["id"])
        msgs = self.db.get_messages(conv["id"])
        assert len(msgs) == 0

    def test_add_and_get_memories(self):
        self.db.add_memory("User's name is Alice", importance=0.9)
        self.db.add_memory("User prefers Python", importance=0.7)
        mems = self.db.get_memories()
        assert len(mems) == 2
        # Should be ordered by importance desc
        assert mems[0]["importance"] >= mems[1]["importance"]

    def test_search_memories(self):
        self.db.add_memory("User loves coffee")
        self.db.add_memory("User dislikes tea")
        results = self.db.search_memories("coffee")
        assert len(results) == 1
        assert "coffee" in results[0]["content"]

    def test_settings(self):
        self.db.set_setting("model", "llama3.2")
        val = self.db.get_setting("model")
        assert val == "llama3.2"

    def test_plugin_data(self):
        self.db.set_plugin_data("terminal", "timeout", "30")
        val = self.db.get_plugin_data("terminal", "timeout")
        assert val == "30"

    def test_timeline_event(self):
        evt = self.db.add_timeline_event("test", "A test event")
        assert evt["id"]
        events = self.db.get_timeline_events()
        assert len(events) == 1


# ── Memory Service Tests ──────────────────────────────────────────────────

class TestMemoryService:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        from database.db_manager import DatabaseManager
        from services.memory_service import MemoryService
        self.db = DatabaseManager(Path(self.tmp.name))
        self.db.initialize()
        self.svc = MemoryService(self.db)

    def teardown_method(self):
        self.db.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_add_memory(self):
        result = asyncio.run(self.svc.add_memory("Test memory", importance=0.8))
        assert result["id"]
        assert result["content"] == "Test memory"

    def test_get_all_memories(self):
        asyncio.run(self.svc.add_memory("Memory 1"))
        asyncio.run(self.svc.add_memory("Memory 2"))
        mems = asyncio.run(self.svc.get_all_memories())
        assert len(mems) == 2

    def test_extract_memories_from_name(self):
        asyncio.run(self.svc.extract_and_store(
            "My name is Bob", "Nice to meet you, Bob!"
        ))
        mems = asyncio.run(self.svc.get_all_memories())
        # Should have extracted the name
        assert len(mems) >= 1

    def test_get_relevant_memories(self):
        asyncio.run(self.svc.add_memory("User is a Python developer"))
        asyncio.run(self.svc.add_memory("User likes dark themes"))
        results = asyncio.run(self.svc.get_relevant_memories("Python code"))
        assert any("Python" in m["content"] for m in results)

    def test_delete_memory(self):
        mem = asyncio.run(self.svc.add_memory("Forget me"))
        asyncio.run(self.svc.delete_memory(mem["id"]))
        mems = asyncio.run(self.svc.get_all_memories())
        assert all(m["id"] != mem["id"] for m in mems)


# ── Plugin Tests ──────────────────────────────────────────────────────────

class TestTerminalPlugin:
    def setup_method(self):
        from plugins.terminal.plugin import TerminalPlugin
        self.plugin = TerminalPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        meta = self.plugin.metadata()
        assert meta["name"] == "terminal"
        assert "description" in meta
        assert "version" in meta

    def test_echo_command(self):
        result = asyncio.run(self.plugin.execute({"input": "echo hello"}))
        assert "hello" in result.lower()

    def test_empty_command(self):
        result = asyncio.run(self.plugin.execute({"input": ""}))
        assert "No command" in result

    def test_invalid_command(self):
        result = asyncio.run(self.plugin.execute(
            {"input": "this_command_does_not_exist_xyz"}
        ))
        # Should not raise, should return error message
        assert isinstance(result, str)
        assert len(result) > 0


class TestFilesystemPlugin:
    def setup_method(self):
        from plugins.filesystem.plugin import FilesystemPlugin
        self.plugin = FilesystemPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        meta = self.plugin.metadata()
        assert meta["name"] == "filesystem"

    def test_list_home(self):
        import os
        result = asyncio.run(self.plugin.execute({
            "action": "list",
            "path": str(Path.home()),
        }))
        assert "Directory:" in result

    def test_read_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            # Write
            write_result = asyncio.run(self.plugin.execute({
                "action": "write",
                "path": str(test_file),
                "content": "Hello AETHER",
            }))
            assert "Written" in write_result
            # Read back
            read_result = asyncio.run(self.plugin.execute({
                "action": "read",
                "path": str(test_file),
            }))
            assert "Hello AETHER" in read_result

    def test_stat_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "stat.txt"
            test_file.write_text("test")
            result = asyncio.run(self.plugin.execute({
                "action": "stat",
                "path": str(test_file),
            }))
            assert "File:" in result


class TestBrowserPlugin:
    def setup_method(self):
        from plugins.browser.plugin import BrowserPlugin
        self.plugin = BrowserPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        meta = self.plugin.metadata()
        assert meta["name"] == "browser"

    def test_url_resolution_https(self):
        url = self.plugin._resolve_url("https://example.com")
        assert url == "https://example.com"

    def test_url_resolution_no_scheme(self):
        url = self.plugin._resolve_url("example.com")
        assert url.startswith("https://")

    def test_url_resolution_search(self):
        url = self.plugin._resolve_url("what is the meaning of life")
        assert "google.com/search" in url
        assert "meaning" in url


class TestExecutorPlugin:
    def setup_method(self):
        from plugins.executor.plugin import ExecutorPlugin
        self.plugin = ExecutorPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        meta = self.plugin.metadata()
        assert meta["name"] == "executor"

    def test_simple_expression(self):
        result = asyncio.run(self.plugin.execute({"input": "2 + 2"}))
        assert "4" in result

    def test_print_statement(self):
        result = asyncio.run(self.plugin.execute({"input": "print('hello world')"}))
        assert "hello world" in result

    def test_multiline_code(self):
        code = "x = 10\ny = 20\nprint(x + y)"
        result = asyncio.run(self.plugin.execute({"input": code}))
        assert "30" in result

    def test_syntax_error_handled(self):
        result = asyncio.run(self.plugin.execute({"input": "def broken(:\n    pass"}))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_input(self):
        result = asyncio.run(self.plugin.execute({"input": ""}))
        assert "No code" in result

    def test_markdown_fences_stripped(self):
        result = asyncio.run(self.plugin.execute({
            "input": "```python\nprint('fenced')\n```"
        }))
        assert "fenced" in result


class TestSysmonPlugin:
    def setup_method(self):
        from plugins.sysmon.plugin import SysmonPlugin
        self.plugin = SysmonPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        meta = self.plugin.metadata()
        assert meta["name"] == "sysmon"

    def test_full_report(self):
        result = asyncio.run(self.plugin.execute({"input": "all"}))
        assert "CPU" in result

    def test_cpu_report(self):
        result = asyncio.run(self.plugin.execute({"input": "cpu"}))
        assert "CPU" in result
        assert "%" in result

    def test_memory_report(self):
        result = asyncio.run(self.plugin.execute({"input": "memory"}))
        assert "RAM" in result
        assert "GB" in result

    def test_disk_report(self):
        result = asyncio.run(self.plugin.execute({"input": "disk"}))
        assert "Disk" in result


class TestPluginManager:
    def setup_method(self):
        from services.plugin_manager import PluginManager
        plugins_dir = Path(__file__).parent.parent / "plugins"
        self.mgr = PluginManager(plugins_dir)
        self.mgr.discover_and_load()

    def teardown_method(self):
        self.mgr.shutdown_all()

    def test_plugins_loaded(self):
        names = self.mgr.list_names()
        assert "terminal" in names
        assert "filesystem" in names
        assert "browser" in names
        assert "executor" in names
        assert "sysmon" in names

    def test_get_plugin(self):
        p = self.mgr.get_plugin("terminal")
        assert p is not None

    def test_get_nonexistent_plugin(self):
        p = self.mgr.get_plugin("does_not_exist")
        assert p is None

    def test_plugin_list_serializable(self):
        lst = self.mgr.get_plugin_list()
        assert isinstance(lst, list)
        for item in lst:
            assert "name" in item
            assert "description" in item
            assert "version" in item


# ── Conversation Service Tests ────────────────────────────────────────────

class TestConversationService:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        from database.db_manager import DatabaseManager
        from services.ollama_service import OllamaService
        from services.memory_service import MemoryService
        from services.conversation_service import ConversationService
        self.db = DatabaseManager(Path(self.tmp.name))
        self.db.initialize()
        ollama = OllamaService()
        memory = MemoryService(self.db)
        self.svc = ConversationService(self.db, ollama, memory)

    def teardown_method(self):
        self.db.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_create_conversation(self):
        conv = asyncio.run(self.svc.create_conversation("Test"))
        assert conv["id"]
        assert conv["title"] == "Test"

    def test_list_conversations(self):
        asyncio.run(self.svc.create_conversation("C1"))
        asyncio.run(self.svc.create_conversation("C2"))
        convs = asyncio.run(self.svc.list_conversations())
        assert len(convs) == 2

    def test_add_message_auto_title(self):
        conv = asyncio.run(self.svc.create_conversation("New Conversation"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "What is Python?"))
        updated = self.db.get_conversation(conv["id"])
        # Title should have been updated from the first message
        assert updated["title"] != "New Conversation" or updated["title"] == "What is Python?"

    def test_get_messages(self):
        conv = asyncio.run(self.svc.create_conversation("Msg test"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "Hello"))
        asyncio.run(self.svc.add_message(conv["id"], "assistant", "Hi"))
        msgs = asyncio.run(self.svc.get_messages(conv["id"]))
        assert len(msgs) == 2

    def test_delete_conversation(self):
        conv = asyncio.run(self.svc.create_conversation("Delete me"))
        asyncio.run(self.svc.delete_conversation(conv["id"]))
        convs = asyncio.run(self.svc.list_conversations())
        assert all(c["id"] != conv["id"] for c in convs)
