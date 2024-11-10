from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from starlette.websockets import WebSocketDisconnect

from main.Self_healing.bd_schema import Selector, HealingReport

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process received data and broadcast updates
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.active_connections.remove(websocket)

# REST endpoints for initial data load
@app.get("/api/selectors")
async def get_selectors():
    with Session() as session:
        selectors = session.query(Selector).all()
        return selectors

@app.get("/api/healing-reports")
async def get_healing_reports():
    with Session() as session:
        reports = session.query(HealingReport).all()
        return reports