from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.websockets import WebSocketState
from typing import List, Dict
import json
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "buyer": [],
            "seller": []
        }
        self.chat_history: List[dict] = []

    async def connect(self, websocket: WebSocket, client_type: str):
        if client_type not in self.active_connections:
            raise ValueError("Invalid client type")
            
        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.accept()

        self.active_connections[client_type].append(websocket)
        await self.send_chat_history(websocket)

    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type in self.active_connections:
            if websocket in self.active_connections[client_type]:
                self.active_connections[client_type].remove(websocket)

    async def broadcast(self, message: dict):
        message["timestamp"] = datetime.now().isoformat()
        self.chat_history.append(message)

        if len(self.chat_history) > 100:
            self.chat_history = self.chat_history[-100:]

        message_str = json.dumps(message)

        for client_type, connections in self.active_connections.items():
            for connection in connections[:]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_text(message_str)
                except WebSocketDisconnect:
                    self.disconnect(connection, client_type)
                except Exception as e:
                    print(f"Error broadcasting to {client_type}: {str(e)}")
                    self.disconnect(connection, client_type)

    async def send_chat_history(self, websocket: WebSocket):
        try:
            for message in self.chat_history[-50:]: 
                await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending chat history: {str(e)}")

manager = ConnectionManager()

def setup_websocket_routes(app):
    @app.websocket("/ws/buyer")
    async def websocket_buyer_endpoint(websocket: WebSocket):
        await manager.connect(websocket, "buyer")
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    message["sender"] = "buyer"
                    await manager.broadcast(message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid message format",
                        "timestamp": datetime.now().isoformat()
                    })
        except WebSocketDisconnect:
            manager.disconnect(websocket, "buyer")
        except Exception as e:
            print(f"Buyer WebSocket error: {str(e)}")
            manager.disconnect(websocket, "buyer")

    @app.websocket("/ws/seller")
    async def websocket_seller_endpoint(websocket: WebSocket):
        await manager.connect(websocket, "seller")
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    message["sender"] = "seller"
                    await manager.broadcast(message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid message format",
                        "timestamp": datetime.now().isoformat()
                    })
        except WebSocketDisconnect:
            manager.disconnect(websocket, "seller")
        except Exception as e:
            print(f"Seller WebSocket error: {str(e)}")
            manager.disconnect(websocket, "seller")
