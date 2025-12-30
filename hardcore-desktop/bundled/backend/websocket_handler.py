# WebSocket Support for Real-time AI Streaming
# Add to main.py for live code updates

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time AI streaming
    """
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message
            message = data.get('message', '')
            board_type = data.get('board_type', 'esp32')
            
            # Send acknowledgment
            await manager.send_message(session_id, {
                'type': 'ack',
                'message': 'Processing your request...'
            })
            
            # Initialize components
            ai = GeminiAI()
            firmware_gen = FirmwareGeneratorAI()
            
            # Parse command
            action = ai.parse_hardware_command(message, board_type)
            
            # Send progress update
            await manager.send_message(session_id, {
                'type': 'progress',
                'message': 'Assigning pins...'
            })
            
            # Auto-assign pins
            peripheral_type = action.get('action', 'custom')
            auto_pins = pin_mapper.auto_assign_pins(board_type, peripheral_type, {})
            
            # Send progress update
            await manager.send_message(session_id, {
                'type': 'progress',
                'message': 'Generating code...'
            })
            
            # Generate firmware
            code = firmware_gen.generate_firmware(action, auto_pins, board_type)
            
            # Send final response
            await manager.send_message(session_id, {
                'type': 'complete',
                'code': code,
                'pins': auto_pins,
                'wiring': action.get('wiring', []),
                'message': f'✅ Code generated successfully!'
            })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_message(session_id, {
            'type': 'error',
            'message': f'Error: {str(e)}'
        })
        manager.disconnect(session_id)
