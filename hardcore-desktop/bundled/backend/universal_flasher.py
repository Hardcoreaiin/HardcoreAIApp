from typing import Generator
from platformio_builder import PlatformIOBuilder

class UniversalFlasher:
    """
    Universal flasher that handles firmware flashing for any supported board.
    Wraps PlatformIOBuilder to provide a simplified interface.
    """
    
    def __init__(self):
        self.builder = PlatformIOBuilder()
        
    def flash(self, firmware_code: str, board_type: str, port: str = None) -> Generator[str, None, None]:
        """
        Flash firmware to the specified board.
        
        Args:
            firmware_code: The C++ firmware code to flash.
            board_type: The type of board (e.g., 'arduino_uno', 'stm32_f401re').
            port: Optional serial port (e.g., 'COM3'). If provided, PlatformIO might use it,
                  though PlatformIO usually auto-detects based on board config.
        
        Yields:
            Log lines from the build and flash process.
        """
        # Note: PlatformIO usually handles port selection automatically if only one board of that type is connected.
        # If we need to force a port, we might need to pass upload_port to platformio.ini or command line.
        # For now, we rely on PlatformIO's auto-detection or the config in board_definitions.json.
        
        # We could inject 'upload_port = {port}' into platformio.ini if port is provided,
        # but PlatformIOBuilder._init_platformio_project would need to support that.
        # Given the current implementation, we just delegate to build_and_flash_stream.
        
        yield f"Initializing universal flash for board: {board_type}\n"
        
        for line in self.builder.build_and_flash_stream(firmware_code, board_type, flash=True):
            yield line
