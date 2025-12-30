# Chat Endpoint Enhancement - Add to main.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pin_mapper import IntelligentPinMapper

# Initialize pin mapper
pin_mapper = IntelligentPinMapper()

class ChatRequest(BaseModel):
    message: str
    board_type: str = "esp32"
    current_code: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    code: Optional[str] = None
    wiring: Optional[List[Dict[str, str]]] = None
    pin_assignments: Optional[Dict[str, int]] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: auth.User = Depends(auth.get_current_user)
):
    """
    Enhanced conversational AI endpoint with intelligent pin assignment
    """
    try:
        # Initialize components
        ai = GeminiAI()
        firmware_gen = FirmwareGeneratorAI()
        hal = HALAdapter()
        
        # Parse user intent
        action = ai.parse_hardware_command(request.message, request.board_type)
        
        # ENHANCEMENT: Use intelligent pin mapper
        peripheral_type = action.get('action', 'custom')
        requirements = action.get('params', {})
        
        # Auto-assign optimal pins
        auto_pins = pin_mapper.auto_assign_pins(
            request.board_type,
            peripheral_type,
            requirements
        )
        
        # Merge with AI-suggested pins (AI pins take priority if specified)
        resolved_pins = {**auto_pins, **hal.resolve_pins(action, request.board_type)}
        
        # Generate firmware with intelligent pins
        code = firmware_gen.generate_firmware(action, resolved_pins, request.board_type)
        
        # Create enhanced AI response message
        ai_message = self._create_ai_message(action, resolved_pins, request.board_type)
        
        # Get pin usage map for visualization
        pin_usage = pin_mapper.get_pin_usage_map(request.board_type)
        
        return ChatResponse(
            message=ai_message,
            code=code,
            wiring=action.get('wiring'),
            pin_assignments={
                'assigned': resolved_pins,
                'conflicts': pin_usage.get('conflicts', []),
                'available': pin_usage.get('available_pins', [])[:10]  # Show first 10
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

def _create_ai_message(action: Dict, pins: Dict, board_type: str) -> str:
    """Create intelligent AI response message"""
    action_type = action.get('action', 'custom')
    
    messages = {
        'blink': f"✅ Added LED blinking on pin {pins.get('LED', 2)}",
        'read_sensor': f"✅ Set up {action['params'].get('sensor_type', 'sensor')} on pin {pins.get('DATA', 4)}",
        'servo_sweep': f"✅ Added servo control on PWM pin {pins.get('SERVO', 13)}",
        'i2c': f"✅ Configured I2C: SDA={pins.get('SDA')}, SCL={pins.get('SCL')}",
        'spi': f"✅ Configured SPI: MOSI={pins.get('MOSI')}, MISO={pins.get('MISO')}, SCK={pins.get('SCK')}",
    }
    
    base_message = messages.get(action_type, "✅ Generated custom code")
    
    # Add pin conflict warnings if any
    conflicts = pin_mapper.detect_conflicts(board_type)
    if conflicts:
        base_message += f"\n\n⚠️ Warning: {len(conflicts)} pin conflict(s) detected"
    
    return base_message
