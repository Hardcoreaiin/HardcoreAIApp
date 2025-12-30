"""
Intelligent Hardware Abstraction Layer
Validates AI pin selections, provides constraints, and auto-fixes conflicts.
Works WITH the AI, not after it.
"""

import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass

@dataclass
class PinConstraints:
    """Pin constraints for a specific board."""
    available_gpio: List[int]
    pwm_capable: List[int]
    adc_capable: List[int]
    i2c_pins: Dict[str, int]  # {"SDA": 21, "SCL": 22}
    reserved: List[int]  # Reserved/unusable pins
    
@dataclass
class ValidationIssue:
    """Pin validation issue."""
    type: str  # "conflict", "invalid_pin", "wrong_capability"
    severity: str  # "critical", "warning"
    message: str
    suggested_fix: Optional[str] = None

class IntelligentHAL:
    """
    Hardware-aware adapter that validates and resolves pins.
    Provides constraints to AI and validates AI output.
    """
    
    # Board specifications
    BOARD_SPECS = {
        "esp32": {
            "available_gpio": list(range(0, 40)),
            "pwm_capable": [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
            "adc_capable": [32, 33, 34, 35, 36, 39],
            "i2c": {"SDA": 21, "SCL": 22},
            "reserved": [0, 1, 6, 7, 8, 9, 10, 11],  # Boot, flash pins
            "default_led": 2
        },
        "arduino_nano": {
            "available_gpio": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "pwm_capable": [3, 5, 6, 9, 10, 11],
            "adc_capable": [14, 15, 16, 17, 18, 19],  # A0-A5
            "i2c": {"SDA": 18, "SCL": 19},  # A4, A5
            "reserved": [0, 1],  # RX, TX
            "default_led": 13
        },
        "arduino_uno": {
            "available_gpio": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "pwm_capable": [3, 5, 6, 9, 10, 11],
            "adc_capable": [14, 15, 16, 17, 18, 19],
            "i2c": {"SDA": 18, "SCL": 19},
            "reserved": [0, 1],
            "default_led": 13
        }
    }
    
    def __init__(self, board_type: str = "esp32"):
        self.board_type = board_type
        self.spec = self.BOARD_SPECS.get(board_type, self.BOARD_SPECS["esp32"])
        
        print(f"[IntelligentHAL] Initialized for {board_type}")
        print(f"[IntelligentHAL]   GPIO pins: {len(self.spec['available_gpio'])}")
        print(f"[IntelligentHAL]   PWM capable: {len(self.spec['pwm_capable'])}")
    
    def get_constraints(self) -> PinConstraints:
        """Provide pin constraints to AI before generation."""
        return PinConstraints(
            available_gpio=self.spec["available_gpio"],
            pwm_capable=self.spec["pwm_capable"],
            adc_capable=self.spec["adc_capable"],
            i2c_pins=self.spec["i2c"],
            reserved=self.spec["reserved"]
        )
    
    def validate_and_resolve(self, pin_json: Dict[str, Any]) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
        """
        Validate AI's pin choices and auto-fix issues.
        
        Returns:
            (resolved_pins, issues)
        """
        print(f"[IntelligentHAL] Validating pin configuration...")
        
        issues = []
        resolved = {}
        used_pins: Set[int] = set()
        
        connections = pin_json.get("connections", [])
        
        for conn in connections:
            component = conn.get("component", "Unknown")
            pins = conn.get("pins", [])
            
            for pin in pins:
                mcu_pin_str = str(pin.get("mcu_pin", "0"))
                pin_type = pin.get("type", "GPIO")
                
                # Parse pin number
                mcu_pin = self._parse_pin_number(mcu_pin_str)
                
                # Validate pin
                pin_issues = self._validate_pin(mcu_pin, pin_type, component)
                issues.extend(pin_issues)
                
                # Check for conflicts
                if mcu_pin in used_pins:
                    issues.append(ValidationIssue(
                        type="conflict",
                        severity="critical",
                        message=f"Pin {mcu_pin} used by multiple components",
                        suggested_fix=f"Reassign one component to different pin"
                    ))
                
                used_pins.add(mcu_pin)
                resolved[component] = mcu_pin
        
        # Auto-fix critical issues
        if any(i.severity == "critical" for i in issues):
            print(f"[IntelligentHAL] Auto-fixing {len(issues)} critical issues...")
            resolved, issues = self._auto_fix(resolved, issues, connections)
        
        print(f"[IntelligentHAL] Validation complete")
        print(f"[IntelligentHAL]   Resolved pins: {len(resolved)}")
        print(f"[IntelligentHAL]   Issues: {len(issues)}")
        
        return resolved, issues
    
    def _parse_pin_number(self, pin_str: str) -> int:
        """Extract numeric pin from various formats (GPIO2, D13, 2, etc.)."""
        match = re.search(r'\d+', str(pin_str))
        return int(match.group(0)) if match else 0
    
    def _validate_pin(self, pin: int, pin_type: str, component: str) -> List[ValidationIssue]:
        """Validate a single pin assignment."""
        issues = []
        
        # Check if pin exists
        if pin not in self.spec["available_gpio"]:
            issues.append(ValidationIssue(
                type="invalid_pin",
                severity="critical",
                message=f"Pin {pin} not available on {self.board_type}",
                suggested_fix=f"Use pin from: {self.spec['available_gpio'][:5]}"
            ))
            return issues
        
        # Check if reserved
        if pin in self.spec["reserved"]:
            issues.append(ValidationIssue(
                type="reserved_pin",
                severity="warning",
                message=f"Pin {pin} is reserved (boot/flash)",
                suggested_fix="Use different pin if possible"
            ))
        
        # Check capability match
        if pin_type == "PWM" and pin not in self.spec["pwm_capable"]:
            issues.append(ValidationIssue(
                type="wrong_capability",
                severity="critical",
                message=f"Pin {pin} not PWM-capable for {component}",
                suggested_fix=f"Use PWM pin: {self.spec['pwm_capable'][:3]}"
            ))
        
        if pin_type == "ADC" and pin not in self.spec["adc_capable"]:
            issues.append(ValidationIssue(
                type="wrong_capability",
                severity="critical",
                message=f"Pin {pin} not ADC-capable for {component}",
                suggested_fix=f"Use ADC pin: {self.spec['adc_capable'][:3]}"
            ))
        
        return issues
    
    def _auto_fix(self, 
                  resolved: Dict[str, int],
                  issues: List[ValidationIssue],
                  connections: List[Dict]) -> Tuple[Dict[str, Any], List[ValidationIssue]]:
        """
        Attempt to auto-fix critical issues.
        Reassigns pins that are invalid or conflicting.
        """
        fixed_resolved = resolved.copy()
        remaining_issues = []
        
        # Track used pins
        used_pins = set(fixed_resolved.values())
        
        for issue in issues:
            if issue.severity != "critical":
                remaining_issues.append(issue)
                continue
            
            # Try to fix based on issue type
            if issue.type == "wrong_capability":
                # Extract component name from message
                component_match = re.search(r'for (\w+)', issue.message)
                if component_match:
                    component = component_match.group(1)
                    
                    # Find required capability
                    if "PWM" in issue.message:
                        # Assign first available PWM pin
                        for pwm_pin in self.spec["pwm_capable"]:
                            if pwm_pin not in used_pins:
                                print(f"[IntelligentHAL]   Auto-fix: {component} → Pin {pwm_pin} (PWM)")
                                fixed_resolved[component] = pwm_pin
                                used_pins.add(pwm_pin)
                                break
                    elif "ADC" in issue.message:
                        for adc_pin in self.spec["adc_capable"]:
                            if adc_pin not in used_pins:
                                print(f"[IntelligentHAL]   Auto-fix: {component} → Pin {adc_pin} (ADC)")
                                fixed_resolved[component] = adc_pin
                                used_pins.add(adc_pin)
                                break
            
            elif issue.type == "invalid_pin":
                # Just a warning now, already fixed
                remaining_issues.append(ValidationIssue(
                    type="auto_fixed",
                    severity="warning",
                    message=f"Auto-fixed: {issue.message}"
                ))
        
        return fixed_resolved, remaining_issues
    
    def generate_pins_header(self, resolved_pins: Dict[str, int]) -> str:
        """Generate C header with pin definitions."""
        lines = [
            "/*",
            " * Resolved Pin Definitions",
            f" * Board: {self.board_type.upper()}",
            " * Auto-generated by HardcoreAI IntelligentHAL",
            " */",
            "",
            "#ifndef RESOLVED_PINS_H",
            "#define RESOLVED_PINS_H",
            ""
        ]
        
        for component, pin in sorted(resolved_pins.items()):
            define_name = f"{component.upper()}_PIN"
            lines.append(f"#define {define_name} {pin}")
        
        lines.extend(["", "#endif // RESOLVED_PINS_H", ""])
        
        return "\n".join(lines)
