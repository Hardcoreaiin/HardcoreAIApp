"""
Gemini-Only Firmware Generation Engine with Intent Protection
Enhanced version of strict Gemini engine with semantic validation.
"""

import os
import json
import re
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from context_loader import ProjectContext, ProjectContextLoader

@dataclass
class GenerationAttempt:
    """Record of a single generation attempt."""
    model: str
    status_code: int
    latency_ms: int
    error_snippet: Optional[str] = None
    success: bool = False

@dataclass
class FirmwarePackage:
    """Complete firmware package with all required sections."""
    code: str
    pin_block: str
    pin_json: Dict[str, Any]
    timeline: str
    tests: List[str]
    
    # Metadata
    model_used: str = ""
    confidence: float = 1.0
    context_used: bool = False
    attempts: List[GenerationAttempt] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "code": self.code,
            "pin_block": self.pin_block,
            "pin_json": self.pin_json,
            "timeline": self.timeline,
            "tests": self.tests,
            "metadata": {
                "model": self.model_used,
                "confidence": self.confidence,
                "context_aware": self.context_used,
                "attempts": [
                    {
                        "model": a.model,
                        "status": a.status_code,
                        "latency_ms": a.latency_ms,
                        "success": a.success
                    } for a in self.attempts
                ]
            }
        }

class GeminiError(Exception):
    """Base exception for Gemini-related errors."""
    def __init__(self, error_code: str, message: str, attempts: List[GenerationAttempt]):
        self.error_code = error_code
        self.message = message
        self.attempts = attempts
        super().__init__(message)

class StrictGeminiEngine:
    """
    Strict Gemini-only firmware generation engine with semantic intent protection.
    
    CRITICAL: NO LOCAL FALLBACKS - Fails explicitly when Gemini unavailable.
    """
    
    # Whitelisted Gemini models
    DEFAULT_MODEL_WHITELIST = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite", 
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]
    
    # Retry configuration (Survival Mode for free tier)
    RETRY_CONFIG = {
        "max_attempts": int(os.getenv("GEMINI_MAX_RETRIES", "10")),
        "base_delay": float(os.getenv("GEMINI_RETRY_BASE_DELAY", "2.0")),
        "max_delay": 60.0,
        "backoff_factor": 1.5
    }
    
    def __init__(self, api_key: Optional[str] = None, workspace_root: Optional[Path] = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        
        # Load model whitelist from env or use default
        whitelist_str = os.getenv("GEMINI_MODEL_WHITELIST", "")
        if whitelist_str:
            self.model_whitelist = [m.strip() for m in whitelist_str.split(",")]
        else:
            self.model_whitelist = self.DEFAULT_MODEL_WHITELIST.copy()
        
        self.current_model_index = 0
        self.current_model = self.model_whitelist[0]
        
        # Context loader for project awareness
        self.context_loader = ProjectContextLoader(workspace_root)
        
        # Configuration
        self.timeout = 30
        self.temperature = 0.2
        
        # Track last user prompt for helpers
        self.last_user_prompt: Optional[str] = None
        
        print(f"[StrictGemini] ===== GEMINI-ONLY ENGINE (INTENT-PROTECTED) =====")
        print(f"[StrictGemini] Model whitelist: {self.model_whitelist}")
        print(f"[StrictGemini] Max retries: {self.RETRY_CONFIG['max_attempts']}")
        print(f"[StrictGemini] API Key configured: {'Yes' if self.api_key else 'NO - WILL FAIL'}")
    
    def preflight_check_models(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Query Gemini API to find first supported model.
        Returns: (model_name, error_message)
        """
        print(f"[StrictGemini] Running preflight model check...")
        
        if not self.api_key:
            return (None, "No API key configured")
        
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        
        try:
            resp = requests.get(endpoint, timeout=10)
            resp.raise_for_status()
            models_data = resp.json()
            
            # Find first whitelisted model that supports generateContent
            for model_info in models_data.get("models", []):
                model_name = model_info.get("name", "").replace("models/", "")
                
                if model_name in self.model_whitelist:
                    methods = model_info.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        print(f"[StrictGemini] ✓ Found supported model: {model_name}")
                        return (model_name, None)
            
            available = [m.get("name", "").replace("models/", "") for m in models_data.get("models", [])]
            error_msg = f"No whitelisted models support generateContent. Available: {available[:5]}"
            print(f"[StrictGemini] ✗ Preflight failed: {error_msg}")
            return (None, error_msg)
            
        except requests.HTTPError as e:
            error_msg = f"Preflight HTTP error {e.response.status_code}: {e.response.text[:200]}"
            print(f"[StrictGemini] ✗ Preflight failed: {error_msg}")
            return (None, error_msg)
        except Exception as e:
            error_msg = f"Preflight check failed: {str(e)}"
            print(f"[StrictGemini] ✗ Preflight failed: {error_msg}")
            return (None, error_msg)
    
    def generate_firmware(self, 
                         user_request: str, 
                         board_type: str = "esp32",
                         project_id: str = "current_project") -> FirmwarePackage:
        """
        Main entry point - Strict Gemini-only generation with intent protection.
        
        Raises GeminiError if generation fails for any reason.
        NEVER returns local fallback code.
        """
        print(f"\n[StrictGemini] ===== FIRMWARE GENERATION REQUEST =====")
        print(f"[StrictGemini] Request: {user_request[:100]}...")
        print(f"[StrictGemini] Board (API): {board_type}")
        
        # Track for pin extraction
        self.last_user_prompt = user_request
        
        attempts: List[GenerationAttempt] = []
        
        # STAGE 1: Preflight check
        supported_model, error = self.preflight_check_models()
        if not supported_model:
            raise GeminiError(
                error_code="MODEL_NOT_SUPPORTED",
                message=f"No Gemini models available. {error}",
                attempts=attempts
            )
        
        # Use the preflight-validated model
        self.current_model = supported_model
        
        # STAGE 2: Load context
        print(f"\n[StrictGemini] STAGE 1: Loading project context...")
        context = self.context_loader.load(project_id)
        
        # CRITICAL: Extract board from user's prompt text FIRST
        # This prevents asking "What board?" when user says "Make this ESP32..."
        extracted_board = self._extract_board_from_prompt(user_request)
        if extracted_board:
            print(f"[StrictGemini]   Board extracted from prompt: '{extracted_board}'")
            context.board_type = extracted_board
        elif board_type and board_type.lower() not in ('unknown', 'none', ''):
            normalized = self._normalize_board_identifier(board_type)
            print(f"[StrictGemini]   Board from API: {board_type} -> {normalized}")
            context.board_type = normalized
        
        # If still no board, use default
        if not context.board_type or context.board_type.lower() in ('unknown', 'none', ''):
            context.board_type = "esp32dev"
            print(f"[StrictGemini]   Using default board: esp32dev")
        
        # STAGE 3: Build prompt with ABSOLUTE CORE RULE
        print(f"[StrictGemini] STAGE 2: Building prompt...")
        prompt = self._build_contextual_prompt(user_request, context)
        
        # STAGE 4: Generate with retry (exponential backoff)
        print(f"[StrictGemini] STAGE 3: Calling Gemini with retry...")
        raw_output, attempts = self._generate_with_retry(prompt)
        
        if not raw_output:
            # All retries exhausted
            raise GeminiError(
                error_code="LLM_UNAVAILABLE",
                message=f"All {len(attempts)} Gemini attempts failed. Check API status and try again in 60s.",
                attempts=attempts
            )
        
        # STAGE 5: Parse output
        print(f"[StrictGemini] STAGE 4: Parsing output...")
        try:
            package = self._parse_ai_output(raw_output, context.board_type)
            package.model_used = self.current_model
            package.context_used = context.existing_code is not None
            package.attempts = attempts
            
        except Exception as e:
            raise GeminiError(
                error_code="VALIDATION_FAILED",
                message=f"Gemini output parsing failed: {str(e)}. Output may be incomplete.",
                attempts=attempts
            )
        
        # STAGE 6: SEMANTIC VALIDATION (Warning Only - NOT Blocking)
        # This checks if Gemini violated intent rules but does NOT prevent output
        print(f"[StrictGemini] STAGE 5: Semantic validation (warning only)...")
        is_semantically_valid, semantic_error = self._semantic_validate(user_request, package)
        
        if not is_semantically_valid:
            print(f"[StrictGemini]   ⚠️  WARNING: {semantic_error}")
            print(f"[StrictGemini]   ⚠️  Gemini may have misunderstood the request")
            print(f"[StrictGemini]   ℹ️  Returning output anyway (no blocking)")
            # Continue anyway - show what Gemini actually generated
        else:
            print(f"[StrictGemini]   ✓ Semantic validation passed")
        
        # STAGE 7: Strict structural validation
        print(f"[StrictGemini] STAGE 6: Structural validation...")
        is_valid, validation_error = self._validate_strict(package)
        
        if not is_valid:
            raise GeminiError(
                error_code="VALIDATION_FAILED",
                message=f"Gemini output incomplete: {validation_error}. Please try again.",
                attempts=attempts
            )
        
        # Save to history
        self.context_loader.save_history(project_id, user_request, package.to_dict())
        
        print(f"[StrictGemini] ✅ Generation complete!")
        print(f"[StrictGemini]   Model: {package.model_used}")
        print(f"[StrictGemini]   Board: {context.board_type}")
        print(f"[StrictGemini]   Confidence: {package.confidence}")
        
        return package
    
    def _build_contextual_prompt(self, user_request: str, context: ProjectContext) -> str:
        """Build prompt with ABSOLUTE CORE RULE and context injection."""
        
        system_prompt = """You are HardcoreAI — an industry-grade Embedded Systems, Robotics, and Firmware Engineer.

Your mission:
Make hardware programming effortless for beginners and precise for experts.
A user should be able to connect hardware, describe behavior in natural language, and receive correct, flashable firmware.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE CORE RULE (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE USER'S INTENT IS THE SINGLE SOURCE OF TRUTH.

Once a task is identified (e.g., motor control, sensor reading, robot motion),
YOU MUST NEVER change, downgrade, replace, or reinterpret the task.

Examples of forbidden behavior:
• Motors → LEDs ❌
• Driver-based control → GPIO demo code ❌
• Robot motion → unrelated example ❌
• Ignoring explicitly provided pins or hardware ❌

If the user says "motor", you generate MOTOR CODE.
If the user says "sensor", you generate SENSOR CODE.
If the user says "robot", you generate ROBOT LOGIC.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIRMWARE GENERATION REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When generating firmware, ALWAYS output ALL of the following, in order:

1. COMPLETE, BUILDABLE FIRMWARE CODE (fenced ```cpp)
   • Correct language & framework for the board
   • No placeholder registers
   • No fake delays
   • No unrelated examples

2. PIN CONNECTIONS
   • Explicit MCU pin → peripheral pin
   • Signal type (GPIO / PWM / ADC / I2C / SPI)
   • Power & ground connections

3. <!--PIN-CONNECTIONS-JSON-->
   • Must match the firmware exactly

4. TIMELINE
   • Describe behavior over time (first ~30s)

5. TEST CHECKLIST
   • What to observe
   • How to verify correctness

NEVER claim success without real firmware.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIMING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Multi-phase logic MUST NOT use delay()
• Arduino-class MCUs → millis()-based FSM
• ESP32 → FreeRTOS tasks/timers when appropriate
• Parse complex timing exactly ("first X sec, then Y sec, then stop")
"""

        # Context injection
        prompt_parts = [system_prompt, "\n\n--- CURRENT CONTEXT ---\n"]
        prompt_parts.append(f"TARGET BOARD: {context.board_type.upper()}\n")
        
        # Existing code context
        if context.existing_code:
            prompt_parts.append(f"\nEXISTING CODE (for reference):\n```cpp\n{context.existing_code[:800]}\n```\n")
            
        # Existing pins
        if context.existing_pins:
            pin_str = ", ".join(f"{k}={v}" for k, v in list(context.existing_pins.items())[:5])
            prompt_parts.append(f"\nCURRENT PINS: {pin_str}\n")
        
        # Conversation history
        if context.conversation_history:
            recent = context.conversation_history[-3:]
            prompt_parts.append("\n--- RECENT CONVERSATION ---\n")
            for i, entry in enumerate(recent, 1):
                user_msg = entry.get('user_prompt', '')
                action = entry.get('action', 'unknown')
                prompt_parts.append(f"{i}. User: \"{user_msg}\" → Action: {action}\n")
        
        # User request
        prompt_parts.append(f"\n--- USER REQUEST ---\n{user_request}\n")
        
        # Final instruction
        prompt_parts.append("\nGenerate complete firmware with ALL 5 sections. Ensure the hardware matches the user's EXACT intent.")
        
        return "".join(prompt_parts)
    
    def _semantic_validate(self, prompt: str, package: FirmwarePackage) -> Tuple[bool, Optional[str]]:
        """
        Semantic validation: ensure generated firmware matches user's actual intent.
        
        This catches violations like:
        - User asks for motor control, gets LED code
        - User provides explicit pins that are ignored
        """
        text = prompt.lower()
        code = package.code.lower()
        pin_block = (package.pin_block or "").lower()

        # CRITICAL CHECK 1: Detect LED substitution (most common violation)
        has_led_code = any(pattern in code for pattern in [
            "led_pin", "led =", "blink", "digitalwrite"
        ])
        user_asked_for_led = "led" in text or "blink" in text
        
        # If code is LED-focused but user never mentioned LEDs, check if they asked for something else
        if has_led_code and not user_asked_for_led:
            wants_motor = any(k in text for k in ["motor", "robot", "move", "l298", "driver"])
            wants_sensor = any(k in text for k in ["sensor", "read", "ultrasonic", "temperature"])
            
            if wants_motor or wants_sensor:
                return False, f"CRITICAL VIOLATION: User requested {('motor control' if wants_motor else 'sensor reading')} but generated code is LED blink demo."

        # CHECK 2: Motor / L298N detection
        wants_motor = any(k in text for k in ["motor", "robot", "move forward", "l298", "l298n"])
        has_motor_code = any(k in code for k in ["motor", "l298", "l298n"]) or ("pwm" in code and wants_motor)

        if wants_motor and not has_motor_code:
            return False, "Generated code does not implement motor control requested by user."

        # CHECK 3: Explicit pin labels must be reflected
        explicit_pins = self._extract_pin_mappings_from_prompt(prompt)
        if explicit_pins:
            missing_labels = []
            for conn in explicit_pins:
                label = conn.get("component", "")
                if not label:
                    continue
                l_lower = label.lower()
                if l_lower not in code and l_lower not in pin_block:
                    missing_labels.append(label)

            if missing_labels:
                return False, f"Generated code ignored explicit pin labels: {', '.join(missing_labels)}."

        return True, None
    
    def _extract_pin_mappings_from_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Parse explicit user pin mappings such as:
        - ENA - 19
        - IN1 - 21
        - IN2: 18
        """
        connections: List[Dict[str, Any]] = []
        if not prompt:
            return connections

        for line in prompt.splitlines():
            m = re.match(r"^\s*([A-Za-z][A-Za-z0-9_ ]*?)\s*[-:=]\s*(\d+)\s*$", line)
            if not m:
                continue
            label, num = m.group(1).strip(), int(m.group(2))
            if not label:
                continue

            connections.append({
                "component": label,
                "pins": [{
                    "mcu_pin": num,
                    "component_pin": label,
                    "type": "GPIO"
                }]
            })

        if connections:
            print(f"[StrictGemini]   Extracted {len(connections)} explicit pin mappings")
        return connections
    
    def _extract_board_from_prompt(self, prompt: str) -> Optional[str]:
        """
        Extract board/MCU name from user's natural language.
        
        Examples:
        - "Make this ESP32 move forward" → "esp32dev"
        - "Connect L298N to Arduino Uno" → "arduino_uno"
        """
        if not prompt:
            return None
            
        lower = prompt.lower()
        
        # Check for explicit board mentions (order matters - specific first)
        if "arduino uno" in lower or " uno " in lower:
            return "arduino_uno"
        if "arduino nano" in lower or " nano " in lower:
            return "arduino_nano"
        if "arduino mega" in lower or " mega" in lower:
            return "arduino_mega"
        if "esp32" in lower:
            return "esp32dev"
        if "esp8266" in lower:
            return "esp12e"
        if "stm32" in lower:
            return "stm32"
        if "c2000" in lower or "ti c2000" in lower:
            return "ti_c2000"
        if "pico" in lower or "rp2040" in lower:
            return "rp2040"
            
        return None
    
    def _normalize_board_identifier(self, raw: str) -> str:
        """Normalize board identifier from UI/API."""
        s = raw.strip().lower()

        if "arduino nano" in s or "nano" in s:
            return "arduino_nano"
        if "arduino uno" in s or "uno" in s:
            return "arduino_uno"
        if "arduino mega" in s or "mega" in s:
            return "arduino_mega"
        if "esp32" in s:
            return "esp32dev"
        if "esp8266" in s:
            return "esp12e"
        if "stm32" in s:
            return "stm32"
        if "c2000" in s or "ti" in s:
            return "ti_c2000"
        if "pico" in s:
            return "rp2040"

        return raw
    
    # ===== All original methods below (unchanged) =====
    
    def _generate_with_retry(self, prompt: str) -> Tuple[Optional[str], List[GenerationAttempt]]:
        """Call Gemini with exponential backoff retry."""
        attempts = []
        max_attempts = self.RETRY_CONFIG["max_attempts"]
        base_delay = self.RETRY_CONFIG["base_delay"]
        backoff_factor = self.RETRY_CONFIG["backoff_factor"]
        max_delay = self.RETRY_CONFIG["max_delay"]
        
        for attempt_num in range(max_attempts):
            start_time = time.time()
            
            try:
                print(f"[StrictGemini]   Attempt {attempt_num + 1}/{max_attempts}: {self.current_model}")
                
                endpoint = f"https://generativelanguage.googleapis.com/v1/models/{self.current_model}:generateContent"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generation_config": {
                        "temperature": self.temperature,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096
                    }
                }
                
                response = requests.post(
                    f"{endpoint}?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                attempt = GenerationAttempt(
                    model=self.current_model,
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    success=response.status_code == 200
                )
                
                print(f"[StrictGemini]   Status: {response.status_code} ({latency_ms}ms)")
                
                if response.status_code == 429:
                    attempt.error_snippet = response.text[:200]
                    attempts.append(attempt)
                    
                    if attempt_num < max_attempts - 1:
                        delay = min(base_delay * (backoff_factor ** attempt_num), max_delay)
                        print(f"[StrictGemini]   Rate limited, retrying in {delay}s...")
                        time.sleep(delay)
                        self._rotate_model()
                        continue
                    else:
                        return (None, attempts)
                
                if response.status_code != 200:
                    attempt.error_snippet = response.text[:200]
                    attempts.append(attempt)
                    
                    if attempt_num < max_attempts - 1:
                        self._rotate_model()
                        time.sleep(0.5)
                        continue
                    else:
                        return (None, attempts)
                
                body = response.json()
                text = self._extract_text(body)
                
                if text:
                    print(f"[StrictGemini]   ✓ Received {len(text)} chars")
                    attempts.append(attempt)
                    return (text, attempts)
                else:
                    attempt.error_snippet = "Empty response"
                    attempts.append(attempt)
                    
                    if attempt_num < max_attempts - 1:
                        self._rotate_model()
                        continue
                    else:
                        return (None, attempts)
                    
            except requests.Timeout:
                latency_ms = int((time.time() - start_time) * 1000)
                attempt = GenerationAttempt(
                    model=self.current_model,
                    status_code=408,
                    latency_ms=latency_ms,
                    error_snippet="Timeout",
                    success=False
                )
                attempts.append(attempt)
                
                if attempt_num < max_attempts - 1:
                    self._rotate_model()
                    continue
                    
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                attempt = GenerationAttempt(
                    model=self.current_model,
                    status_code=500,
                    latency_ms=latency_ms,
                    error_snippet=str(e)[:200],
                    success=False
                )
                attempts.append(attempt)
                
                if attempt_num < max_attempts - 1:
                    self._rotate_model()
                    continue
        
        return (None, attempts)
    
    def _rotate_model(self):
        """Switch to next model in whitelist."""
        old_model = self.current_model
        self.current_model_index = (self.current_model_index + 1) % len(self.model_whitelist)
        self.current_model = self.model_whitelist[self.current_model_index]
        print(f"[StrictGemini]   Rotated: {old_model} → {self.current_model}")
    
    def _extract_text(self, response_body: Dict[str, Any]) -> Optional[str]:
        """Safely extract text from Gemini response."""
        try:
            candidates = response_body.get("candidates", [])
            if not candidates:
                return None
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            
            return "\n".join(p.get("text", "") for p in parts).strip()
            
        except Exception:
            return None
    
    def _parse_ai_output(self, text: str, board: str) -> FirmwarePackage:
        """Parse AI output - may raise exceptions if incomplete."""
        package = FirmwarePackage(code="", pin_block="", pin_json={}, timeline="", tests=[])
        
        package.code = self._extract_code(text)
        package.pin_block = self._extract_pin_block(text, board)
        package.pin_json = self._extract_pin_json(text, board)
        package.timeline = self._extract_timeline(text)
        package.tests = self._extract_tests(text)
        package.confidence = self._calculate_confidence(package)
        
        # Regenerate pin_block from JSON for frontend
        if package.pin_json and package.pin_json.get("connections"):
            package.pin_block = self.generate_pin_block_from_json(package.pin_json, board)
        
        return package
    
    def _validate_strict(self, package: FirmwarePackage) -> Tuple[bool, Optional[str]]:
        """Strict 5-section validation with auto-repair."""
        if not package.code or len(package.code.strip()) < 50:
            return (False, "CODE section missing or too short")
        
        if not package.pin_json or not isinstance(package.pin_json, dict):
            return (False, "PIN_JSON missing")
        
        if "connections" not in package.pin_json or not package.pin_json["connections"]:
            connections = self._extract_pins_from_code_to_json(package.code)
            if connections:
                package.pin_json["connections"] = connections
            else:
                simple_pins = self._find_any_pins_in_code(package.code)
                if simple_pins:
                    package.pin_json["connections"] = simple_pins
                else:
                    package.pin_json["connections"] = []
        
        if not package.timeline:
            package.timeline = self._generate_default_timeline(package.code)
        
        if not package.tests:
            package.tests = self._generate_default_tests(package.code)
        
        return (True, None)
    
    def _generate_default_timeline(self, code: str) -> str:
        """Generate basic timeline from code analysis."""
        delays = re.findall(r'delay\((\d+)\)', code)
        if delays:
            total_ms = sum(int(d) for d in delays[:5])
            return f"Executes with delays totaling ~{total_ms}ms in main loop"
        if 'millis()' in code:
            return "Time-based control using millis() for non-blocking execution"
        if 'servo' in code.lower():
            return "Servo control with initialization and position commands"
        return "Continuous execution in main loop"
    
    def _generate_default_tests(self, code: str) -> List[str]:
        """Generate basic test checklist."""
        tests = []
        if 'Serial.begin' in code:
            tests.append("Verify serial monitor shows output")
        if 'servo' in code.lower() or 'Servo' in code:
            tests.append("Verify servo movement")
        if 'LED' in code or 'digitalWrite' in code:
            tests.append("Verify LED behavior")
        if 'delay(' in code:
            delays = re.findall(r'delay\((\d+)\)', code)
            if delays:
                tests.append(f"Verify timing matches delays ({delays[0]}ms, etc.)")
        if not tests:
            tests.append("Upload code and verify expected behavior")
            tests.append("Check serial monitor for debug output")
        tests.append("Ensure no compilation errors")
        return tests
    
    def _extract_pins_from_code_to_json(self, code: str) -> List[Dict[str, Any]]:
        """Extract pin definitions from code."""
        connections = []
        seen_pins = set()
        
        for match in re.finditer(r'#define\s+(\w*(?:PIN|LED|SERVO|MOTOR)\w*)\s+(\d+)', code, re.I):
            name, pin = match.groups()
            if pin not in seen_pins:
                component = name.replace("_PIN", "").replace("PIN_", "")
                connections.append({
                    "component": component,
                    "pins": [{"mcu_pin": pin, "component_pin": "Signal", "type": "GPIO"}],
                    "notes": f"From #define {name}"
                })
                seen_pins.add(pin)
        
        for match in re.finditer(r'const\s+int\s+(\w*(?:PIN|LED|SERVO|MOTOR)\w*)\s*=\s*(\d+)', code, re.I):
            name, pin = match.groups()
            if pin not in seen_pins:
                component = name.replace("_PIN", "").replace("PIN_", "")
                connections.append({
                    "component": component,
                    "pins": [{"mcu_pin": pin, "component_pin": "Signal", "type": "GPIO"}],
                    "notes": f"From const {name}"
                })
                seen_pins.add(pin)
        
        return connections
    
    def _find_any_pins_in_code(self, code: str) -> List[Dict[str, Any]]:
        """Last resort: find ANY pin numbers."""
        connections = []
        seen_pins = set()
        
        for match in re.finditer(r'pinMode\s*\(\s*(\d+)\s*,', code):
            pin = match.group(1)
            if pin not in seen_pins:
                connections.append({
                    "component": f"Pin_{pin}",
                    "pins": [{"mcu_pin": pin, "component_pin": "GPIO", "type": "GPIO"}],
                    "notes": "From pinMode()"
                })
                seen_pins.add(pin)
        
        for match in re.finditer(r'digitalWrite\s*\(\s*(\d+)\s*,', code):
            pin = match.group(1)
            if pin not in seen_pins:
                connections.append({
                    "component": f"Pin_{pin}",
                    "pins": [{"mcu_pin": pin, "component_pin": "GPIO", "type": "GPIO"}],
                    "notes": "From digitalWrite()"
                })
                seen_pins.add(pin)
        
        for match in re.finditer(r'\.attach\s*\(\s*(\d+)\s*\)', code):
            pin = match.group(1)
            if pin not in seen_pins:
                connections.append({
                    "component": "Servo",
                    "pins": [{"mcu_pin": pin, "component_pin": "PWM", "type": "PWM"}],
                    "notes": "From servo.attach()"
                })
                seen_pins.add(pin)
        
        return connections
    
    def _extract_code(self, text: str) -> str:
        """Extract code from fenced blocks."""
        match = re.search(r"```(?:cpp|c|arduino|ino)\n([\s\S]*?)\n```", text, re.I)
        if match:
            return match.group(1).strip()
        
        match = re.search(r"```\n?([\s\S]*?)\n?```", text)
        if match:
            code = match.group(1).strip()
            if "#include" in code or "void setup" in code:
                return code
        
        return ""
    
    def _extract_pin_block(self, text: str, board: str) -> str:
        """Extract PIN CONNECTIONS block."""
        match = re.search(r"(PIN CONNECTIONS[\s\S]*?)(?:\n\n|<!--PIN-CONNECTIONS-JSON-->)", text, re.I)
        if match:
            return match.group(1).strip()
        return f"PIN CONNECTIONS\n---\nMCU: {board}\n(Auto-generated)"
    
    def generate_pin_block_from_json(self, pin_json: Dict[str, Any], board: str) -> str:
        """Generate human-readable PIN CONNECTIONS block."""
        if not pin_json or "connections" not in pin_json:
            return f"PIN CONNECTIONS\n---\nMCU: {board}\nNo connections"
        
        connections = pin_json.get("connections", [])
        if not connections:
            return f"PIN CONNECTIONS\n---\nMCU: {board}\nNo connections"
        
        lines = ["PIN CONNECTIONS", "=" * 50, f"MCU: {pin_json.get('mcu', board).upper()}", ""]
        
        for i, conn in enumerate(connections, 1):
            component = conn.get("component", "Unknown")
            lines.append(f"{i}. {component}")
            lines.append("   " + "-" * 40)
            
            for pin_info in conn.get("pins", []):
                mcu_pin = pin_info.get("mcu_pin", "?")
                comp_pin = pin_info.get("component_pin", "Signal")
                pin_type = pin_info.get("type", "GPIO")
                lines.append(f"   MCU Pin {mcu_pin} → {component} {comp_pin} ({pin_type})")
            
            notes = conn.get("notes", "")
            if notes:
                lines.append(f"   Note: {notes}")
            lines.append("")
        
        lines.append("=" * 50)
        lines.append(f"Total: {len(connections)} connections")
        
        return "\n".join(lines)
    
    def _extract_pin_json(self, text: str, board: str) -> Dict[str, Any]:
        """Extract PIN JSON with flexible matching."""
        label_pos = text.find("<!--PIN-CONNECTIONS-JSON-->")
        
        if label_pos != -1:
            search_text = text[label_pos + 27:]
            json_str = self._find_json_object(search_text)
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        if "connections" not in parsed:
                            parsed["connections"] = []
                        if "mcu" not in parsed:
                            parsed["mcu"] = board
                        return parsed
                except:
                    pass
        
        # Find any JSON with connections/mcu
        start_idx = 0
        while True:
            start = text.find('{', start_idx)
            if start == -1:
                break
            
            json_str = self._find_json_object(text[start:])
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict) and ("connections" in parsed or "mcu" in parsed):
                        if "mcu" not in parsed:
                            parsed["mcu"] = board
                        return parsed
                except:
                    pass
                start_idx = start + len(json_str)
            else:
                start_idx = start + 1
        
        # Extract from code
        code = self._extract_code(text)
        if code:
            connections = self._extract_pins_from_code_to_json(code)
            if connections:
                return {"mcu": board, "connections": connections, "auto_extracted": True}
        
        return {"mcu": board, "connections": []}
    
    def _find_json_object(self, text: str) -> Optional[str]:
        """Find first balanced JSON object."""
        start = text.find('{')
        if start == -1:
            return None
        
        depth = 0
        in_string = False
        escape = False
        
        for i in range(start, len(text)):
            ch = text[i]
            
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        
        return None
    
    def _extract_timeline(self, text: str) -> str:
        """Extract timeline."""
        match = re.search(r"//\s*TIMELINE[:\s]+(.*?)(?:\n|$)", text, re.I)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_tests(self, text: str) -> List[str]:
        """Extract test checklist."""
        tests = []
        match = re.search(r"(?:TEST|CHECKLIST)[:\s]*([\s\S]*?)(?:\n\n|$)", text, re.I)
        if match:
            for line in match.group(1).split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•")):
                    tests.append(line.lstrip("-•").strip())
        return tests
    
    def _calculate_confidence(self, package: FirmwarePackage) -> float:
        """Calculate confidence score."""
        score = 0.0
        if package.code and len(package.code) > 100:
            score += 0.4
        if package.pin_json and package.pin_json.get("connections"):
            score += 0.3
        if package.timeline:
            score += 0.15
        if package.tests:
            score += 0.15
        return round(score, 2)
    
    def chat_response(self, prompt: str) -> str:
        """Handle conversational chat."""
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1/models/{self.current_model}:generateContent"
            payload = {
                "contents": [{"parts": [{"text": f"You are HardcoreAI. User: '{prompt}'. Reply in 2-3 sentences."}]}],
                "generation_config": {"temperature": 0.7, "max_output_tokens": 512}
            }
            
            response = requests.post(f"{endpoint}?key={self.api_key}",
                                   headers={"Content-Type": "application/json"},
                                   json=payload, timeout=10)
            
            if response.status_code == 429:
                return "I'm rate-limited. Try generating firmware!"
            
            if response.status_code == 200:
                text = self._extract_text(response.json())
                return text if text else "I'm having trouble responding."
            
            return "Error connecting to AI."
            
        except Exception as e:
            return f"Chat error: {str(e)[:50]}"


# Backward compatibility
ClaudeStyleFirmwareAI = StrictGeminiEngine
