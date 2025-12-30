# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import shutil
import traceback
import os
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ai import StrictGeminiEngine, GeminiError
from context_loader import ProjectContextLoader
from hal_adapter import IntelligentHAL
from firmware_gen import FirmwareAssembler
from database import init_db
from pin_mapper import IntelligentPinMapper
from project_templates import ProjectTemplates
import auth

app = FastAPI(title="Hardcore.ai Orchestrator")

# Initialize Database
init_db()

# Initialize Intelligent Pin Mapper
pin_mapper = IntelligentPinMapper()

# Initialize Project Templates
project_templates = ProjectTemplates()

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

class HardwareCommandRequest(BaseModel):
    prompt: str
    board_type: str = "unknown"
    board_netlist: Optional[Dict[str, Any]] = None
    project_id: str = "current_project"  # Added for context isolation
    # NEW: Structured peripheral config from UI (like STM32CubeMX)
    peripheral_config: Optional[Dict[str, Any]] = None
    # NEW: Detected board from USB detection (source of truth if present)
    detected_board: Optional[str] = None
    detected_port: Optional[str] = None

# Global context loader instance (persists across requests)
_context_loader = ProjectContextLoader()

# Global API key storage (set by user via settings)
_user_api_key: Optional[str] = None

class ApiKeyRequest(BaseModel):
    api_key: str

@app.post("/settings/api-key")
async def set_api_key(request: ApiKeyRequest):
    """
    Set the Gemini API key from user settings.
    This allows users to provide their own API key.
    """
    global _user_api_key
    _user_api_key = request.api_key
    print(f"[Settings] API key updated (length: {len(request.api_key)})")
    return {"status": "success", "message": "API key saved"}

@app.get("/settings/api-key/status")
async def get_api_key_status():
    """Check if an API key is configured."""
    global _user_api_key
    has_key = bool(_user_api_key) or bool(os.getenv("LLM_API_KEY"))
    return {"configured": has_key}

def get_active_api_key() -> Optional[str]:
    """Get the active API key (user-provided or env)."""
    global _user_api_key
    return _user_api_key or os.getenv("LLM_API_KEY")

# =====================================================
# INTENT GATE AND STATE MACHINE (CRITICAL)
# =====================================================
# This prevents code generation on greetings/small talk

class ChatRequest(BaseModel):
    """Request model for AI chat - separate from code generation."""
    message: str
    project_id: str = "current_project"
    board_type: str = "unknown"
    detected_board: Optional[str] = None

class ConversationState:
    """In-memory conversation state manager."""
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
    
    def get(self, project_id: str) -> Dict[str, Any]:
        if project_id not in self.states:
            self.states[project_id] = {
                "state": "IDLE",  # IDLE, CLARIFYING, READY, GENERATING
                "pending_request": None,  # Original build request
                "board": None,
                "driver": None,
                "pins": {},
                "behavior": None,
                "last_question": None,
            }
        return self.states[project_id]
    
    def update(self, project_id: str, **kwargs):
        state = self.get(project_id)
        state.update(kwargs)
        return state
    
    def reset(self, project_id: str):
        self.states[project_id] = {
            "state": "IDLE",
            "pending_request": None,
            "board": None,
            "driver": None,
            "pins": {},
            "behavior": None,
            "last_question": None,
        }

# Global conversation state
_conversation_state = ConversationState()

def classify_intent(message: str, current_state: str) -> str:
    """
    Classify user message intent.
    
    Returns:
    - SMALL_TALK: greetings, chitchat (NO code)
    - CLARIFICATION: answering a previous question
    - BUILD_INTENT: wants to build/control hardware
    - CONFIRMATION: "yes", "proceed", "generate"
    """
    msg = message.lower().strip()
    
    # CONFIRMATION patterns (when in READY state)
    if current_state == "READY":
        confirmation_words = ["yes", "yeah", "yep", "proceed", "generate", "ok", "okay", "sure", "go ahead", "do it", "confirm"]
        if any(word in msg for word in confirmation_words):
            return "CONFIRMATION"
    
    # Small talk / greetings (NO code generation)
    small_talk_patterns = [
        "hi", "hello", "hey", "howdy", "greetings",
        "how are you", "what's up", "sup", "yo",
        "good morning", "good afternoon", "good evening",
        "thanks", "thank you", "bye", "goodbye",
        "who are you", "what are you", "help me"
    ]
    if msg in small_talk_patterns or any(msg.startswith(p) for p in ["hi ", "hello ", "hey "]):
        return "SMALL_TALK"
    
    # If we're in CLARIFYING state, treat as answer
    if current_state == "CLARIFYING":
        return "CLARIFICATION"
    
    # Build intent patterns
    build_keywords = [
        "make", "build", "create", "control", "move", "drive", "spin",
        "blink", "flash", "read", "write", "connect", "setup", "configure",
        "motor", "led", "sensor", "servo", "display", "robot", "car",
        "forward", "backward", "left", "right", "stop", "start"
    ]
    if any(kw in msg for kw in build_keywords):
        return "BUILD_INTENT"
    
    # Default to small talk for safety (NO code)
    return "SMALL_TALK"

def generate_small_talk_response(message: str) -> str:
    """Generate friendly response without any code."""
    msg = message.lower().strip()
    if msg in ["hi", "hello", "hey"]:
        return "Hello! I'm HardcoreAI, your embedded systems copilot. What would you like to build today?"
    if "how are you" in msg:
        return "I'm ready to help you build amazing hardware projects! What would you like to create?"
    if "thank" in msg:
        return "You're welcome! Let me know if you need anything else."
    if "help" in msg:
        return "I can help you generate firmware for ESP32, Arduino, STM32, and more. Just describe what you want to build - for example: 'Make a robot move forward' or 'Blink an LED on GPIO 2'."
    return "I'm here to help you build hardware projects. Describe what you'd like to create, and I'll generate the firmware for you."

def generate_clarification_question(context: Dict[str, Any]) -> str:
    """Generate a clarification question based on missing context."""
    if not context.get("board"):
        return "What board are you using? (ESP32, Arduino, STM32, etc.)"
    if not context.get("driver") and "motor" in context.get("pending_request", "").lower():
        return "What motor driver are you using? (L298N, L293D, DRV8833, etc.)"
    if not context.get("behavior"):
        return "Can you describe the behavior in more detail? (timing, sequence, etc.)"
    return None

@app.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user: auth.User = Depends(auth.get_current_user_optional)
):
    """
    AI Chat endpoint with Intent Gate.
    
    CRITICAL: This endpoint NEVER generates code unless:
    1. User expresses BUILD_INTENT
    2. Clarification is complete
    3. User CONFIRMS generation
    
    response_type: "text" | "clarification" | "code"
    """
    try:
        print(f"\n[Chat] ===== CHAT REQUEST =====")
        print(f"[Chat] Message: {request.message}")
        print(f"[Chat] Project: {request.project_id}")
        
        # Get current conversation state
        ctx = _conversation_state.get(request.project_id)
        current_state = ctx["state"]
        print(f"[Chat] Current State: {current_state}")
        
        # Classify intent
        intent = classify_intent(request.message, current_state)
        print(f"[Chat] Intent: {intent}")
        
        # ===== SMALL TALK =====
        if intent == "SMALL_TALK":
            response = generate_small_talk_response(request.message)
            return {
                "status": "success",
                "response_type": "text",
                "message": response,
                "state": current_state,
            }
        
        # ===== CLARIFICATION (answering a question) =====
        if intent == "CLARIFICATION":
            # Update context with answer
            msg = request.message.lower()
            
            # Detect board from answer
            if "esp32" in msg:
                _conversation_state.update(request.project_id, board="esp32dev")
            elif "arduino" in msg:
                _conversation_state.update(request.project_id, board="arduino_uno")
            elif "stm32" in msg:
                _conversation_state.update(request.project_id, board="stm32")
            
            # Detect driver
            if "l298" in msg:
                _conversation_state.update(request.project_id, driver="L298N")
            elif "l293" in msg:
                _conversation_state.update(request.project_id, driver="L293D")
            
            # Check if we have enough info
            ctx = _conversation_state.get(request.project_id)
            next_question = generate_clarification_question(ctx)
            
            if next_question:
                _conversation_state.update(request.project_id, last_question=next_question)
                return {
                    "status": "success",
                    "response_type": "clarification",
                    "message": next_question,
                    "state": "CLARIFYING",
                }
            else:
                # Ready for confirmation
                _conversation_state.update(request.project_id, state="READY")
                summary = f"I'll generate firmware for:\n• Board: {ctx.get('board', 'ESP32')}\n• Driver: {ctx.get('driver', 'default')}\n• Behavior: {ctx.get('pending_request', 'as requested')}\n\nProceed with code generation?"
                return {
                    "status": "success",
                    "response_type": "clarification",
                    "message": summary,
                    "state": "READY",
                }
        
        # ===== BUILD INTENT =====
        if intent == "BUILD_INTENT":
            # Store the request, move to CLARIFYING
            _conversation_state.update(
                request.project_id,
                state="CLARIFYING",
                pending_request=request.message,
                board=request.detected_board or request.board_type if request.board_type != "unknown" else None
            )
            
            ctx = _conversation_state.get(request.project_id)
            next_question = generate_clarification_question(ctx)
            
            if next_question:
                _conversation_state.update(request.project_id, last_question=next_question)
                return {
                    "status": "success",
                    "response_type": "clarification",
                    "message": next_question,
                    "state": "CLARIFYING",
                }
            else:
                # Have enough info, ask for confirmation
                _conversation_state.update(request.project_id, state="READY")
                summary = f"I'll generate firmware for:\n• Board: {ctx.get('board', 'ESP32')}\n• Behavior: {request.message}\n\nProceed with code generation?"
                return {
                    "status": "success",
                    "response_type": "clarification",
                    "message": summary,
                    "state": "READY",
                }
        
        # ===== CONFIRMATION - GENERATE CODE =====
        if intent == "CONFIRMATION":
            ctx = _conversation_state.get(request.project_id)
            pending = ctx.get("pending_request", "LED blink example")
            board = ctx.get("board", "esp32dev")
            
            print(f"[Chat] CONFIRMED - Generating firmware")
            print(f"[Chat] Request: {pending}")
            print(f"[Chat] Board: {board}")
            
            # Now actually generate code
            _conversation_state.update(request.project_id, state="GENERATING")
            
            try:
                ai_engine = StrictGeminiEngine()
                firmware_package = ai_engine.generate_firmware(
                    user_request=pending,
                    board_type=board,
                    project_id=request.project_id
                )
                
                # Validate and assemble
                hal = IntelligentHAL(board)
                resolved_pins, _ = hal.validate_and_resolve(firmware_package.pin_json)
                
                assembler = FirmwareAssembler()
                compiled = assembler.assemble(
                    firmware_package=firmware_package.to_dict(),
                    board_type=board,
                    resolved_pins=resolved_pins
                )
                
                # Reset state
                _conversation_state.reset(request.project_id)
                
                return {
                    "status": "success",
                    "response_type": "code",
                    "message": "Firmware generated successfully!",
                    "firmware": compiled.main_cpp,
                    "pin_block": firmware_package.pin_block,
                    "state": "IDLE",
                }
                
            except Exception as e:
                _conversation_state.update(request.project_id, state="READY")
                return {
                    "status": "error",
                    "response_type": "text",
                    "message": f"Generation failed: {str(e)}. Try again?",
                    "state": "READY",
                }
        
        # Default fallback
        return {
            "status": "success",
            "response_type": "text",
            "message": "I'm not sure what you'd like to do. Try describing what you want to build, like 'Make a robot move forward' or 'Blink an LED'.",
            "state": current_state,
        }
        
    except Exception as e:
        print(f"[Chat] ERROR: {e}")
        return {
            "status": "error",
            "response_type": "text",
            "message": f"Sorry, something went wrong. Please try again.",
            "state": "IDLE",
        }

@app.post("/execute")
async def execute_hardware_command(
    request: HardwareCommandRequest,
    current_user: auth.User = Depends(auth.get_current_user_optional)
):
    """
    AI-first firmware generation endpoint with state machine.
    Injects peripheral config and respects detected board.
    """
    try:
        print(f"\n[Orchestrator] ===== FIRMWARE GENERATION REQUEST =====")
        print(f"[Orchestrator] Prompt: {request.prompt}")
        print(f"[Orchestrator] Board (API): {request.board_type}")
        print(f"[Orchestrator] Detected Board: {request.detected_board}")
        print(f"[Orchestrator] Detected Port: {request.detected_port}")
        print(f"[Orchestrator] Project ID: {request.project_id}")
        print(f"[Orchestrator] Has Peripheral Config: {request.peripheral_config is not None}")

        # ===== BOARD SOURCE OF TRUTH =====
        # Priority: detected_board > board_type from API > "unknown"
        effective_board = (
            request.detected_board 
            or (request.board_type if request.board_type not in ('unknown', 'none', '') else None)
            or 'esp32dev'  # Safe default
        )
        print(f"[Orchestrator] Effective Board: {effective_board}")

        # ===== BUILD ENHANCED PROMPT =====
        enhanced_prompt = request.prompt

        # Inject peripheral config if provided
        if request.peripheral_config:
            peripheral_section = _format_peripheral_config(request.peripheral_config)
            enhanced_prompt = f"{peripheral_section}\n\n{request.prompt}"
            print(f"[Orchestrator] Injected peripheral config into prompt")

        # Initialize Engine
        ai_engine = StrictGeminiEngine()

        # ===== AI GENERATION =====
        print(f"\n[Orchestrator] STAGE 1: AI Generation")
        firmware_package = ai_engine.generate_firmware(
            user_request=enhanced_prompt,
            board_type=effective_board,
            project_id=request.project_id
        )

        print(f"[Orchestrator]   ✓ Firmware generated successfully")
        print(f"[Orchestrator]   Model: {firmware_package.model_used}")
        print(f"[Orchestrator]   Confidence: {firmware_package.confidence}")

        # ===== STAGE 2: HAL VALIDATION =====
        print(f"\n[Orchestrator] STAGE 2: HAL Pin Validation")
        hal = IntelligentHAL(effective_board)
        resolved_pins, validation_issues = hal.validate_and_resolve(firmware_package.pin_json)

        # ===== STAGE 3: FIRMWARE ASSEMBLY =====
        print(f"\n[Orchestrator] STAGE 3: Firmware Assembly")
        assembler = FirmwareAssembler()
        compiled_firmware = assembler.assemble(
            firmware_package=firmware_package.to_dict(),
            board_type=effective_board,
            resolved_pins=resolved_pins
        )

        # Guardrail: never claim success without actual code
        if not compiled_firmware.main_cpp or len(compiled_firmware.main_cpp.strip()) < 50:
            print("[Orchestrator] Assembly produced empty/too-short firmware")
            return {
                "status": "error",
                "message": "Firmware generation failed internal validation. Please try rephrasing your request.",
                "is_chat": True,
                "firmware": None,
            }

        # ===== STAGE 4: RESPONSE =====
        print(f"\n[Orchestrator] STAGE 4: Final Response")

        api_response = {
            "status": "success",
            "firmware": compiled_firmware.main_cpp,
            "platformio_ini": compiled_firmware.platformio_ini,
            "pin_block": firmware_package.pin_block,
            "pin_json": firmware_package.pin_json,
            "resolved_pins": resolved_pins,
            "timeline": firmware_package.timeline,
            "tests": firmware_package.tests,
            "message": "Firmware Generated Successfully",
            "is_chat": False,
            "board_used": effective_board,
        }

        # Save to isolated project workspace
        _save_to_workspace(compiled_firmware, effective_board, request.project_id)

        # Save to history for context persistence
        _context_loader.save_history(request.project_id, request.prompt, firmware_package.to_dict())

        return api_response


    except GeminiError as e:
        # Gemini-specific error - return HTTP 503 with structured error
        print(f"[Orchestrator]   GEMINI ERROR: {e.error_code}")
        print(f"[Orchestrator]   Message: {e.message}")
        print(f"[Orchestrator]   Attempts: {len(e.attempts)}")

        # Build structured error response
        error_response = {
            "status": "error",
            "error_code": e.error_code,
            "message": e.message,
            "metadata": {
                "attempts": [
                    {
                        "model": a.model,
                        "status": a.status_code,
                        "latency_ms": a.latency_ms,
                        "error_snippet": a.error_snippet,
                        "success": a.success
                    } for a in e.attempts
                ],
                "timestamp": datetime.now().isoformat()
            }
        }

        # Determine specific remediation message
        if e.error_code == "MODEL_NOT_SUPPORTED":
            error_response["remediation"] = "Check API key or update GEMINI_MODEL_WHITELIST environment variable"
        elif e.error_code == "RATE_LIMITED":
            error_response["remediation"] = "Wait 60 seconds before retrying. Consider upgrading API quota."
        elif e.error_code == "LLM_UNAVAILABLE":
            error_response["remediation"] = "Verify API key is valid and has quota. Check Gemini API status."
        elif e.error_code == "VALIDATION_FAILED":
            error_response["remediation"] = "Gemini output was incomplete. Try rephrasing your request or try again."

        raise HTTPException(status_code=503, detail=error_response)

    except Exception as e:
        # Unexpected error
        import traceback
        error_trace = traceback.format_exc()

        print(f"[Orchestrator]  UNEXPECTED ERROR: {e}")
        print(f"[Orchestrator] Traceback:\n{error_trace}")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(e),
                "type": type(e).__name__,
                "trace": error_trace[:500]
            }
        )

def _format_peripheral_config(config: Dict[str, Any]) -> str:
    """
    Convert structured peripheral config (from UI) to AI-readable prompt section.
    This is the bridge between the STM32CubeMX-style UI and the AI engine.
    """
    lines = ["=== PERIPHERAL CONFIGURATION (FROM UI) ==="]
    lines.append("The user has configured the following peripherals. Use these EXACT settings.")
    lines.append("")
    
    # GPIO
    gpio = config.get("gpio", [])
    if gpio:
        lines.append("GPIO PINS:")
        for g in gpio:
            pin = g.get("pin", 0)
            mode = g.get("mode", "OUTPUT")
            label = g.get("label", "")
            lines.append(f"  - GPIO {pin}: {mode}" + (f" ({label})" if label else ""))
    
    # I2C
    i2c = config.get("i2c", [])
    if i2c:
        lines.append("\nI2C DEVICES:")
        for d in i2c:
            name = d.get("name", "Device")
            addr = d.get("address", "0x00")
            sda = d.get("sda", 21)
            scl = d.get("scl", 22)
            lines.append(f"  - {name}: Address={addr}, SDA=GPIO{sda}, SCL=GPIO{scl}")
    
    # SPI
    spi = config.get("spi", [])
    if spi:
        lines.append("\nSPI DEVICES:")
        for d in spi:
            name = d.get("name", "Device")
            cs = d.get("cs", 5)
            mosi = d.get("mosi", 23)
            miso = d.get("miso", 19)
            sck = d.get("sck", 18)
            lines.append(f"  - {name}: CS=GPIO{cs}, MOSI=GPIO{mosi}, MISO=GPIO{miso}, SCK=GPIO{sck}")
    
    # UART
    uart = config.get("uart", [])
    if uart:
        lines.append("\nUART PORTS:")
        for u in uart:
            name = u.get("name", "UART")
            tx = u.get("tx", 17)
            rx = u.get("rx", 16)
            baud = u.get("baud", 115200)
            lines.append(f"  - {name}: TX=GPIO{tx}, RX=GPIO{rx}, Baud={baud}")
    
    # Timers
    timers = config.get("timers", [])
    if timers:
        lines.append("\nTIMERS:")
        for t in timers:
            name = t.get("name", "Timer")
            interval = t.get("interval", 1000)
            unit = t.get("unit", "ms")
            lines.append(f"  - {name}: {interval}{unit} interval")
    
    # Clock
    clock = config.get("clock", {})
    if clock:
        freq = clock.get("frequency", 240)
        lines.append(f"\nCPU CLOCK: {freq} MHz")
    
    lines.append("\n=== END PERIPHERAL CONFIGURATION ===")
    lines.append("Generate code using these EXACT pin assignments. Do NOT change pins.")
    
    return "\n".join(lines)

def _generate_user_message(package, issues) -> str:
    """Generate helpful user-facing message."""
    msg = "Firmware generated successfully"
    if package.context_used:
        msg += " (using project context)"
    if issues:
        critical = sum(1 for i in issues if i.severity == "critical")
        if critical > 0:
            msg += f". Auto-fixed {critical} critical pin issues"
    if hasattr(package, 'pin_json') and package.pin_json.get('auto_extracted'):
        msg += ". Auto-extracted pins from code"
    return msg

def _save_to_workspace(firmware, board_type: str, project_id: str):
    """Save generated files to project-specific workspace."""
    from pathlib import Path
    from platformio_builder import PlatformIOBuilder
    import shutil
    
    builder = PlatformIOBuilder()
    
    # DYNAMIC WORKSPACE PATH
    project_dir = builder.workspace / project_id
    print(f"[Orchestrator] Saving project to: {project_dir}")
    
    # Clean and recreate (Or maybe just ensure exists? Recreating wipes history/mods... 
    # For now, let's stick to current behavior of nuking validation output, 
    # but ContextLoader persists state separately in same folder)
    if project_dir.exists():
        # Careful! We don't want to delete the .hardcore_state.json or history if we're just updating code
        # But previous logic was shutil.rmtree. 
        # Let's keep rmtree for now to align with "Antigravity behavior" of clean generation, 
        # BUT we must preserve state/history if we want AI context to work across turns.
        # Actually, ContextLoader works ON TOP of files. 
        # Ideally we only overwrite source files.
        pass
    else:
        project_dir.mkdir(parents=True, exist_ok=True)
        
    # Initialize PlatformIO structure (idempotent-ish)
    builder._init_platformio_project(project_dir, board_type)
    
    # Write files
    (project_dir / "src" / "main.cpp").write_text(firmware.main_cpp)
    (project_dir / "src" / "resolved_pins.h").write_text(firmware.resolved_pins_h)
    (project_dir / "platformio.ini").write_text(firmware.platformio_ini)
    
    print(f"[Orchestrator] Files saved to {project_dir}")

# --- Remaining endpoints: build / flash / flash stream / ota / boards / drivers / zip download ---
# These endpoints are mostly unchanged from your previous server but are included to maintain compatibility.
# They call into your PlatformIOBuilder, UniversalFlasher, OTAFlasher, WirelessScanner, etc.
# (I kept them minimal here — copy your existing implementations or keep as-is.)

@app.post("/build")
async def build_firmware(
    request: Dict[str, Any],
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        from platformio_builder import PlatformIOBuilder
        builder = PlatformIOBuilder()
        result = builder.build_and_flash(
            firmware_code=request["firmware"],
            board_type=request.get("board_type", "esp32"),
            flash=False
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flash")
async def flash_firmware(
    request: Dict[str, Any],
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        from platformio_builder import PlatformIOBuilder
        builder = PlatformIOBuilder()
        result = builder.build_and_flash(
            firmware_code=request["firmware"],
            board_type=request.get("board_type", "esp32"),
            flash=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flash/stream")
async def flash_firmware_stream(
    request: Dict[str, Any],
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        from platformio_builder import PlatformIOBuilder
        builder = PlatformIOBuilder()
        return StreamingResponse(
            builder.build_and_flash_stream(
                firmware_code=request["firmware"],
                board_type=request.get("board_type", "esp32"),
                flash=True
            ),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flash/universal")
async def flash_universal(
    request: Dict[str, Any],
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        from universal_flasher import UniversalFlasher
        flasher = UniversalFlasher()
        return StreamingResponse(
            flasher.flash(
                firmware_code=request["firmware"],
                board_type=request.get("board_type", "esp32"),
                port=request.get("port")
            ),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flash/ota")
async def flash_ota(
    request: Dict[str, Any],
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        from ota_flasher import OTAFlasher
        from platformio_builder import PlatformIOBuilder
        import os

        firmware_code = request.get("firmware")
        device_ip = request.get("device_ip")
        device_port = request.get("device_port", 3232)
        board_type = request.get("board_type", "esp32")
        ota_password = request.get("ota_password")

        if not device_ip:
            raise HTTPException(status_code=400, detail="device_ip is required")

        builder = PlatformIOBuilder()
        build_result = builder.build_and_flash(firmware_code, board_type, flash=False)

        if not build_result.get("success"):
            raise HTTPException(status_code=500, detail=f"Compilation failed: {build_result.get('error', 'Unknown error')}")

        firmware_bin_path = build_result.get("firmware_path")
        if not firmware_bin_path or not Path(firmware_bin_path).exists():
            raise HTTPException(status_code=500, detail="Compiled firmware file not found")

        ota_flasher = OTAFlasher()

        def generate_ota_status():
            for status in ota_flasher.flash_via_wifi(
                firmware_bin_path=firmware_bin_path,
                device_ip=device_ip,
                port=device_port,
                password=ota_password
            ):
                yield status
        return StreamingResponse(generate_ota_status(), media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTA flash failed: {str(e)}")

@app.get("/boards")
async def detect_boards(
    current_user: auth.User = Depends(auth.get_current_user)
):
    import os
    is_production = os.getenv("RENDER") is not None or os.getenv("VERCEL") is not None
    if is_production:
        return {
            "devices": [],
            "message": "Board detection is not available in production. Please run locally with PlatformIO installed."
        }
    try:
        from platformio_builder import PlatformIOBuilder
        builder = PlatformIOBuilder()
        devices = builder.detect_connected_boards()
        if not devices:
            return {"devices": [], "message": "No boards detected. Make sure your board is connected and drivers are installed."}
        if devices and devices[0].get("error"):
            error_msg = devices[0].get('error', '')
            if 'pio' in error_msg.lower() or 'platformio' in error_msg.lower():
                return {"devices": [], "message": "PlatformIO is not installed. Install it with: pip install platformio"}
            return {"devices": devices, "message": f"Detection issue: {error_msg}"}
        return {"devices": devices}
    except FileNotFoundError as e:
        if 'pio' in str(e).lower():
            return {"devices": [], "message": "PlatformIO is not installed. Please install it with: pip install platformio"}
        raise
    except Exception as e:
        return {"devices": [], "error": str(e), "message": "Failed to detect boards."}

@app.post("/install-drivers")
async def install_drivers_endpoint(
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        import sys
        import subprocess
        script_path = Path("../drivers/install_drivers.py").resolve()
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        return {"status": "success", "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project-files")
async def get_project_files(
    current_user: auth.User = Depends(auth.get_current_user)
):
    try:
        import zipfile
        import io
        from platformio_builder import PlatformIOBuilder

        builder = PlatformIOBuilder()
        project_dir = builder.workspace / "current_project"

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="No project found. Generate firmware first.")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            main_file = project_dir / "src" / "main.cpp"
            if main_file.exists():
                zip_file.write(main_file, "main.cpp")
            ini_file = project_dir / "platformio.ini"
            if ini_file.exists():
                zip_file.write(ini_file, "platformio.ini")
            pins_header = project_dir / "src" / "resolved_pins.h"
            if pins_header.exists():
                zip_file.write(pins_header, "resolved_pins.h")
            src_dir = project_dir / "src"
            if src_dir.exists():
                for header_file in src_dir.glob("*.h"):
                    if header_file.name != "resolved_pins.h":
                        zip_file.write(header_file, header_file.name)
        zip_buffer.seek(0)
        from fastapi.responses import Response
        return Response(content=zip_buffer.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": "attachment; filename=hardcore_project.zip"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project zip: {str(e)}")

@app.get("/board-pinout/{board_type}")
async def get_board_pinout(board_type: str):
    """
    Get pinout layout for visual diagram generation
    Returns pin layout and labels for the specified board
    """
    try:
        from board_pinouts import get_board_pinout
        pinout = get_board_pinout(board_type)
        return pinout
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get board pinout: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
