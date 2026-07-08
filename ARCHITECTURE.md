# AETHER — Architectural Audit Report

**Date:** 2026-07-04
**Python:** 3.10.6 | **PySide6:** 6.6+ | **Qt Quick:** 2.15 | **OS:** Windows
**Repo:** 21 commits | **Tests:** 47 (18 pass, 21 fail, 8 error)

---

## 1. Project Overview

AETHER is a native desktop AI agent that routes user requests through an intent-driven pipeline: classify → plan → reason → execute → observe → reflect. It provides a PySide6/QML UI with chat, memory, plugin tools, and an execution timeline.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         app.py (Entry Point)                        │
│              os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"      │
│                   Sets Fusion before QML engine                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│                    AetherApplication (application.py)               │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ SplashScreen  │  │ SystemInit.  │  │ QQmlApplicationEngine   │  │
│  │ (ui/splash.py)│  │ (QThread)    │  │ + 11 QML files          │  │
│  └───────────────┘  └──────┬───────┘  └──────────┬──────────────┘  │
│                            │                      │                 │
│                            ▼                      ▼                 │
│                     services dict          QMLBridge (bridge.py)    │
│                      (14 objects)          contextProperty "bridge" │
└─────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────┐
│                         Initializer Thread                          │
│                                                                     │
│  1. DB Manager ────► 2. Ollama ────► 3. Memory ──► 4. Conversation │
│         │                                                            │
│  5. ToolRegistry ◄──── 6. PluginManager (discovers 12 plugins)     │
│         │                                                            │
│  7. IntentRouter + Planner + ObsEngine + ReflectEngine + PermMgr    │
│         │                                                            │
│  8. ReasoningEngine ────► AgentRuntime                              │
│         │                                                            │
│  Wires: bridge.agent_runtime = AgentRuntime(...)                    │
└─────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────┐
│                     AgentRuntime (agent_runtime.py)                 │
│                                                                     │
│  process(text)                                                      │
│      │                                                              │
│      ▼                                                              │
│  IntentRouter.classify(text)                                        │
│      │                                                              │
│      ├── KNOWLEDGE ──────► _handle_knowledge → LLM only             │
│      ├── DESKTOP_ACTION ─► _handle_desktop_action → plan + tools    │
│      ├── MIXED_TASK ─────► _handle_mixed_task → plan + LLM + tools │
│      └── UNKNOWN ───────► _handle_unknown → clarification prompt   │
│                                                                     │
│  _tool_gate(): "Can LLM answer without OS?" → YES/NO               │
│                                                                     │
│  ReasoningEngine.run_loop(context, plan, max_iterations)            │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │  think() → execute_step() → observe() → reflect() → loop │     │
│    │  Stops on is_complete or max iterations                   │     │
│    └──────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────┐
│                         Plugin Architecture                         │
│                                                                     │
│  models/tool_base.py ──── ToolBase (ABC) + ToolObservation dataclass│
│  models/plugin_base.py ──── PluginBase (ABC) legacy                 │
│                                                                     │
│  12 plugin directories: browser, terminal, filesystem, executor,    │
│    sysmon, docker, git, memory, system, vscode, vision (PluginBase),│
│    voice (PluginBase)                                               │
│                                                                     │
│  PluginManager discovers plugin.py files, loads tool/plugin classes,│
│    wraps PluginBase via LegacyPluginAdapter, registers in ToolReg.  │
└─────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────┐
│                        Database (SQLite)                            │
│                                                                     │
│  Tables: conversations, messages, memories, memory_tags, settings,  │
│          plugin_data, execution_timeline                             │
│  WAL mode, foreign_keys ON, auto-migration via PRAGMA table_info    │
│  7 columns added post-creation (pinned, favorite, custom_title,     │
│    last_message, message_count, timeline.conversation_id,           │
│    memories.conversation_id)                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### File Inventory

| Layer | Files | Lines |
|-------|-------|-------|
| Core engine | 11 `.py` (`core/`) | ~1,700 |
| Services | 6 `.py` (`services/`) | ~1,000 |
| Database | 1 `.py` (`database/`) | ~490 |
| Models | 3 `.py` (`models/`) | ~140 |
| Plugins | 12 `.py` + 12 `__init__.py` | ~1,500 |
| QML UI | 11 `.qml` (`ui/qml/`) | ~3,500 |
| Entry/Utils | 4 `.py` (`app.py`, `utils/`, `ui/splash.py`) | ~270 |
| Tests | 1 `.py` (`tests/`) | ~406 |
| **Total** | **~45 Python + 11 QML** | **~9,000** |

---

## 2. Component Scores (1–10)

### Architecture

| Component | Score | Comments |
|-----------|-------|----------|
| **Intent Router** | 8/10 | Two-stage (regex + LLM), four clean routes, good pattern coverage. |
| **Planner** | 7/10 | Dual enforcement (`_is_knowledge_only` + LLM prompt), `replan()` exists. |
| **Agent Runtime** | 8/10 | Clean routing, tool gate, iteration limits per route. |
| **Reasoning Engine** | 7/10 | `run_loop()` with `max_iterations`, think/execute/observe/reflect. |
| **Reflection** | 5/10 | LLM path fragile (single `|` delimiter), rule fallback weak. Rule-based only checks 3 conditions. |
| **Observation Engine** | 7/10 | Clean ring buffer (200), structured dict, OK. |
| **Permission Manager** | 4/10 | Token-based matching (`"rm -rf" in input_str`), no real deny enforcement, always auto-approves on LLM failure. |
| **Tool Registry** | 8/10 | Clean registration, `find_by_capability()`, legacy adapter pattern. |
| **Plugin Manager** | 7/10 | Lazy discovery, handles both ToolBase and PluginBase, stub fallback for failed loads. |
| **QML Bridge** | 8/10 | 20+ signals, 15+ slots, `AsyncWorker` pattern, clean lifecycle. |
| **Database** | 9/10 | WAL, foreign keys, auto-migration, clean API. |
| **Conversation Service** | 8/10 | Full CRUD, export (MD/JSON), search, auto-title with 19 patterns. |

### Infrastructure

| Component | Score | Comments |
|-----------|-------|----------|
| **Tests** | 3/10 | 47 tests: 18 pass, 21 fail, 8 error. Plugin tests broken (ToolObservation return type). |
| **Security** | 3/10 | Permission manager is token-gated (bypassable), `executor` plugin has no sandbox, `terminal` plugin runs arbitrary commands. |
| **Error Handling** | 5/10 | Most async paths wrapped in try/except, but many just log and return placeholder. No retry policy for transient DB errors. |
| **QML** | 9/10 | Zero warnings, zero binding loops, proper `ListModel`, `Behavior` animations, responsive layout. |
| **Documentation** | 6/10 | Good docstrings, but ARCHITECTURE.md was stale (now updated). |
| **Async Hygiene** | 6/10 | `AsyncWorker` works but creates a new event loop per call. Not shared. `on_step` callback in `run_loop` is `await`'d but never awaited. |

### Overall Architecture Score: **6.5/10**

---

## 3. Critical Issues Found

### 🔴 CRITICAL: Plugin Tests Assert Against Wrong Return Type

**File:** `tests/test_core.py`
**Impact:** 21 of 47 tests fail
**Root cause:** Tests were written for `PluginBase.execute()` which returns `str`. All 8 ToolBase plugins now return `ToolObservation` objects. Every assertion like `"hello" in result` fails because `result` is a `ToolObservation`.

```python
# OLD (expected): result = "hello world"
# NEW (actual):   result = ToolObservation(stdout="hello world\n", ...)
assert "hello" in result  # TypeError: argument of type 'ToolObservation' is not iterable
assert isinstance(result, str)  # AssertionError: ToolObservation is not str
```

### 🔴 CRITICAL: Permission Manager Is Token-Gated (Bypassable)

**Files:** `core/permission_manager.py:18-24`, `core/reasoning_engine.py:110-118`
**Impact:** Any command can be made to match a deny-list rule simply by not including the exact token string. `"rm -rf /"` is blocked, but `"Remove-Item -Path C:\ -Recurse -Force"` (PowerShell equivalent) passes right through, as would `"rm -rf --no-preserve-root /"` (subtle variation). Additionally, `request_approval()` always returns `False` on high risk when `_auto_approve_high_risk` is `False`, making high-risk actions silently impossible rather than prompting the user.

### 🔴 CRITICAL: Executor Plugin Runs Code With No Sandbox

**File:** `plugins/executor/plugin.py:62-76`
**Impact:** `exec()` and `eval()` are called with `__builtins__` available and no restriction on imports, file I/O, or network access. Any user request to "run code" gets full Python interpreter access to the host. Combined with the permission bypass above, this is a privilege escalation vector.

### 🟡 HIGH: `on_step` Callback Never Awaited

**File:** `core/reasoning_engine.py:138-139, 195-196`
**Impact:** The `on_step` async callback is called but not awaited:

```python
if on_step:
    await on_step(state)  # BUG: should be 'await on_step(state)' but it IS awaited
```

Actually wait, looking again at line 139: `await on_step(state)` — it IS awaited. But in `agent_runtime.py`, the `agent_runtime` doesn't pass `on_step` at all, so this code path is dead.

### 🟡 HIGH: PluginManager Test Broken by Signature Change

**File:** `tests/test_core.py:326`
```python
self.mgr = PluginManager(plugins_dir)  # Missing tool_registry argument
```
`PluginManager.__init__()` now requires `tool_registry`. Tests haven't been updated.

### 🟡 HIGH: BrowserPlugin Missing `initialize()` Method

**File:** `plugins/browser/plugin.py`
**Impact:** Tests call `self.plugin.initialize()` (line 225) but `BrowserPlugin` inherits from `ToolBase` which has no `initialize()` method. This causes `AttributeError` on 4 browser tests.

### 🟡 MEDIUM: `stream_chat()` Never Actually Streams in Agent Path

**File:** `core/bridge.py:175`
**Impact:** When `agent_runtime.process()` returns a result, the `_stream_chat()` fallback is skipped. But `_handle_knowledge()` returns a single string via `ollama.generate()`, not a stream. The user sees the full response only after the LLM finishes — no token-by-token streaming for agent-routed requests.

### 🟡 MEDIUM: Legacy PluginAdapter Has No Parameter Mapping

**File:** `core/tool_registry.py:30`
**Impact:** `LegacyPluginAdapter.parameters()` returns `{"input": {"type": "string"}}` for all legacy plugins, ignoring the actual parameter schemas from `PluginBase`. The vision and voice plugins have meaningful settings schemas that are lost.

### 🟡 MEDIUM: Title Generation `test_extract_memories_from_name` Fails

**File:** `tests/test_core.py:117-123`
**Impact:** `MemoryService.extract_and_store()` doesn't actually extract name information from conversation text. The test expects name extraction, but the method only adds to short-term memory without analysis.

### 🟢 LOW: Deprecation Warning for `pytest-asyncio` Config

**Context:** `pytest-asyncio` defaults will change in future versions. Tests should set `asyncio_mode = "auto"` in `pytest.ini`.

### 🟢 LOW: `intent_engine.py` Orphaned File

**File:** `core/intent_engine.py`
**Impact:** The old `IntentEngine` class at 194 lines is no longer imported anywhere. `intent_router.py` replaced it. Should be removed or marked deprecated.

### 🟢 LOW: Splash Progress Bar Uses Indeterminate Mode

**File:** `ui/splash.py:79`
**Impact:** `QProgressBar` is set to `setRange(0, 0)` (indeterminate). It never shows real progress. The `set_status()` method updates text but the bar never fills.

---

## 4. Data Flow Analysis

### Request Path (Happy Path)

```
User types text
  → CommandInput._submit()
  → bridge.sendMessage(text)
    → AsyncWorker._async_send_message(text)
      → _ensure_conversation() (creates if none exists)
      → bridge.messageReceived.emit("user", text)
      → conversation_service.add_message()
      → memory_service.extract_and_store()
      → agent_runtime.process(text)
        → intent_router.classify(text)
          → _check_knowledge() (regex)
          → _check_desktop_action() (regex)
          → _check_mixed_task() (regex)
          → _llm_classify() (LLM fallback)
        → Route handler called
          → KNOWLEDGE: ollama.generate() → return
          → DESKTOP_ACTION: planner.create_plan() → reasoning_engine.run_loop()
          → MIXED_TASK: planner.create_plan() → reasoning_engine.run_loop()
      → bridge.messageReceived.emit("assistant", result)
      → bridge.streamComplete.emit()
      → conversation_service.add_message()
```

### Reasoning Loop

```
run_loop(context, plan, max_iterations):
  for iteration in range(max_iterations):
    state = think(context, plan)     # LLM decides next tool or completion
    yield state                      # Emitted via AsyncIterator
    if state.is_complete: break
    if no tool selected: break
    tool_result = execute_step(tool, params)
    observation_engine.observe(tool, params, result)
    state.observation = observation
    reflection, action = reflection_engine.reflect(tool, result)
    if blocked: break
    if continue/skip: plan.current_step++
    context = f"Previous: {thought}\nResult: {summary}\nContinue..."
```

---

## 5. Design Patterns

| Pattern | Location | Implementation |
|---------|----------|----------------|
| **Strategy** | `intent_router.py` | Route enum selects handler strategy |
| **Chain of Responsibility** | `IntentRouter.classify()` | Knowledge → Desktop → Mixed → Unknown |
| **Template Method** | `ReasoningEngine.run_loop()` | Think → Execute → Observe → Reflect |
| **Observer** | `QMLBridge` signals/slots | 20+ Qt signals connected to QML |
| **Adapter** | `LegacyPluginAdapter` | Wraps PluginBase as ToolBase |
| **Registry** | `ToolRegistry` | Tools register by name, lookup by name |
| **Worker Thread** | `AsyncWorker` | Runs asyncio coroutines in QThread |
| **Factory** | `SystemInitializer.run()` | Creates and wires ~14 service objects |
| **Repository** | `DatabaseManager` | Data access layer for SQLite |
| **Ring Buffer** | `ObservationEngine._history` | 200-entry ring buffer |

---

## 6. Security Assessment

| Issue | Severity | File | Recommendation |
|-------|----------|------|----------------|
| No code sandbox | 🔴 Critical | `executor/plugin.py:62-76` | Use `RestrictedPython` or a subprocess with `-I` flag |
| Token-gated permissions | 🟡 High | `permission_manager.py:18-24` | Use regex patterns, block dangerous flag combos |
| Terminal command injection | 🟡 High | `terminal/plugin.py:48-57` | Commands run via `subprocess_shell` with user input |
| No Input length limits | 🟡 Medium | `bridge.py:128-165` | No cap on text input, potential resource exhaustion |
| Arbitrary file deletion | 🟡 Medium | `filesystem/plugin.py:134-142` | Path traversal via `..` not blocked |
| No encryption at rest | 🟢 Low | `database/db_manager.py` | SQLite file unencrypted on disk |
| No auth/identity | 🟢 Low | Entire app | Single-user desktop app (acceptable) |

---

## 7. Test Coverage

### By Module

| Module | Tests | Pass | Fail | Error | Coverage Estimate |
|--------|-------|------|------|-------|-------------------|
| `DatabaseManager` | 9 | 9 | 0 | 0 | ~80% |
| `MemoryService` | 5 | 4 | 1 | 0 | ~50% |
| `TerminalPlugin` | 4 | 0 | 4 | 0 | ~60% (broken) |
| `FilesystemPlugin` | 4 | 0 | 4 | 0 | ~60% (broken) |
| `BrowserPlugin` | 4 | 0 | 0 | 4 | ~70% (broken) |
| `ExecutorPlugin` | 7 | 0 | 7 | 0 | ~70% (broken) |
| `SysmonPlugin` | 5 | 0 | 5 | 0 | ~60% (broken) |
| `PluginManager` | 4 | 0 | 0 | 4 | ~40% (broken) |
| `ConversationService` | 5 | 5 | 0 | 0 | ~60% |

**Missing test coverage:**
- `IntentRouter` — 0 tests (4 routes, 2-stage classification)
- `AgentRuntime` — 0 tests (4 handlers, tool gate)
- `Planner` — 0 tests (_is_knowledge_only, _llm_decompose, replan)
- `ReasoningEngine` — 0 tests (run_loop, think, execute_step)
- `ReflectionEngine` — 0 tests (reflect, _llm_reflect, _rule_based_reflect)
- `ObservationEngine` — 0 tests
- `PermissionManager` — 0 tests
- `QMLBridge` — 0 tests (20+ signals, 15+ slots)
- `SystemMonitorService` — 0 tests
- `OllamaService` — 0 tests
- All QML files — 0 tests (no Qt Test setup)
- All `__init__.py` files — 0 tests

### Test Infrastructure Issues
1. `PluginManager.__init__()` now requires `tool_registry` arg — tests not updated
2. `BrowserPlugin` has no `initialize()` method — tests call it
3. All plugin tests expect `str` return from `execute()` — plugins now return `ToolObservation`
4. No `pytest.ini` or `pyproject.toml` config for `pytest-asyncio`

---

## 8. Technical Debt & Anti-patterns

### Code Quality

| Issue | Location | Details |
|-------|----------|---------|
| **Magical `__import__`** | `reasoning_engine.py:91` | Uses `__import__("json")` instead of `import json` at top of file |
| **Dead code** | `intent_engine.py` (194 lines) | Replaced by `intent_router.py`, not imported anywhere |
| **Dead code path** | `reasoning_engine.py:138-139` | `on_step` parameter passed but never supplied by callers |
| **Function-level import** | `tool_registry.py:33` | `import time` inside method |
| **Inconsistent import style** | Multiple files | Mix of top-level and inner imports |
| **String formatting** | Multiple files | Mix of `f"{x}"`, `%s`, and `.format()` in same file (e.g., `ollama_service.py` lines 45, 65) |
| **Missing `__pycache__` in .gitignore** | `.gitignore` | Should add `__pycache__/`, `*.pyc` |
| **No `pytest.ini`** | Project root | Tests need `asyncio_mode = "auto"` to suppress warning |
| **Hardcoded paths** | `plugins/docker/plugin.py:44-45` | `C:/Program Files/Docker/...` — won't work for all Windows installs |
| **Inconsistent return types** | Plugin tests vs implementation | Tests assume `str`, implementation returns `ToolObservation` |

### Database

| Issue | Details |
|-------|---------|
| Schema creation uses `executescript` with hardcoded SQL string | No SQL file separation |
| `update_last_message()` updates `message_count` with `message_count+1` instead of counting actual rows | Can drift if messages are deleted |
| `duplicate_conversation()` doesn't duplicate `pinned`, `favorite` flags | Data loss on duplicate |
| No cascade delete on `FOREIGN KEY` — handled manually in Python | Race condition risk (delete between SELECT and DELETE) |

### QML

| Issue | Details |
|-------|---------|
| `themeObj` passed via `required property` to every component | Works but verbose — could use singleton |
| Two identical popup menu definitions in Sidebar.qml (~60 lines each) | Three-dot and right-click menus are duplicate code |
| Empty state in `ExecutionTimeline.qml` is inside `ListView` as sibling to delegates | Item is always created, even when model has data |

---

## 9. Roadmap Recommendations

### Immediate (Week 1)

1. **Fix plugin tests** — update all 21 broken test assertions to check `ToolObservation.stdout` instead of raw string:
   ```python
   result = await self.plugin.execute({"input": "echo hello"})
   assert "hello" in result.stdout if isinstance(result, ToolObservation) else result
   ```
2. **Fix `PluginManager` test setup** — pass `ToolRegistry()` argument
3. **Add `BrowserPlugin.initialize()`** — no-op method to match test interface
4. **Add `pytest.ini`** — `[pytest] asyncio_mode = auto`

### Short-term (Week 2–3)

5. **Add IntentRouter tests** — 8+ tests for all 4 routes, both regex and LLM paths (mock Ollama)
6. **Add AgentRuntime tests** — 4 handler tests with mocked dependencies
7. **Fix Permission Manager** — regex-based pattern matching, real user prompt via bridge signal
8. **Remove orphaned `intent_engine.py`**
9. **Streaming for agent-routed responses** — wire `_handle_knowledge` to `stream_chat` instead of `generate`

### Medium-term (Week 4–6)

10. **Executor sandbox** — subprocess with `-I` flag, restricted globals, timeout enforcement
11. **Cross-platform path handling** — use `Path` consistently in Docker/plugin paths
12. **QML test harness** — `Qt Test` framework for QML component testing
13. **Export UI** — progress dialog for large exports, error state in QML
14. **Replace duplicate Sidebar popup code** — extract to reusable QML component

### Long-term (Month 2+)

15. **Plugin hot-reload** — file watcher on plugin directories for development iteration
16. **Plugin settings UI** — wire `PluginBase.settings()` to QML settings panel
17. **Multi-modal streaming** — real-time audio I/O without blocking UI
18. **Plugin isolation** — subprocess per plugin for crash isolation
19. **Vector memory search** — replace keyword matching with embeddings for semantic memory retrieval
20. **Desktop analytics** — usage telemetry (opt-in) for UX improvement data

---

## 10. Summary

### What's Strong
- Clean intent routing with 2-stage classification (regex + LLM)
- Zero-warning QML with proper binding discipline and `ListModel` usage
- Solid database layer with WAL, FK constraints, auto-migration
- Good separation of concerns between core, services, plugins, and UI
- 8 tool plugins (terminal, filesystem, browser, executor, sysmon, docker, git, system) + 2 PluginBase plugins (vision, voice)
- Full conversation CRUD with export (MD + JSON), search, duplicate, cascade delete

### What Needs Work
- **Plugin test suite is completely broken** (21 failures + 8 errors out of 47 tests)
- **No tests for core agent pipeline** (IntentRouter, AgentRuntime, Planner, ReasoningEngine, ReflectionEngine, PermissionManager)
- **Security model is token-gated** — easily bypassed
- **Executor plugin runs arbitrary Python** with no sandbox
- **No streaming for agent-routed LLM responses**

### Verdict

AETHER has strong architectural bones — the intent routing, tool registry, database, and QML layer are well-designed. The plugin system is extensible and the reasoning loop is functional. However, the test suite is in critical condition (most tests broken), the security model is superficial, and core engine components have zero test coverage. The project needs ~2 weeks of focused effort on testing and security hardening before it can be considered production-ready.
