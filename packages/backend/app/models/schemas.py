from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class LaunchAppRequest(BaseModel):
    name: str


class CloseAppRequest(BaseModel):
    name: str


class FileReadRequest(BaseModel):
    path: str


class PluginToggleRequest(BaseModel):
    enabled: bool


class SystemMetrics(BaseModel):
    cpu: dict
    gpu: dict
    ram: dict
    disk: dict
    battery: dict
    network: dict
    model: dict


class MemorySearchResult(BaseModel):
    id: str
    content: str
    type: str
    timestamp: float
    similarity: float
