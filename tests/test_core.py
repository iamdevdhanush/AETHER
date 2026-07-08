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

from models.tool_base import ToolObservation

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
        assert self.plugin.name() == "terminal"
        assert self.plugin.description()

    def test_echo_command(self):
        result = asyncio.run(self.plugin.execute({"input": "echo hello"}))
        assert "hello" in result.stdout.lower()

    def test_empty_command(self):
        result = asyncio.run(self.plugin.execute({"input": ""}))
        assert "No command" in result.stderr

    def test_invalid_command(self):
        result = asyncio.run(self.plugin.execute(
            {"input": "this_command_does_not_exist_xyz"}
        ))
        assert isinstance(result, ToolObservation)
        assert not result.success


class TestFilesystemPlugin:
    def setup_method(self):
        from plugins.filesystem.plugin import FilesystemPlugin
        self.plugin = FilesystemPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "filesystem"
        assert self.plugin.description()

    def test_list_home(self):
        import os
        result = asyncio.run(self.plugin.execute({
            "action": "list",
            "path": str(Path.home()),
        }))
        assert "Directory:" in result.stdout

    def test_read_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            # Write
            write_result = asyncio.run(self.plugin.execute({
                "action": "write",
                "path": str(test_file),
                "content": "Hello AETHER",
            }))
            assert "Written" in write_result.stdout
            # Read back
            read_result = asyncio.run(self.plugin.execute({
                "action": "read",
                "path": str(test_file),
            }))
            assert "Hello AETHER" in read_result.stdout

    def test_stat_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "stat.txt"
            test_file.write_text("test")
            result = asyncio.run(self.plugin.execute({
                "action": "stat",
                "path": str(test_file),
            }))
            assert "File:" in result.stdout


class TestBrowserPlugin:
    def setup_method(self):
        from plugins.browser.plugin import BrowserPlugin
        self.plugin = BrowserPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "browser"
        assert self.plugin.description()

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
        assert self.plugin.name() == "executor"
        assert self.plugin.description()

    def test_simple_expression(self):
        result = asyncio.run(self.plugin.execute({"input": "2 + 2"}))
        assert "4" in result.stdout

    def test_print_statement(self):
        result = asyncio.run(self.plugin.execute({"input": "print('hello world')"}))
        assert "hello world" in result.stdout

    def test_multiline_code(self):
        code = "x = 10\ny = 20\nprint(x + y)"
        result = asyncio.run(self.plugin.execute({"input": code}))
        assert "30" in result.stdout

    def test_syntax_error_handled(self):
        result = asyncio.run(self.plugin.execute({"input": "def broken(:\n    pass"}))
        assert isinstance(result, ToolObservation)
        assert not result.success

    def test_empty_input(self):
        result = asyncio.run(self.plugin.execute({"input": ""}))
        assert "No code" in result.stderr

    def test_markdown_fences_stripped(self):
        result = asyncio.run(self.plugin.execute({
            "input": "```python\nprint('fenced')\n```"
        }))
        assert "fenced" in result.stdout


class TestSysmonPlugin:
    def setup_method(self):
        from plugins.sysmon.plugin import SysmonPlugin
        self.plugin = SysmonPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "sysmon"
        assert self.plugin.description()

    def test_full_report(self):
        result = asyncio.run(self.plugin.execute({"input": "all"}))
        assert "CPU" in result.stdout

    def test_cpu_report(self):
        result = asyncio.run(self.plugin.execute({"input": "cpu"}))
        assert "CPU" in result.stdout
        assert "%" in result.stdout

    def test_memory_report(self):
        result = asyncio.run(self.plugin.execute({"input": "memory"}))
        assert "RAM" in result.stdout
        assert "GB" in result.stdout

    def test_disk_report(self):
        result = asyncio.run(self.plugin.execute({"input": "disk"}))
        assert "Disk" in result.stdout


class TestPluginManager:
    def setup_method(self):
        from core.tool_registry import ToolRegistry
        from services.plugin_manager import PluginManager
        plugins_dir = Path(__file__).parent.parent / "plugins"
        self.mgr = PluginManager(plugins_dir, ToolRegistry())
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
        assert updated["title"] != "New Conversation"

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

    def test_rename_conversation(self):
        conv = asyncio.run(self.svc.create_conversation("Original"))
        ok = asyncio.run(self.svc.rename_conversation(conv["id"], "Renamed"))
        assert ok
        updated = self.db.get_conversation(conv["id"])
        assert updated["title"] == "Renamed"

    def test_duplicate_conversation(self):
        conv = asyncio.run(self.svc.create_conversation("Original"))
        asyncio.run(self.svc.rename_conversation(conv["id"], "Original"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "Hello"))
        dup = asyncio.run(self.svc.duplicate_conversation(conv["id"]))
        assert dup is not None
        assert "Original" in dup["title"]
        dup_msgs = asyncio.run(self.svc.get_messages(dup["id"]))
        assert len(dup_msgs) == 1
        assert dup_msgs[0]["content"] == "Hello"

    def test_search_conversations(self):
        conv = asyncio.run(self.svc.create_conversation("Python discussion"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "What is Python?"))
        results = asyncio.run(self.svc.search_conversations("Python"))
        assert len(results) >= 1

    def test_export_markdown(self):
        conv = asyncio.run(self.svc.create_conversation("Export test"))
        asyncio.run(self.svc.rename_conversation(conv["id"], "Export test"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "Hello"))
        asyncio.run(self.svc.add_message(conv["id"], "assistant", "World"))
        md = asyncio.run(self.svc.export_conversation_markdown(conv["id"]))
        assert "# Export test" in md
        assert "Hello" in md
        assert "World" in md

    def test_export_json(self):
        conv = asyncio.run(self.svc.create_conversation("JSON export"))
        asyncio.run(self.svc.rename_conversation(conv["id"], "JSON export"))
        asyncio.run(self.svc.add_message(conv["id"], "user", "Hello"))
        js = asyncio.run(self.svc.export_conversation_json(conv["id"]))
        assert '"title": "JSON export"' in js
        assert '"role": "user"' in js


# ── Additional Plugin Tests ──────────────────────────────────────────────

class TestVSCodePlugin:
    def setup_method(self):
        from plugins.vscode.plugin import VSCodePlugin
        self.plugin = VSCodePlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "vscode"
        assert self.plugin.description()

    def test_parameters_schema(self):
        params = self.plugin.parameters()
        assert "input" in params.get("properties", {})


class TestGitPlugin:
    def setup_method(self):
        from plugins.git.plugin import GitPlugin
        self.plugin = GitPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "git"
        assert self.plugin.description()

    def test_parameters_schema(self):
        params = self.plugin.parameters()
        assert "input" in params.get("properties", {})
        assert "input" in params.get("required", [])


class TestDockerPlugin:
    def setup_method(self):
        from plugins.docker.plugin import DockerPlugin
        self.plugin = DockerPlugin()
        self.plugin.initialize()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "docker"
        assert self.plugin.description()

    def test_parameters_schema(self):
        params = self.plugin.parameters()
        assert "input" in params.get("properties", {})


class TestSystemPlugin:
    def setup_method(self):
        from plugins.system.plugin import SystemPlugin
        self.plugin = SystemPlugin()

    def teardown_method(self):
        self.plugin.shutdown()

    def test_metadata(self):
        assert self.plugin.name() == "system"
        assert self.plugin.description()

    def test_help_response(self):
        result = asyncio.run(self.plugin.execute({"input": "help"}))
        assert "Available:" in result.stdout


class TestMemoryPlugin:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        from database.db_manager import DatabaseManager
        from plugins.memory.plugin import MemoryPlugin
        self.db = DatabaseManager(Path(self.tmp.name))
        self.db.initialize()
        self.plugin = MemoryPlugin()
        self.plugin.initialize()
        self.plugin.set_db(self.db)

    def teardown_method(self):
        self.plugin.shutdown()
        self.db.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_metadata(self):
        assert self.plugin.name() == "memory"
        assert self.plugin.description()

    def test_list_empty(self):
        result = asyncio.run(self.plugin.execute({"input": "list"}))
        assert "No memories" in result.stdout

    def test_add_and_list(self):
        asyncio.run(self.plugin.execute({"input": "add test memory", "action": "add"}))
        result = asyncio.run(self.plugin.execute({"input": "", "action": "list"}))
        assert "Stored Memories" in result.stdout


class TestMemoryServiceEdgeCases:
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

    def test_extract_name_my_name_is(self):
        name = self.svc._extract_name("My name is Alice")
        assert name == "Alice"

    def test_extract_name_im_called(self):
        name = self.svc._extract_name("I'm called Bob")
        assert name == "Bob"

    def test_extract_name_no_match(self):
        name = self.svc._extract_name("Hello there")
        assert name is None

    def test_working_memory(self):
        self.svc.set_task("Open Chrome and search", ["Open Chrome", "Search"])
        ctx = self.svc.get_working_context()
        assert "Open Chrome" in ctx
        self.svc.update_task_progress(1)
        self.svc.store_artifact("result", "Found it")
        assert self.svc.working["artifacts"]["result"] == "Found it"
        self.svc.clear_working()
        assert self.svc.working["current_task"] is None

    def test_short_term_capped(self):
        for i in range(60):
            self.svc.add_to_short_term("user", f"msg{i}")
        assert len(self.svc.short_term) <= 50
        assert self.svc.short_term[-1]["content"] == "msg59"

    def test_get_preference(self):
        asyncio.run(self.svc.remember_preference("theme", "dark"))
        val = asyncio.run(self.svc.get_preference("theme"))
        assert val == "dark"

    def test_get_preference_nonexistent(self):
        val = asyncio.run(self.svc.get_preference("does_not_exist"))
        assert val is None

    def test_store_workflow(self):
        asyncio.run(self.svc.store_workflow("Test workflow", [{"tool": "terminal", "params": {"input": "echo hi"}}], "Success"))
        mems = asyncio.run(self.svc.get_all_memories())
        assert len(mems) >= 1

    def test_store_workflow_dedup(self):
        asyncio.run(self.svc.store_workflow("Unique workflow", [{"tool": "test"}], "Done"))
        asyncio.run(self.svc.store_workflow("Unique workflow", [{"tool": "test"}], "Done"))
        mems = asyncio.run(self.svc.get_all_memories())
        workflows = [m for m in mems if "workflow" in m.get("source", "")]
        assert len(workflows) <= 1


class TestToolObservation:
    def test_success_summary(self):
        obs = ToolObservation(stdout="Hello world", exit_code=0, success=True)
        assert "Hello world" in obs.summary()

    def test_failure_summary(self):
        obs = ToolObservation(stdout="", stderr="Error occurred", exit_code=1, success=False)
        assert "Error occurred" in obs.summary()

    def test_empty_success_summary(self):
        obs = ToolObservation(exit_code=0, success=True)
        assert obs.summary() == "(completed)"


# ── ToolBase Implementation Tests ────────────────────────────────────────

class TestToolBaseContract:
    def test_all_plugins_implement_toolbase(self):
        from core.tool_registry import ToolRegistry
        from services.plugin_manager import PluginManager
        plugins_dir = Path(__file__).parent.parent / "plugins"
        mgr = PluginManager(plugins_dir, ToolRegistry())
        mgr.discover_and_load()
        names = mgr.list_names()
        assert len(names) >= 3
        for name in names:
            tool = mgr.get_plugin(name)
            assert tool is not None or not mgr.PLUGIN_STUBS.get(name)
        mgr.shutdown_all()


# ── Core Component Tests ─────────────────────────────────────────────────

class TestToolRegistry:
    def setup_method(self):
        from core.tool_registry import ToolRegistry
        self.registry = ToolRegistry()

    def teardown_method(self):
        self.registry.shutdown_all()

    def test_register_and_get(self):
        from plugins.terminal.plugin import TerminalPlugin
        tool = TerminalPlugin()
        tool.initialize()
        self.registry.register(tool)
        assert self.registry.get("terminal") is tool

    def test_list_tools(self):
        from plugins.executor.plugin import ExecutorPlugin
        tool = ExecutorPlugin()
        tool.initialize()
        self.registry.register(tool)
        tools = self.registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "executor"

    def test_find_by_capability(self):
        from plugins.terminal.plugin import TerminalPlugin
        tool = TerminalPlugin()
        tool.initialize()
        self.registry.register(tool)
        results = self.registry.find_by_capability(["shell", "command"])
        assert len(results) >= 1

    def test_get_nonexistent(self):
        assert self.registry.get("nope") is None


class TestPermissionManager:
    def setup_method(self):
        from core.permission_manager import PermissionManager
        self.pm = PermissionManager()

    def test_low_risk(self):
        risk = self.pm.assess_risk("filesystem", {"input": "list /home"})
        from core.permission_manager import RiskLevel
        assert risk == RiskLevel.LOW

    def test_high_risk(self):
        risk = self.pm.assess_risk("system", {"input": "shutdown"})
        from core.permission_manager import RiskLevel
        assert risk == RiskLevel.HIGH

    def test_always_deny(self):
        risk = self.pm.assess_risk("terminal", {"input": "rm -rf /"})
        from core.permission_manager import RiskLevel
        assert risk == RiskLevel.HIGH

    def test_approval_flow(self):
        import uuid
        rid = str(uuid.uuid4())
        auto_approved = asyncio.run(
            self.pm.request_approval("system", {"input": "shutdown"}, "test")
        )
        assert not auto_approved
        approved = self.pm.approve(rid)
        assert not approved
        denied = self.pm.deny(rid)
        assert not denied


class TestObservationEngine:
    def setup_method(self):
        from core.observation_engine import ObservationEngine
        self.engine = ObservationEngine()

    def test_observe(self):
        obs = ToolObservation(stdout="hello", exit_code=0, success=True)
        result = asyncio.run(self.engine.observe("terminal", {"input": "echo hi"}, obs))
        assert result["tool"] == "terminal"
        assert result["stdout"] == "hello"
        assert result["success"] is True

    def test_get_last(self):
        obs = ToolObservation(stdout="test", success=True)
        asyncio.run(self.engine.observe("test", {}, obs))
        last = self.engine.get_last()
        assert last is not None
        assert last["tool"] == "test"

    def test_get_history(self):
        for i in range(5):
            obs = ToolObservation(stdout=f"msg{i}", success=True)
            asyncio.run(self.engine.observe(f"tool{i}", {}, obs))
        history = self.engine.get_history(limit=3)
        assert len(history) == 3
        assert history[-1]["tool"] == "tool4"

    def test_clear(self):
        obs = ToolObservation(stdout="test", success=True)
        asyncio.run(self.engine.observe("test", {}, obs))
        self.engine.clear()
        assert self.engine.get_last() is None

    def test_history_capped(self):
        for i in range(250):
            obs = ToolObservation(stdout=f"msg{i}", success=True)
            asyncio.run(self.engine.observe(f"tool{i}", {}, obs))
        assert len(self.engine._history) <= 200


# ── Database Migration Tests ─────────────────────────────────────────────

class TestDatabaseMigrations:
    def teardown_method(self):
        if hasattr(self, 'db'):
            self.db.close()
        if hasattr(self, 'tmp_path'):
            Path(self.tmp_path).unlink(missing_ok=True)

    def test_migration_adds_missing_columns(self):
        """Simulate old schema and verify migration adds columns."""
        import sqlite3
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.tmp_path = self.tmp.name
        conn = sqlite3.connect(self.tmp_path)
        conn.execute("""
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Conversation',
                model TEXT NOT NULL DEFAULT 'llama3.2',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                archived INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()

        from database.db_manager import DatabaseManager
        self.db = DatabaseManager(Path(self.tmp_path))
        self.db.initialize()

        conv = self.db.get_conversation(
            self.db.create_conversation("Migration test")["id"]
        )
        assert conv is not None
        assert conv["pinned"] == 0
        assert conv["favorite"] == 0
        assert conv["custom_title"] == 0
