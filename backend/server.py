from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # For text sessions
        self.text_connections: Dict[str, List[WebSocket]] = {}
        # For stream sessions
        self.stream_connections: Dict[str, Dict] = {}
        
    async def connect_text(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.text_connections:
            self.text_connections[session_id] = []
        self.text_connections[session_id].append(websocket)
        
    def disconnect_text(self, websocket: WebSocket, session_id: str):
        if session_id in self.text_connections:
            if websocket in self.text_connections[session_id]:
                self.text_connections[session_id].remove(websocket)
            if not self.text_connections[session_id]:
                del self.text_connections[session_id]
    
    async def broadcast_text(self, session_id: str, message: dict):
        if session_id in self.text_connections:
            for connection in self.text_connections[session_id].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    self.text_connections[session_id].remove(connection)

    async def connect_stream(self, websocket: WebSocket, session_id: str, user_type: str):
        await websocket.accept()
        if session_id not in self.stream_connections:
            self.stream_connections[session_id] = {
                'broadcaster': None,
                'viewers': []
            }
        
        if user_type == 'broadcaster':
            self.stream_connections[session_id]['broadcaster'] = websocket
        else:
            self.stream_connections[session_id]['viewers'].append(websocket)
    
    def disconnect_stream(self, websocket: WebSocket, session_id: str):
        if session_id in self.stream_connections:
            if self.stream_connections[session_id]['broadcaster'] == websocket:
                self.stream_connections[session_id]['broadcaster'] = None
            elif websocket in self.stream_connections[session_id]['viewers']:
                self.stream_connections[session_id]['viewers'].remove(websocket)
                
            # Clean up empty sessions
            if (not self.stream_connections[session_id]['broadcaster'] and 
                not self.stream_connections[session_id]['viewers']):
                del self.stream_connections[session_id]
    
    async def forward_stream_signal(self, session_id: str, signal: dict, sender: WebSocket):
        if session_id not in self.stream_connections:
            return
            
        connections = self.stream_connections[session_id]
        
        # Forward signals between broadcaster and viewers
        if sender == connections['broadcaster']:
            # Send to all viewers
            for viewer in connections['viewers'].copy():
                try:
                    await viewer.send_text(json.dumps(signal))
                except:
                    connections['viewers'].remove(viewer)
        elif sender in connections['viewers']:
            # Send to broadcaster
            if connections['broadcaster']:
                try:
                    await connections['broadcaster'].send_text(json.dumps(signal))
                except:
                    connections['broadcaster'] = None

manager = ConnectionManager()

# Models
class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    session_type: str  # 'text' or 'stream'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class SessionCreate(BaseModel):
    session_type: str

class TextMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    username: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TextMessageCreate(BaseModel):
    username: str
    message: str

# Helper function to prepare data for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

# Session endpoints
@api_router.post("/sessions", response_model=Session)
async def create_session(session_data: SessionCreate):
    # Generate 6-digit code
    code = str(uuid.uuid4())[:6].upper()
    
    session = Session(
        code=code,
        session_type=session_data.session_type
    )
    
    session_dict = prepare_for_mongo(session.dict())
    await db.sessions.insert_one(session_dict)
    
    return session

@api_router.get("/sessions/{code}", response_model=Session)
async def get_session(code: str):
    session = await db.sessions.find_one({"code": code, "is_active": True})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return Session(**session)

@api_router.delete("/sessions/{code}")
async def close_session(code: str):
    result = await db.sessions.update_one(
        {"code": code},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session closed"}

# Text message endpoints
@api_router.post("/sessions/{session_id}/messages", response_model=TextMessage)
async def send_text_message(session_id: str, message_data: TextMessageCreate):
    message = TextMessage(
        session_id=session_id,
        username=message_data.username,
        message=message_data.message
    )
    
    message_dict = prepare_for_mongo(message.dict())
    await db.text_messages.insert_one(message_dict)
    
    # Broadcast to WebSocket connections
    await manager.broadcast_text(session_id, {
        "type": "message",
        "data": message.dict()
    })
    
    return message

@api_router.get("/sessions/{session_id}/messages", response_model=List[TextMessage])
async def get_text_messages(session_id: str):
    messages = await db.text_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [TextMessage(**message) for message in messages]

# WebSocket endpoints for text sessions
@app.websocket("/ws/text/{session_id}")
async def websocket_text_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect_text(websocket, session_id)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for connection test
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect_text(websocket, session_id)

# WebSocket endpoints for stream sessions  
@app.websocket("/ws/stream/{session_id}/{user_type}")
async def websocket_stream_endpoint(websocket: WebSocket, session_id: str, user_type: str):
    await manager.connect_stream(websocket, session_id, user_type)
    try:
        while True:
            data = await websocket.receive_text()
            signal = json.loads(data)
            await manager.forward_stream_signal(session_id, signal, websocket)
    except WebSocketDisconnect:
        manager.disconnect_stream(websocket, session_id)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()