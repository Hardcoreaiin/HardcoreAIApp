# Enhanced AI with STM32 Integration
# Automatically configures STM32 clocks and generates HAL code

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai import GeminiAI
from stm32_clock_config import STM32ClockConfigurator
from stm32_hal_generator import STM32HALGenerator
from typing import Dict, Any

class EnhancedAI(GeminiAI):
    """
    Enhanced AI with STM32 auto-configuration
    """
    
    def __init__(self):
        super().__init__()
        self.stm32_clock = STM32ClockConfigurator()
        self.stm32_hal = STM32HALGenerator()
    
    def parse_hardware_command(self, prompt: str, board_type: str) -> Dict[str, Any]:
        """
        Enhanced parsing with STM32 auto-configuration
        """
        # Get base action from parent
        action = super().parse_hardware_command(prompt, board_type)
        
        # If STM32 board, add auto-configuration
        if board_type.startswith('stm32'):
            action = self._enhance_stm32_action(action, board_type, prompt)
        
        return action
    
    def _enhance_stm32_action(self, action: Dict, board_type: str, prompt: str) -> Dict:
        """
        Add STM32-specific configuration
        """
        # Determine target frequency
        target_freq = self._detect_required_frequency(prompt, board_type)
        
        # Auto-configure clocks
        clock_config = self.stm32_clock.auto_configure(
            board_type,
            target_freq_mhz=target_freq,
            hse_freq_mhz=8  # Default 8MHz crystal
        )
        
        # Generate clock configuration code
        clock_code = self.stm32_clock.generate_code(clock_config, board_type)
        
        # Get clock summary
        clock_summary = self.stm32_clock.get_clock_summary(clock_config)
        
        # Add to action
        action['stm32_config'] = {
            'clock_config': clock_config,
            'clock_code': clock_code,
            'frequencies': clock_summary
        }
        
        # Generate HAL code for detected peripherals
        hal_code = self._generate_hal_code(action, board_type)
        if hal_code:
            action['stm32_config']['hal_code'] = hal_code
        
        # Add helpful message
        action['message'] = self._create_stm32_message(action, clock_summary)
        
        return action
    
    def _detect_required_frequency(self, prompt: str, board_type: str) -> int:
        """
        Detect required frequency from prompt
        """
        prompt_lower = prompt.lower()
        
        # Check for USB requirement
        if 'usb' in prompt_lower:
            # USB requires specific frequencies
            if board_type == 'stm32f4':
                return 168  # Max for F4 with USB
            elif board_type == 'stm32f7':
                return 216  # Max for F7 with USB
        
        # Check for low power
        if 'low power' in prompt_lower or 'battery' in prompt_lower:
            return 16  # Low frequency for power saving
        
        # Default: use maximum frequency
        max_freqs = {
            'stm32f4': 168,
            'stm32f7': 216,
            'stm32l4': 80,
            'stm32h7': 480
        }
        
        return max_freqs.get(board_type, 168)
    
    def _generate_hal_code(self, action: Dict, board_type: str) -> str:
        """
        Generate HAL initialization code for detected peripherals
        """
        hal_code_parts = []
        action_type = action.get('action', '')
        params = action.get('params', {})
        
        # UART detection
        if 'uart' in action_type.lower() or 'serial' in action_type.lower():
            baudrate = params.get('baudrate', 115200)
            hal_code_parts.append(
                self.stm32_hal.generate_uart_init(1, baudrate, 'PA9', 'PA10')
            )
        
        # SPI detection
        if 'spi' in action_type.lower():
            hal_code_parts.append(
                self.stm32_hal.generate_spi_init(1, 'Master', 'PA5', 'PA6', 'PA7')
            )
        
        # I2C detection
        if 'i2c' in action_type.lower():
            speed = 400000 if 'fast' in action_type.lower() else 100000
            hal_code_parts.append(
                self.stm32_hal.generate_i2c_init(1, speed, 'PB8', 'PB9')
            )
        
        # PWM detection
        if 'pwm' in action_type.lower() or 'servo' in action_type.lower():
            hal_code_parts.append(
                self.stm32_hal.generate_pwm_init(2, 1, 'PA0', 1000)
            )
        
        return '\n\n'.join(hal_code_parts) if hal_code_parts else ''
    
    def _create_stm32_message(self, action: Dict, freqs: Dict) -> str:
        """
        Create informative message about STM32 configuration
        """
        sysclk = freqs.get('SYSCLK', 0)
        usb_clk = freqs.get('USB', 0)
        
        msg = f"✅ STM32 configured at {sysclk:.0f} MHz"
        
        if usb_clk == 48.0:
            msg += f" (USB: {usb_clk:.0f} MHz ✓)"
        
        msg += f"\n📊 APB1: {freqs.get('APB1', 0):.0f} MHz, APB2: {freqs.get('APB2', 0):.0f} MHz"
        
        return msg


# Example usage
if __name__ == "__main__":
    ai = EnhancedAI()
    
    # Test STM32 command
    result = ai.parse_hardware_command("Create STM32F4 project with UART and USB", "stm32f4")
    
    print("Action:", result.get('action'))
    print("\nSTM32 Configuration:")
    print(result.get('message'))
    
    if 'stm32_config' in result:
        config = result['stm32_config']
        print("\nFrequencies:")
        for name, freq in config['frequencies'].items():
            print(f"  {name}: {freq:.2f} MHz")
