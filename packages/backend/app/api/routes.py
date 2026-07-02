from fastapi import APIRouter, WebSocket
from loguru import logger

from app.core.llm import LLMService
from app.services.automation import automation_service
from app.services.file_operations import file_service
from app.memory.store import memory_store
from app.plugins.manager import plugin_manager
from app.models.schemas import (
    ChatRequest, LaunchAppRequest, CloseAppRequest,
    FileReadRequest, PluginToggleRequest,
)

router = APIRouter()
llm = LLMService()


@router.post("/chat")
async def chat(request: ChatRequest):
    system_prompt = {
        "role": "system",
        "content": (
            "You are AETHER, an AI desktop assistant. "
            "You address the user as 'Sir'. "
            "You are professional, warm, and intelligent. "
            "Never use emojis. Be concise but thorough. "
            "You can help with conversation, desktop automation, file operations, and more."
        )
    }
    messages = [system_prompt, {"role": "user", "content": request.message}]

    response_content = ""
    async for chunk in llm.generate(messages, stream=False):
        response_content += chunk

    await memory_store.save_memory(
        f"User: {request.message}\nAssistant: {response_content}",
        "conversation",
    )

    return {
        "response": response_content,
        "conversation_id": request.conversation_id or "",
    }


@router.post("/automation/launch")
async def launch_app(request: LaunchAppRequest):
    result = await automation_service.launch_app(request.name)
    return result


@router.post("/automation/close")
async def close_app(request: CloseAppRequest):
    result = await automation_service.close_app(request.name)
    return result


@router.get("/files")
async def list_files(path: str = "."):
    result = await file_service.list_directory(path)
    return result


@router.get("/files/read")
async def read_file(path: str):
    result = await file_service.read_file(path)
    return result


@router.get("/plugins")
async def get_plugins():
    return plugin_manager.get_all_plugins()


@router.post("/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, request: PluginToggleRequest):
    if request.enabled:
        plugin_manager.enable(plugin_id)
    else:
        plugin_manager.disable(plugin_id)
    return {"success": True}


@router.get("/memory/search")
async def search_memory(q: str):
    results = await memory_store.search_memories(q)
    return results


@router.get("/system/metrics")
async def get_system_metrics():
    from app.services.system_monitor import SystemMonitorService
    monitor = SystemMonitorService()
    return monitor.get_metrics()
