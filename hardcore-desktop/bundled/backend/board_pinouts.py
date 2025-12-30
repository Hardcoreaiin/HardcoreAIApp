"""
Board Pinout Database
Provides pin layout information for auto-generating visual diagrams
"""

BOARD_PINOUTS = {
    "ESP32": {
        "name": "ESP32 DevKit V1",
        "chip": "ESP32-WROOM-32",
        "layout": "dual-column",
        "left_pins": [36, 39, 34, 35, 32, 33, 25, 26, 27, 14, 12, 13],
        "right_pins": [23, 22, 1, 3, 21, 19, 18, 5, 17, 16, 4, 2, 15],
        "pin_labels": {
            36: "VP", 39: "VN", 34: "34", 35: "35",
            32: "32", 33: "33", 25: "25", 26: "26",
            27: "27", 14: "14", 12: "12", 13: "13",
            23: "23", 22: "22", 1: "TX", 3: "RX",
            21: "21", 19: "19", 18: "18", 5: "5",
            17: "17", 16: "16", 4: "4", 2: "2", 15: "15"
        }
    },
    
    "Arduino Nano": {
        "name": "Arduino Nano",
        "chip": "ATmega328P",
        "layout": "dual-column",
        "left_pins": ["D13", "D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "RESET", "RX"],
        "right_pins": ["TX", "3.3V", "AREF", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "5V", "VIN", "GND", "GND"],
        "pin_labels": {}  # Labels match pin names
    },
    
    "Arduino Uno": {
        "name": "Arduino Uno R3",
        "chip": "ATmega328P",
        "layout": "dual-column",
        "left_pins": ["D13", "D12", "D11", "D10", "D9", "D8", "D7", "D6", "D5", "D4", "D3", "D2", "GND", "AREF"],
        "right_pins": ["A0", "A1", "A2", "A3", "A4", "A5", "VIN", "GND", "5V", "3.3V", "RESET", "IOREF"],
        "pin_labels": {}
    },
    
    "Arduino Mega": {
        "name": "Arduino Mega 2560",
        "chip": "ATmega2560",
        "layout": "dual-column",
        "left_pins": list(range(53, 21, -2)),  # D53, D51, D49...D23
        "right_pins": list(range(52, 20, -2)),  # D52, D50, D48...D22
        "pin_labels": {}
    },
    
    "ESP8266": {
        "name": "NodeMCU ESP8266",
        "chip": "ESP8266",
        "layout": "dual-column",
        "left_pins": ["D0", "D1", "D2", "D3", "D4", "3.3V", "GND", "D5", "D6", "D7", "D8", "RX", "TX", "GND", "3.3V"],
        "right_pins": ["A0", "RSV", "RSV", "SD3", "SD2", "SD1", "CMD", "SD0", "CLK", "GND", "3.3V", "EN", "RST", "GND", "VIN"],
        "pin_labels": {}
    }
}

def get_board_pinout(board_type: str) -> dict:
    """
    Get pinout layout for a specific board type
    Returns pinout dict or generic fallback
    """
    # Normalize board name
    board_type = board_type.strip()
    
    # Direct match
    if board_type in BOARD_PINOUTS:
        return BOARD_PINOUTS[board_type]
    
    # Fuzzy matching
    board_lower = board_type.lower()
    for key in BOARD_PINOUTS:
        if board_lower in key.lower() or key.lower() in board_lower:
            return BOARD_PINOUTS[key]
    
    # Generic fallback for unknown boards
    return {
        "name": board_type,
        "chip": "Unknown",
        "layout": "generic",
        "pins": list(range(0, 32)),  # Generic 32-pin layout
        "pin_labels": {}
    }

def get_all_supported_boards():
    """Return list of all boards with pinout definitions"""
    return list(BOARD_PINOUTS.keys())
