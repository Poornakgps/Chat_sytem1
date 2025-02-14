# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import json
from typing import List
from datetime import datetime
from fastapi import HTTPException
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
def create_tables():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Buyer chat table - Add payment_status
    c.execute('''CREATE TABLE IF NOT EXISTS buyer_chat
                 (chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT NOT NULL,
                  file_name TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  is_bargain BOOLEAN DEFAULT FALSE,
                  bargain_amount FLOAT,
                  payment_status TEXT DEFAULT 'pending')''')
    
    # Seller chat table - Add payment_qr_code
    c.execute('''CREATE TABLE IF NOT EXISTS seller_chat
                 (chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT NOT NULL,
                  file_name TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  order_status TEXT,
                  bargain_status TEXT,
                  payment_status TEXT,
                  payment_qr_code TEXT,
                  tracking_number TEXT)''')
    
    conn.commit()
    conn.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Include routers
from buyerq import buyer_router
from seller1 import seller_router

app.include_router(buyer_router)
app.include_router(seller_router)

@app.websocket("/ws/buyer")
async def websocket_buyer_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/seller")
async def websocket_seller_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        
@app.post("/remove_file")
async def remove_file(file_data: dict):
    file_name = file_data.get("file_name")
    if not file_name:
        raise HTTPException(status_code=400, detail="File name is required")
    
    file_path = f"static/uploads/{file_name}"
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"message": "File removed successfully"}
        return {"message": "File not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat_history")
async def get_chat_history():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    try:
        # Get buyer messages
        c.execute('''SELECT message, file_name, timestamp, 'buyer' as sender, 
                    CASE WHEN is_bargain THEN 'bargain' ELSE NULL END as type,
                    bargain_amount as amount
                    FROM buyer_chat 
                    ORDER BY timestamp''')
        buyer_messages = c.fetchall()
        
        # Get seller messages
        c.execute('''SELECT message, file_name, timestamp, 'seller' as sender,
                    order_status, tracking_number,
                    bargain_status as type,
                    CASE WHEN bargain_status = 'approved' THEN 
                        (SELECT bargain_amount FROM buyer_chat WHERE is_bargain = TRUE 
                         ORDER BY timestamp DESC LIMIT 1)
                    ELSE NULL END as amount
                    FROM seller_chat 
                    ORDER BY timestamp''')
        seller_messages = c.fetchall()
        
        # Combine and sort messages
        all_messages = []
        for msg in buyer_messages + seller_messages:
            message_dict = {
                'message': msg[0],
                'file_name': msg[1],
                'timestamp': msg[2],
                'sender': msg[3]
            }
            
            if msg[4]:  # If it's a special message type (bargain/status)
                message_dict['type'] = msg[4]
                if msg[5]:  # Additional data like tracking number or amount
                    if msg[4] == 'bargain':
                        message_dict['amount'] = msg[5]
                    else:
                        message_dict['tracking'] = msg[5]
            
            all_messages.append(message_dict)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x['timestamp'])
        return all_messages
        
    finally:
        conn.close()

@app.post("/api/clear_chat")
async def clear_chat():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    try:
        # Get all file names before clearing
        c.execute("SELECT file_name FROM buyer_chat WHERE file_name IS NOT NULL")
        buyer_files = c.fetchall()
        c.execute("SELECT file_name FROM seller_chat WHERE file_name IS NOT NULL")
        seller_files = c.fetchall()
        
        # Clear database tables
        c.execute("DELETE FROM buyer_chat")
        c.execute("DELETE FROM seller_chat")
        conn.commit()
        
        # Delete associated files
        for file_tuple in buyer_files + seller_files:
            file_name = file_tuple[0]
            if file_name:
                file_path = f"static/uploads/{file_name}"
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_name}: {e}")
        
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()