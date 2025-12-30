"""
Bluetooth Flasher for ESP32 devices
"""
import time
import serial
from typing import Generator, Optional
from pathlib import Path

class BluetoothFlasher:
    """Handles firmware flashing for ESP32 devices via Bluetooth Serial (SPP)."""
    
    def flash_via_bluetooth(self, firmware_bin_path: str, port: str) -> Generator[str, None, None]:
        """
        Flash firmware to ESP32 device via Bluetooth Serial Port.
        
        Args:
            firmware_bin_path: Path to compiled .bin file
            port: COM port associated with the Bluetooth device (e.g., 'COM4' on Windows, '/dev/rfcomm0' on Linux)
        
        Yields:
            Status messages
        """
        try:
            firmware_path = Path(firmware_bin_path)
            if not firmware_path.exists():
                yield f"Error: Firmware file not found: {firmware_bin_path}\n"
                return
            
            yield f"Opening Bluetooth serial port {port}...\n"
            
            # Open serial connection
            # Note: Bluetooth serial can be slow, so we use a conservative baud rate if possible,
            # but usually SPP ignores baud rate settings.
            try:
                ser = serial.Serial(port, 115200, timeout=2, write_timeout=10)
            except serial.SerialException as e:
                yield f"❌ Failed to open port {port}: {str(e)}\n"
                return

            yield f"Connected to {port}. Preparing to flash...\n"
            
            # Read firmware binary
            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()
            
            firmware_size = len(firmware_data)
            yield f"Firmware size: {firmware_size} bytes\n"
            
            # Custom simple protocol for this example:
            # 1. Send "START_OTA:{size}"
            # 2. Wait for "OK"
            # 3. Send data in chunks
            # 4. Wait for "SUCCESS"
            
            # NOTE: This requires the ESP32 to be running a sketch that accepts this protocol over SerialBT!
            # Standard ESP32 OTA is over WiFi. Bluetooth OTA requires custom implementation on the device side.
            # Assuming the user has such a setup or we are using a standard tool wrapper.
            # If we are just sending the binary stream, we might need to know what the device expects.
            
            # For now, let's assume a simple raw stream or a specific handshake.
            # Since standard esptool doesn't support Bluetooth SPP directly without mapping,
            # we will assume the device is listening for a specific OTA command on the SerialBT stream.
            
            # Send Start Command
            start_cmd = f"OTA_START:{firmware_size}\n"
            ser.write(start_cmd.encode())
            yield "Sent OTA start command...\n"
            
            # Wait for acknowledgement
            # This is blocking, but we have a timeout
            response = ser.readline().decode().strip()
            if "OK" not in response:
                # Try one more time?
                yield f"Device response: {response}\n"
                if "OK" not in response:
                    yield "❌ Device did not acknowledge OTA start. Make sure it's in OTA mode.\n"
                    ser.close()
                    return
            
            yield "Device ready. Uploading...\n"
            
            chunk_size = 1024 # 1KB chunks
            total_sent = 0
            
            for i in range(0, firmware_size, chunk_size):
                chunk = firmware_data[i:i+chunk_size]
                ser.write(chunk)
                total_sent += len(chunk)
                
                # Calculate progress
                progress = (total_sent / firmware_size) * 100
                yield f"Progress: {progress:.1f}%\n"
                
                # Small delay to prevent buffer overflow on receiver
                time.sleep(0.05)
                
                # Check for errors occasionally?
                if ser.in_waiting:
                    resp = ser.read(ser.in_waiting).decode(errors='ignore')
                    if "ERROR" in resp:
                        yield f"❌ Error reported by device: {resp}\n"
                        ser.close()
                        return
            
            yield "Upload complete. Waiting for confirmation...\n"
            
            # Wait for final confirmation
            start_time = time.time()
            success = False
            while time.time() - start_time < 10: # 10s timeout
                if ser.in_waiting:
                    line = ser.readline().decode(errors='ignore').strip()
                    if "SUCCESS" in line or "OTA Complete" in line:
                        success = True
                        break
                time.sleep(0.1)
            
            ser.close()
            
            if success:
                yield "✅ Firmware flashed successfully via Bluetooth!\n"
            else:
                yield "⚠️ Upload finished but no confirmation received.\n"
                
        except Exception as e:
            yield f"❌ Bluetooth flash error: {str(e)}\n"
            if 'ser' in locals() and ser.is_open:
                ser.close()
