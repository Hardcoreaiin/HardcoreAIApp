import os
import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional

class PlatformIOBuilder:
    """Handles firmware compilation and flashing using PlatformIO."""
    
    def __init__(self, workspace_dir: str = "firmware_workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
    
    def build_and_flash(self, firmware_code: str, board_type: str = "esp32", flash: bool = False) -> Dict[str, Any]:
        """
        Compile firmware and optionally flash to connected board.
        
        Args:
            firmware_code: Generated firmware code
            board_type: Target board (esp32, arduino, etc.)
            flash: Whether to flash to board after compilation
        
        Returns:
            Dictionary with build status and logs
        """
        try:
            # Create PlatformIO project
            project_dir = self.workspace / "current_project"
            if project_dir.exists():
                shutil.rmtree(project_dir)
            project_dir.mkdir()
            
            # Initialize PlatformIO project
            self._init_platformio_project(project_dir, board_type)
            
            # Write firmware code
            main_file = project_dir / "src" / "main.cpp"
            main_file.write_text(firmware_code)
            
            # Build
            build_result = self._compile(project_dir)
            
            if not build_result["success"]:
                return build_result
            
            # Flash if requested
            if flash:
                flash_result = self._flash(project_dir)
                return {**build_result, **flash_result}
            
            return build_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stage": "setup"
            }
    
    def _init_platformio_project(self, project_dir: Path, board_type: str):
        """Initialize PlatformIO project with platformio.ini."""
        
        # Load board definitions
        base_dir = Path(__file__).parent.parent
        board_def_path = base_dir / "orchestrator" / "board_definitions.json"
        
        # Defaults
        platform = "espressif32"
        board = "esp32dev"
        framework = "arduino"
        upload_protocol = None
        upload_speed = None
        
        if board_def_path.is_file():
            try:
                with board_def_path.open() as f:
                    defs = json.load(f)
                    if board_type in defs:
                        conf = defs[board_type].get("platformio", {})
                        platform = conf.get("platform", platform)
                        board = conf.get("board", board)
                        framework = conf.get("framework", framework)
                        upload_protocol = conf.get("upload_protocol")
                        upload_speed = conf.get("upload_speed")
            except Exception as e:
                print(f"Error loading board definitions: {e}")

        ini_content = f"""[env:default]
platform = {platform}
board = {board}
framework = {framework}
monitor_speed = 115200
"""
        if upload_protocol:
            ini_content += f"upload_protocol = {upload_protocol}\n"
        if upload_speed:
            ini_content += f"upload_speed = {upload_speed}\n"
        
        (project_dir / "platformio.ini").write_text(ini_content)
        (project_dir / "src").mkdir(exist_ok=True)
    
    def _compile(self, project_dir: Path) -> Dict[str, Any]:
        """Compile firmware using PlatformIO."""
        try:
            pio_exe = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\Scripts\pio.exe")
            if not os.path.isfile(pio_exe):
                pio_exe = "pio"  # fallback to PATH
            result = subprocess.run(
                [pio_exe, "run"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "success": result.returncode == 0,
                "stage": "compile",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "firmware_path": str(project_dir / ".pio" / "build" / "default" / "firmware.bin")
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "PlatformIO not found. Install with: pip install platformio",
                "stage": "compile"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timeout (>120 seconds)",
                "stage": "compile"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stage": "compile"
            }
    
    def _flash(self, project_dir: Path) -> Dict[str, Any]:
        """Flash compiled firmware to connected board."""
        try:
            pio_exe = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\Scripts\pio.exe")
            if not os.path.isfile(pio_exe):
                pio_exe = "pio"
            result = subprocess.run(
                [pio_exe, "run", "--target", "upload"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "flash_success": result.returncode == 0,
                "flash_stdout": result.stdout,
                "flash_stderr": result.stderr
            }
            
        except Exception as e:
            return {
                "flash_success": False,
                "flash_error": str(e)
            }
    
    def build_and_flash_stream(self, firmware_code: str, board_type: str = "esp32", flash: bool = False):
        """
        Compile and flash with real-time output streaming.
        Yields log lines as strings.
        """
        try:
            # Create PlatformIO project
            project_dir = self.workspace / "current_project"
            if project_dir.exists():
                shutil.rmtree(project_dir)
            project_dir.mkdir()
            
            # Initialize PlatformIO project
            self._init_platformio_project(project_dir, board_type)
            
            # Write firmware code
            main_file = project_dir / "src" / "main.cpp"
            main_file.write_text(firmware_code)
            
            # Build
            yield "Starting build process...\n"
            pio_exe = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\Scripts\pio.exe")
            if not os.path.isfile(pio_exe):
                pio_exe = "pio"

            # Compile process
            process = subprocess.Popen(
                [pio_exe, "run"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in process.stdout:
                yield line

            process.wait()
            if process.returncode != 0:
                yield "Build failed!\n"
                return

            if not flash:
                yield "Build successful!\n"
                return

            # Flash process
            yield "Starting flash process...\n"
            process = subprocess.Popen(
                [pio_exe, "run", "--target", "upload"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in process.stdout:
                yield line
            
            process.wait()
            if process.returncode == 0:
                yield "Flash successful!\n"
            else:
                yield "Flash failed!\n"

        except Exception as e:
            yield f"Error: {str(e)}\n"

    def _suggest_boards(self, description: str, hwid: str) -> list:
        """Suggest possible board types based on description and hwid."""
        suggestions = []
        desc_lower = description.lower()
        hwid_lower = hwid.lower()
        
        # Common USB-to-Serial patterns (wired only)
        if "ch340" in desc_lower or "ch341" in desc_lower:
            # CH340 is very common on Arduino Nano clones
            suggestions = ["arduino_nano", "arduino_uno", "esp32"]
        elif "cp210" in desc_lower or "cp21" in desc_lower:
            # CP210x is common on ESP32 boards
            suggestions = ["esp32", "arduino_nano"]
        elif "ftdi" in desc_lower or "ft232" in desc_lower:
            # FTDI is common on official Arduino boards
            suggestions = ["arduino_uno", "arduino_mega", "arduino_nano"]
        elif "usb" in desc_lower and "serial" in desc_lower:
            # Generic USB serial - could be anything
            suggestions = ["arduino_nano", "arduino_uno", "esp32", "arduino_mega"]
        else:
            # Default suggestions for unknown USB devices
            suggestions = ["arduino_nano", "arduino_uno", "esp32", "arduino_mega"]
        
        return suggestions

    def detect_connected_boards(self) -> list:
        """Detect connected boards via serial ports with detailed info.
        Returns a list of dicts with keys: port, description, board_type, driver_url (optional), pins (optional).
        """
        log_path = r"C:\Users\shriv\.gemini\antigravity\scratch\Protoforge\Hardcore.ai\orchestrator\debug_log.txt"
        with open(log_path, "a") as log:
            log.write("detect_connected_boards called\n")

        # Load driver DB and board definitions (relative to project root)
        base_dir = Path(__file__).parent.parent  # project root
        driver_path = base_dir / "orchestrator" / "driver_db.json"
        board_def_path = base_dir / "orchestrator" / "board_definitions.json"
        driver_db = {}
        board_defs = {}
        if driver_path.is_file():
            with driver_path.open() as f:
                driver_db = json.load(f)
        if board_def_path.is_file():
            with board_def_path.open() as f:
                board_defs = json.load(f)
        devices = []
        try:
            # Use explicit path if available
            pio_exe = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\Scripts\pio.exe")
            if not os.path.isfile(pio_exe):
                pio_exe = "pio"

            # Use PlatformIO JSON device list if available
            result = subprocess.run(
                [pio_exe, "device", "list", "--json-output"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            with open("debug_log.txt", "a") as log:
                log.write(f"PIO JSON Result: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}\n")

            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                for d in data:
                    # Filter out Bluetooth devices - only show USB/wired connections
                    hwid = d.get("hwid", "")
                    description = d.get("description", "")
                    
                    # Skip Bluetooth devices
                    if "bluetooth" in description.lower() or "bth" in hwid.lower() or "BTHENUM" in hwid:
                        with open("debug_log.txt", "a") as log:
                            log.write(f"Skipping Bluetooth device: {description} on {d.get('port')}\n")
                        continue
                    hwid = d.get("hwid", "")
                    description = d.get("description", "")
                    port = d.get("port", "")
                    # Parse VID:PID from hwid - handle multiple formats
                    vid_pid = None
                    vid = None
                    pid = None
                    
                    # Handle "VID:PID=1A86:7523" format (USB)
                    if "VID:PID=" in hwid:
                        vid_pid = hwid.split("VID:PID=")[1].split()[0]
                    
                    # Handle "VID&000105D6_PID&000A" format (Bluetooth)
                    elif "VID&" in hwid and "PID&" in hwid:
                        try:
                            vid_match = hwid.split("VID&")[1].split("_")[0]
                            pid_match = hwid.split("PID&")[1].split("\\")[0].split("_")[0]
                            # Convert to hex format
                            vid = f"{int(vid_match, 16):04X}"
                            pid = f"{int(pid_match, 16):04X}"
                            vid_pid = f"{vid}:{pid}"
                        except:
                            pass
                    
                    # Handle "1A86:7523" format (direct)
                    if not vid_pid:
                        for part in hwid.split():
                            if ":" in part and len(part) == 9 and all(c in "0123456789abcdefABCDEF:" for c in part):
                                vid_pid = part
                                break
                    
                    with open("debug_log.txt", "a") as log:
                        log.write(f"Processing HWID: {hwid}, Parsed VID:PID: {vid_pid}\n")

                    board_type = "unknown"
                    driver_url = None
                    pins = None
                    
                    # Try to infer from description first (for Bluetooth and other devices)
                    description_lower = description.lower()
                    hwid_lower = hwid.lower()
                    
                    if "bluetooth" in description_lower or "bth" in hwid_lower:
                        # Bluetooth device - can't determine board type from BT alone
                        # But we can check if it has VID/PID in the hwid
                        if vid_pid:
                            # Try to look it up
                            pass  # Will be handled by VID/PID lookup below
                        else:
                            board_type = "unknown"
                    elif "ch340" in description_lower or "ch341" in description_lower:
                        # CH340 USB-to-Serial - common on Arduino clones
                        board_type = "arduino_nano"  # Most common with CH340
                    elif "cp210" in description_lower or "cp21" in description_lower:
                        # CP210x USB-to-Serial - common on ESP32
                        board_type = "esp32"
                    elif "ftdi" in description_lower or "ft232" in description_lower:
                        # FTDI - could be various boards, but often Arduino
                        board_type = "arduino_uno"
                    elif "arduino" in description_lower:
                        if "nano" in description_lower:
                            board_type = "arduino_nano"
                        elif "mega" in description_lower:
                            board_type = "arduino_mega"
                        else:
                            board_type = "arduino_uno"
                    elif "esp32" in description_lower or "esp-32" in description_lower:
                        board_type = "esp32"
                    elif "stm32" in description_lower:
                        if "f4" in description_lower:
                            board_type = "stm32f4"
                        elif "f7" in description_lower:
                            board_type = "stm32f7"
                        elif "l4" in description_lower:
                            board_type = "stm32l4"
                        else:
                            board_type = "stm32f4"  # Default
                    
                    # Try VID/PID lookup if available
                    if vid_pid and board_type == "unknown":
                        try:
                            vid, pid = vid_pid.split(":")
                            # Try both lowercase and uppercase keys
                            vid_key_lower = f"0x{vid.lower()}"
                            vid_key_upper = f"0x{vid.upper()}"
                            
                            with open("debug_log.txt", "a") as log:
                                log.write(f"Loading DB from: {driver_path}\n")

                            vendor_entry = driver_db.get(vid_key_lower) or driver_db.get(vid_key_upper)
                            
                            if vendor_entry:
                                pid_key_lower = f"0x{pid.lower()}"
                                pid_key_upper = f"0x{pid.upper()}"
                                
                                product_entry = vendor_entry.get(pid_key_lower) or vendor_entry.get(pid_key_upper)
                                
                                if product_entry:
                                    with open("debug_log.txt", "a") as log:
                                        log.write(f"Found product entry: {product_entry}\n")

                                    raw_name = product_entry.get("name", "unknown")
                                    # Normalize name: remove (CH340) suffix and handle spaces
                                    board_type = raw_name.replace(" (CH340)", "").lower().replace(" ", "_")
                                    
                                    # Map common variations
                                    if "nano" in board_type:
                                        board_type = "arduino_nano"
                                    elif "uno" in board_type:
                                        board_type = "arduino_uno"
                                    elif "mega" in board_type:
                                        board_type = "arduino_mega"
                                    elif "esp32" in board_type or "esp-32" in board_type:
                                        board_type = "esp32"
                                    
                                    with open("debug_log.txt", "a") as log:
                                        log.write(f"Raw Name: '{raw_name}', Normalized: '{board_type}'\n")

                                    driver_url = product_entry.get("driver_url")
                            
                            with open("debug_log.txt", "a") as log:
                                log.write(f"  Lookup result - Board: {board_type}\n")

                            if board_type and board_type in board_defs:
                                pins = board_defs[board_type].get("pins")
                        except Exception as e:
                            with open("debug_log.txt", "a") as log:
                                log.write(f"  Error parsing VID/PID {vid_pid}: {e}\n")
                            print(f"Error parsing VID/PID {vid_pid}: {e}")
                    
                    devices.append({
                        "port": port,
                        "description": description,
                        "hwid": hwid,
                        "board_type": board_type,
                        "driver_url": driver_url,
                        "pins": pins,
                        "label": f"{description} ({port})",
                        "needs_manual_selection": board_type == "unknown",
                        "suggested_boards": self._suggest_boards(description, hwid) if board_type == "unknown" else []
                    })
            
                return devices
                
        except Exception as e:
            with open("debug_log.txt", "a") as log:
                log.write(f"JSON detection failed: {e}\n")
            pass
        
        # Fallback to text parsing (unchanged)
        try:
            with open("debug_log.txt", "a") as log:
                log.write("Falling back to text parsing\n")

            pio_exe = os.path.expanduser(r"~\AppData\Roaming\Python\Python312\Scripts\pio.exe")
            if not os.path.isfile(pio_exe):
                pio_exe = "pio"
                
            result = subprocess.run(
                [pio_exe, "device", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_device = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    if current_device:
                        # Skip Bluetooth devices
                        hwid = current_device.get("hwid", "")
                        description = current_device.get("description", "").lower()
                        if "bluetooth" not in description and "bth" not in hwid.lower() and "BTHENUM" not in hwid:
                            devices.append(current_device)
                        current_device = {}
                    continue
                if line.startswith("CN"): continue
                if line.startswith("COM") or line.startswith("/dev/"):
                    current_device = {"port": line, "description": "Unknown Device", "board_type": "unknown"}
                elif "Hardware ID" in line:
                    hwid = line.split(":")[-1].strip()
                    current_device["hwid"] = hwid
                    if "10C4:EA60" in hwid:
                        current_device["board_type"] = "esp32"
                    elif "2341:0043" in hwid:
                        current_device["board_type"] = "arduino"
                elif "Description" in line:
                    current_device["description"] = line.split(":", 1)[1].strip()
            if current_device:
                # Skip Bluetooth devices
                hwid = current_device.get("hwid", "")
                description = current_device.get("description", "").lower()
                if "bluetooth" not in description and "bth" not in hwid.lower() and "BTHENUM" not in hwid:
                    devices.append(current_device)
            return devices
        except Exception as e:
            error_msg = str(e)
            with open("debug_log.txt", "a") as log:
                log.write(f"Board detection error: {error_msg}\n")
            
            # Return helpful error message
            return [{
                "error": error_msg,
                "description": "Detection Error",
                "port": "N/A",
                "board_type": "unknown",
                "suggestion": "Make sure PlatformIO is installed and board is connected. Try: pip install platformio"
            }]
