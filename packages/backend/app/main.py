import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.api.websocket import ConnectionManager
from app.core.config import settings
from app.services.system_monitor import SystemMonitorService
from app.memory.store import MemoryStore


manager = ConnectionManager()
system_monitor = SystemMonitorService()
memory_store = MemoryStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AETHER backend starting...")
    await memory_store.initialize()
    monitor_task = asyncio.create_task(system_monitor.start(manager))
    yield
    monitor_task.cancel()
    await memory_store.close()
    logger.info("AETHER backend stopped.")


app = FastAPI(
    title="AETHER API",
    description="The Intelligence Behind Your Computer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "name": "AETHER", "version": "0.1.0"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
