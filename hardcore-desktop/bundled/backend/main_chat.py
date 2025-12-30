from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ai import GeminiAI
from hal_adapter import HALAdapter
from firmware_gen import FirmwareGeneratorAI
from database import init_db
import auth

app = FastAPI(title="Hardcore.ai Orchestrator")

# Initialize Database
init_db()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth Router
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Chat endpoint models
class ChatRequest(BaseModel):
    message: str
    board_type: str = "esp32"
    current_code: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    code: Optional[str] = None
    diff: Optional[List[Dict[str, Any]]] = None
    wiring: Optional[List[Dict[str, str]]] = None

# Existing models
class HardwareCommandRequest(BaseModel):
    prompt: str
    board_type: str = "esp32"
    board_netlist: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Hardcore.ai Orchestrator"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: auth.User = Depends(auth.get_current_user)
):
    """
    Conversational AI endpoint for chat-based code generation.
    """
    try:
        # Initialize AI
        ai = GeminiAI()
        firmware_gen = FirmwareGeneratorAI()
        hal = HALAdapter()
        
        # Parse user intent
        action = ai.parse_hardware_command(request.message, request.board_type)
        
        # Resolve pins
        resolved_pins = hal.resolve_pins(action, request.board_type)
        
        # Generate firmware
        code = firmware_gen.generate_firmware(action, resolved_pins, request.board_type)
        
        # Create AI response message
        ai_message = f"I've generated code for your request: '{request.message}'\n\n"
        
        if action.get('action') == 'blink':
            ai_message += f"Added LED blinking on pin {resolved_pins.get('LED', 2)} with {action['params'].get('interval_ms', 1000)}ms interval."
        elif action.get('action') == 'read_sensor':
            sensor = action['params'].get('sensor_type', 'DHT11')
            ai_message += f"Set up {sensor} sensor reading on pin {resolved_pins.get('DATA', 4)}."
        elif action.get('action') == 'servo_sweep':
            ai_message += f"Added servo control on pin {resolved_pins.get('SERVO', 13)}."
        else:
            ai_message += "Generated custom code based on your request."
        
        # Calculate diff (simple line-based for now)
        diff = []
        if request.current_code:
            old_lines = request.current_code.split('\n')
            new_lines = code.split('\n')
            
            # Find changed lines (simplified)
            for i, (old, new) in enumerate(zip(old_lines, new_lines)):
                if old != new:
                    diff.append({
                        "type": "modification",
                        "startLine": i + 1,
                        "endLine": i + 1,
                        "content": new
                    })
            
            # Handle added lines
            if len(new_lines) > len(old_lines):
                for i in range(len(old_lines), len(new_lines)):
                    diff.append({
                        "type": "addition",
                        "startLine": i + 1,
                        "endLine": i + 1,
                        "content": new_lines[i]
                    })
        
        return ChatResponse(
            message=ai_message,
            code=code,
            diff=diff if diff else None,
            wiring=action.get('wiring')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# Keep existing endpoints...
@app.post("/execute")
async def execute_hardware_command(
    request: HardwareCommandRequest,
    current_user: auth.User = Depends(auth.get_current_user)
):
    """Main orchestrator endpoint - takes natural language and executes full workflow."""
    try:
        ai = GeminiAI()
        firmware_gen = FirmwareGeneratorAI()
        hal = HALAdapter()
        
        action = ai.parse_hardware_command(request.prompt, request.board_type)
        resolved_pins = hal.resolve_pins(action, request.board_type)
        code = firmware_gen.generate_firmware(action, resolved_pins, request.board_type)
        
        return {
            "action": action,
            "resolved_pins": resolved_pins,
            "firmware_code": code,
            "board_type": request.board_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... rest of existing endpoints (build, flash, boards, etc.) ...
