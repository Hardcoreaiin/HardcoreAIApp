"""
Firmware Assembler - Pure Assembly Layer
Takes AI-generated firmware package and assembles final output with
platform-specific headers, pin definitions, and build configurations.
NO AI generation logic - pure assembly.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CompiledFirmware:
    """Complete compiled firmware package ready for deployment."""
    main_cpp: str
    resolved_pins_h: str
    platformio_ini: str
    dependencies: list
    build_command: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_cpp": self.main_cpp,
            "resolved_pins_h": self.resolved_pins_h,
            "platformio_ini": self.platformio_ini,
            "dependencies": self.dependencies,
            "build_command": self.build_command
        }

class FirmwareAssembler:
    """
    Assembles complete firmware from AI-generated package.
    Adds platform-specific polish, headers, and build configurations.
    """
    
    # Platform-specific board configurations
    BOARD_CONFIGS = {
        "esp32": {
            "platform": "espressif32",
            "board": "esp32dev",
            "framework": "arduino",
            "dependencies": ["ESP32Servo"]
        },
        "arduino_nano": {
            "platform": "atmelavr",
            "board": "nanoatmega328",
            "framework": "arduino",
            "dependencies": ["Servo"]
        },
        "arduino_uno": {
            "platform": "atmelavr",
            "board": "uno",
            "framework": "arduino",
            "dependencies": ["Servo"]
        }
    }
    
    def __init__(self):
        print("[FirmwareAssembler] Initialized")
    
    def assemble(self, 
                 firmware_package: Dict[str, Any],
                 board_type: str = "esp32",
                 resolved_pins: Optional[Dict[str, Any]] = None) -> CompiledFirmware:
        """
        Assemble complete firmware from AI package.
        
        Args:
            firmware_package: AI-generated package with code, pins, etc.
            board_type: Target board type
            resolved_pins: HAL-resolved pin mappings
            
        Returns:
            CompiledFirmware ready for deployment
        """
        print(f"[FirmwareAssembler] Assembling firmware for {board_type}")
        
        # Extract AI-generated code
        code = firmware_package.get("code", "")
        pin_json = firmware_package.get("pin_json", {})
        
        # Add platform-specific polish
        polished_code = self._add_platform_headers(code, board_type)
        polished_code = self._add_build_comment(polished_code, board_type)
        
        # Generate resolved_pins.h (optional header file)
        pins_header = self._generate_pin_header(pin_json, resolved_pins)
        
        # Generate platformio.ini
        pio_config = self._generate_platformio_ini(board_type, code)
        
        # Detect dependencies from code
        dependencies = self._detect_dependencies(code)
        
        # Build command
        build_cmd = "pio run -t upload"
        
        print(f"[FirmwareAssembler] ✓ Assembly complete")
        print(f"[FirmwareAssembler]   Code: {len(polished_code)} chars")
        print(f"[FirmwareAssembler]   Dependencies: {dependencies}")
        
        return CompiledFirmware(
            main_cpp=polished_code,
            resolved_pins_h=pins_header,
            platformio_ini=pio_config,
            dependencies=dependencies,
            build_command=build_cmd
        )
    
    def _add_platform_headers(self, code: str, board: str) -> str:
        """Add platform-specific headers if missing."""
        # Check if Arduino.h is included
        if "#include <Arduino.h>" not in code and "#include <Arduino.h>" not in code.lower():
            # Add at top (before any other #include)
            lines = code.split("\n")
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("#include"):
                    insert_pos = i
                    break
            
            if insert_pos == 0:
                # No includes, add at very top
                code = "#include <Arduino.h>\n\n" + code
            else:
                # Add before first include
                lines.insert(insert_pos, "#include <Arduino.h>")
                code = "\n".join(lines)
        
        return code
    
    def _add_build_comment(self, code: str, board: str) -> str:
        """Add build command comment at end if not present."""
        if "// Build:" not in code and "Build:" not in code:
            board_config = self.BOARD_CONFIGS.get(board, self.BOARD_CONFIGS["esp32"])
            code += f"\n\n// Build: pio run -t upload -e {board_config['board']}\n"
        
        return code
    
    def _generate_pin_header(self, 
                             pin_json: Dict[str, Any],
                             resolved_pins: Optional[Dict[str, Any]]) -> str:
        """
        Generate resolved_pins.h header file.
        Optional include for projects that want pin definitions separated.
        """
        header = """/* 
 * Resolved Pin Definitions
 * Auto-generated by HardcoreAI
 */

#ifndef RESOLVED_PINS_H
#define RESOLVED_PINS_H

"""
        
        # Extract pins from JSON
        connections = pin_json.get("connections", [])
        
        for conn in connections:
            component = conn.get("component", "Unknown")
            pins = conn.get("pins", [])
            
            for pin in pins:
                mcu_pin = pin.get("mcu_pin", "0")
                pin_type = pin.get("type", "GPIO")
                
                # Generate #define
                define_name = f"{component.upper()}_{pin_type}_PIN"
                header += f"#define {define_name} {mcu_pin}\n"
        
        header += "\n#endif // RESOLVED_PINS_H\n"
        
        return header
    
    def _generate_platformio_ini(self, board: str, code: str) -> str:
        """Generate platformio.ini configuration."""
        board_config = self.BOARD_CONFIGS.get(board, self.BOARD_CONFIGS["esp32"])
        
        # Detect dependencies from code
        dependencies = self._detect_dependencies(code)
        dep_lines = "\n".join(f"    {dep}" for dep in dependencies)
        
        config = f"""[env:{board_config['board']}]
platform = {board_config['platform']}
board = {board_config['board']}
framework = {board_config['framework']}
monitor_speed = 115200
lib_deps = 
{dep_lines if dep_lines else "    ; No additional libraries"}
"""
        
        return config
    
    def _detect_dependencies(self, code: str) -> list:
        """Detect library dependencies from code."""
        deps = []
        
        # Servo library
        if "Servo" in code and "#include" in code and "Servo.h" in code:
            if "ESP32" in code or "esp32" in code.lower():
                deps.append("ESP32Servo")
            else:
                deps.append("Servo")
        
        # Wire (I2C)
        if "Wire.h" in code:
            deps.append("Wire")
        
        # SPI
        if "SPI.h" in code:
            deps.append("SPI")
        
        return deps
