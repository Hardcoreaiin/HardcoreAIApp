"""
Context Loader - Project Awareness Module
Loads existing project files, conversation history, and board specifications
to provide the AI with full context for intelligent firmware generation.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class ProjectContext:
    """Complete project context for AI reasoning."""
    project_path: Path
    existing_code: Optional[str] = None
    existing_pins: Dict[str, int] = field(default_factory=dict)
    board_type: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    platformio_config: Optional[str] = None
    
    # State Machine Fields
    # conversation_state uses the higher-level lifecycle requested by the app:
    #   IDLE, NEEDS_CLARIFICATION, READY_TO_GENERATE, GENERATING, ERROR_RECOVERABLE
    conversation_state: str = "IDLE"
    last_ai_message_type: str = "FINAL_OUTPUT"  # CLARIFICATION, FINAL_OUTPUT
    pending_request: Optional[str] = None  # The original request being clarified

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_path": str(self.project_path),
            "has_existing_code": self.existing_code is not None,
            "existing_pins": self.existing_pins,
            "board_type": self.board_type,
            "history_length": len(self.conversation_history),
            "components": self.components,
            "state": {
                "conversation_state": self.conversation_state,
                "last_ai_message_type": self.last_ai_message_type,
                "pending_request": self.pending_request
            }
        }

class ProjectContextLoader:
    """
    Loads all relevant project context for AI reasoning.
    Enables the AI to be aware of existing code, pins, and user intent.
    """
    
    def __init__(self, workspace_root: Path = None):
        if workspace_root is None:
            workspace_root = Path(__file__).parent.parent / "workspace"
        self.workspace_root = workspace_root
        print(f"[ContextLoader] Initialized with workspace: {self.workspace_root}")
    
    def load(self, project_id: str = "current_project") -> ProjectContext:
        """
        Load complete project context.
        
        Args:
            project_id: Project identifier (defaults to current_project)
            
        Returns:
            ProjectContext with all available information
        """
        project_path = self.workspace_root / project_id
        
        print(f"[ContextLoader] Loading context for: {project_id}")
        
        context = ProjectContext(project_path=project_path)
        
        # Load existing code if present
        main_cpp = project_path / "src" / "main.cpp"
        if main_cpp.exists():
            print(f"[ContextLoader] Found existing main.cpp")
            context.existing_code = self._load_file(main_cpp)
            context.existing_pins = self._extract_pins_from_code(context.existing_code)
            print(f"[ContextLoader] Extracted {len(context.existing_pins)} pin definitions")
        
        # Load PlatformIO config to detect board
        pio_ini = project_path / "platformio.ini"
        if pio_ini.exists():
            print(f"[ContextLoader] Found platformio.ini")
            context.platformio_config = self._load_file(pio_ini)
            context.board_type = self._detect_board_from_config(context.platformio_config)
        
        # Load conversation history
        history_file = project_path / ".hardcore_history.json"
        if history_file.exists():
            context.conversation_history = self._load_history(history_file)
            print(f"[ContextLoader] Loaded {len(context.conversation_history)} history entries")
            
        # Load conversation state (with Auto-Expiry)
        state_file = project_path / ".hardcore_state.json"
        if state_file.exists():
            state = self._load_state(state_file)
            
            # Check for expiry (1 hour)
            is_expired = False
            updated_at_str = state.get("updated_at")
            if updated_at_str:
                from datetime import datetime, timedelta
                try:
                    last_update = datetime.fromisoformat(updated_at_str)
                    if datetime.now() - last_update > timedelta(hours=1):
                        is_expired = True
                        print(f"[ContextLoader] State EXPIRED (Last update: {updated_at_str}). Resetting.")
                except Exception as e:
                    print(f"[ContextLoader] Date parse error: {e}")
            
            if not is_expired:
                # Backward compatibility: old snapshots used "AWAITING_CLARIFICATION"
                # which we now normalize to "NEEDS_CLARIFICATION".
                raw_state = state.get("conversation_state", "IDLE")
                if raw_state == "AWAITING_CLARIFICATION":
                    raw_state = "NEEDS_CLARIFICATION"

                context.conversation_state = raw_state
                context.last_ai_message_type = state.get("last_ai_message_type", "FINAL_OUTPUT")
                context.pending_request = state.get("pending_request")
                print(f"[ContextLoader] Loaded state: {context.conversation_state}")
            else:
                # Force reset in memory (file remains until next save overwrites it)
                context.conversation_state = "IDLE"
                context.pending_request = None
        
        # Extract components from existing code
        if context.existing_code:
            context.components = self._detect_components(context.existing_code)
            print(f"[ContextLoader] Detected components: {context.components}")
        
        print(f"[ContextLoader] Context loaded successfully")
        return context
    
    def save_state(self, project_id: str, context: ProjectContext):
        """Save conversation state."""
        project_path = self.workspace_root / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        
        state_file = project_path / ".hardcore_state.json"
        
        state_data = {
            "conversation_state": context.conversation_state,
            "last_ai_message_type": context.last_ai_message_type,
            "pending_request": context.pending_request,
            "updated_at": self._get_timestamp()
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

    def save_history(self, project_id: str, user_prompt: str, ai_response: Dict[str, Any]):
        """Save interaction to conversation history with detailed context."""
        project_path = self.workspace_root / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        
        history_file = project_path / ".hardcore_history.json"
        
        # Load existing history
        history = []
        if history_file.exists():
            history = self._load_history(history_file)
        
        # Extract action/summary from response
        action = "firmware_generated"
        if "code" in ai_response:
            # Try to detect what was generated
            code = ai_response.get("code", "")
            if "servo" in code.lower():
                action = "servo_control"
            elif "led" in code.lower() or "blink" in code.lower():
                action = "led_blink"
            elif "motor" in code.lower():
                action = "motor_control"
            elif "sensor" in code.lower():
                action = "sensor_reading"
        
        # Add new entry with more detail
        history.append({
            "timestamp": self._get_timestamp(),
            "user_prompt": user_prompt,
            "action": action,
            "success": ai_response.get("metadata", {}).get("model") is not None,
            "board": ai_response.get("pin_json", {}).get("mcu", "unknown"),
            "components": [conn.get("component") for conn in ai_response.get("pin_json", {}).get("connections", [])]
        })
        
        # Keep only last 10 entries for context
        history = history[-10:]
        
        # Save
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_file(self, path: Path) -> str:
        """Safely load a text file."""
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"[ContextLoader] Warning: Could not load {path}: {e}")
            return ""
    
    def _extract_pins_from_code(self, code: str) -> Dict[str, int]:
        """
        Extract all pin definitions from code.
        Supports: #define PIN_NAME 13, const int PIN_NAME = 13
        """
        pins = {}
        
        # Match #define patterns
        for match in re.finditer(r'#define\s+(\w+)\s+(\d+)', code):
            name, value = match.groups()
            if 'PIN' in name.upper() or name.upper() in ['LED', 'SERVO', 'MOTOR']:
                pins[name] = int(value)
        
        # Match const int patterns
        for match in re.finditer(r'const\s+int\s+(\w+)\s*=\s*(\d+)', code):
            name, value = match.groups()
            if 'PIN' in name.upper() or name.upper() in ['LED', 'SERVO', 'MOTOR']:
                pins[name] = int(value)
        
        return pins
    
    def _detect_board_from_config(self, config: str) -> str:
        """Detect board type from platformio.ini."""
        # Look for board = xxx line
        match = re.search(r'board\s*=\s*(\w+)', config)
        if match:
            board = match.group(1)
            if 'esp32' in board.lower():
                return 'esp32'
            elif 'nano' in board.lower():
                return 'arduino_nano'
            elif 'uno' in board.lower():
                return 'arduino_uno'
            return board
        return 'unknown'  # default
    
    def _load_history(self, history_file: Path) -> List[Dict[str, str]]:
        """Load conversation history from JSON."""
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ContextLoader] Warning: Could not load history: {e}")
            return []

    def _load_state(self, state_file: Path) -> Dict[str, Any]:
        """Load conversation state from JSON."""
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ContextLoader] Warning: Could not load state: {e}")
            return {}
    
    def _detect_components(self, code: str) -> List[str]:
        """Detect components mentioned in code."""
        components = []
        
        code_lower = code.lower()
        
        # Servo detection
        if 'servo' in code_lower or '#include <servo' in code_lower:
            components.append('servo')
        
        # Motor detection
        if 'motor' in code_lower:
            components.append('motor')
        
        # LED detection
        if 'led' in code_lower or 'digitalwrite' in code_lower:
            components.append('led')
        
        # Sensor detection
        if 'sensor' in code_lower or 'analogread' in code_lower:
            components.append('sensor')
        
        # I2C detection
        if 'wire.h' in code_lower or 'i2c' in code_lower:
            components.append('i2c_device')
        
        return components
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
