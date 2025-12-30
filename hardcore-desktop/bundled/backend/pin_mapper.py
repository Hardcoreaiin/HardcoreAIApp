# Intelligent Pin Assignment System
# Auto-assigns optimal pins based on board capabilities and peripheral requirements

import json
from pathlib import Path
from typing import Dict, List, Optional

class IntelligentPinMapper:
    def __init__(self):
        self.board_capabilities = self.load_board_capabilities()
        self.pin_usage = {}  # Track which pins are in use
        
    def load_board_capabilities(self) -> Dict:
        """Load board pin capabilities from board_definitions.json"""
        board_def_path = Path(__file__).parent / "board_definitions.json"
        if board_def_path.exists():
            with open(board_def_path, 'r') as f:
                return json.load(f)
        return {}
    
    def auto_assign_pins(self, board_type: str, peripheral_type: str, requirements: Dict) -> Dict[str, int]:
        """
        Intelligently assign pins for a peripheral based on requirements
        
        Args:
            board_type: e.g., 'esp32', 'arduino_uno'
            peripheral_type: e.g., 'led', 'dht22', 'servo', 'i2c'
            requirements: Dict with keys like 'pwm_capable', 'analog_capable', etc.
        
        Returns:
            Dict mapping pin roles to pin numbers
        """
        board_pins = self.board_capabilities.get(board_type, {}).get('pins', {})
        assigned_pins = {}
        
        # Different strategies for different peripherals
        if peripheral_type == 'led':
            assigned_pins['LED'] = self._find_best_gpio(board_type, board_pins)
        
        elif peripheral_type == 'dht22' or peripheral_type == 'dht11':
            assigned_pins['DATA'] = self._find_best_gpio(board_type, board_pins)
        
        elif peripheral_type == 'servo':
            assigned_pins['SERVO'] = self._find_pwm_pin(board_type, board_pins)
        
        elif peripheral_type == 'i2c':
            i2c_pins = self._find_i2c_pins(board_type, board_pins)
            assigned_pins.update(i2c_pins)
        
        elif peripheral_type == 'spi':
            spi_pins = self._find_spi_pins(board_type, board_pins)
            assigned_pins.update(spi_pins)
        
        elif peripheral_type == 'uart':
            uart_pins = self._find_uart_pins(board_type, board_pins)
            assigned_pins.update(uart_pins)
        
        # Mark pins as used
        for role, pin in assigned_pins.items():
            self.pin_usage[pin] = peripheral_type
        
        return assigned_pins
    
    def _find_best_gpio(self, board_type: str, board_pins: Dict) -> int:
        """Find the best available GPIO pin"""
        # Default safe pins for different boards
        defaults = {
            'esp32': [2, 4, 5, 18, 19, 21, 22, 23],
            'arduino_uno': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            'arduino_mega': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            'stm32': [0, 1, 2, 3, 4, 5]
        }
        
        available_pins = defaults.get(board_type, [2])
        
        # Find first unused pin
        for pin in available_pins:
            if pin not in self.pin_usage:
                return pin
        
        return available_pins[0]  # Fallback
    
    def _find_pwm_pin(self, board_type: str, board_pins: Dict) -> int:
        """Find a PWM-capable pin"""
        pwm_pins = {
            'esp32': [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23],
            'arduino_uno': [3, 5, 6, 9, 10, 11],
            'arduino_mega': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            'stm32': [0, 1, 2, 3]
        }
        
        available = pwm_pins.get(board_type, [13])
        
        for pin in available:
            if pin not in self.pin_usage:
                return pin
        
        return available[0]
    
    def _find_i2c_pins(self, board_type: str, board_pins: Dict) -> Dict[str, int]:
        """Find I2C pins (SDA, SCL)"""
        i2c_defaults = {
            'esp32': {'SDA': 21, 'SCL': 22},
            'arduino_uno': {'SDA': 18, 'SCL': 19},  # A4, A5
            'arduino_mega': {'SDA': 20, 'SCL': 21},
            'stm32': {'SDA': 9, 'SCL': 8}
        }
        
        return i2c_defaults.get(board_type, {'SDA': 21, 'SCL': 22})
    
    def _find_spi_pins(self, board_type: str, board_pins: Dict) -> Dict[str, int]:
        """Find SPI pins (MOSI, MISO, SCK, CS)"""
        spi_defaults = {
            'esp32': {'MOSI': 23, 'MISO': 19, 'SCK': 18, 'CS': 5},
            'arduino_uno': {'MOSI': 11, 'MISO': 12, 'SCK': 13, 'CS': 10},
            'arduino_mega': {'MOSI': 51, 'MISO': 50, 'SCK': 52, 'CS': 53},
            'stm32': {'MOSI': 11, 'MISO': 12, 'SCK': 13, 'CS': 10}
        }
        
        return spi_defaults.get(board_type, spi_defaults['esp32'])
    
    def _find_uart_pins(self, board_type: str, board_pins: Dict) -> Dict[str, int]:
        """Find UART pins (TX, RX)"""
        uart_defaults = {
            'esp32': {'TX': 1, 'RX': 3},
            'arduino_uno': {'TX': 1, 'RX': 0},
            'arduino_mega': {'TX': 1, 'RX': 0},
            'stm32': {'TX': 2, 'RX': 3}
        }
        
        return uart_defaults.get(board_type, uart_defaults['esp32'])
    
    def detect_conflicts(self, board_type: str) -> List[Dict]:
        """Detect pin conflicts and return warnings"""
        conflicts = []
        
        # Check for pins used multiple times
        pin_counts = {}
        for pin, peripheral in self.pin_usage.items():
            pin_counts[pin] = pin_counts.get(pin, 0) + 1
        
        for pin, count in pin_counts.items():
            if count > 1:
                conflicts.append({
                    'pin': pin,
                    'issue': f'Pin {pin} is assigned to multiple peripherals',
                    'severity': 'error'
                })
        
        return conflicts
    
    def get_pin_usage_map(self, board_type: str) -> Dict:
        """Get visual representation of pin usage"""
        return {
            'used_pins': self.pin_usage,
            'available_pins': self._get_available_pins(board_type),
            'conflicts': self.detect_conflicts(board_type)
        }
    
    def _get_available_pins(self, board_type: str) -> List[int]:
        """Get list of available (unused) pins"""
        all_pins = {
            'esp32': list(range(0, 40)),
            'arduino_uno': list(range(0, 20)),
            'arduino_mega': list(range(0, 70)),
            'stm32': list(range(0, 50))
        }
        
        board_all_pins = all_pins.get(board_type, list(range(0, 40)))
        return [p for p in board_all_pins if p not in self.pin_usage]
    
    def reset(self):
        """Reset pin usage tracking"""
        self.pin_usage = {}
