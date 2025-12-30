# STM32 Clock Configuration Engine
# Automatically configures optimal clock tree - eliminates CubeMX dependency

from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ClockConfig:
    """STM32 Clock Configuration"""
    hse_freq_mhz: int
    target_sysclk_mhz: int
    pll_m: int
    pll_n: int
    pll_p: int
    pll_q: int
    ahb_prescaler: int
    apb1_prescaler: int
    apb2_prescaler: int
    flash_latency: int
    
class STM32ClockConfigurator:
    """
    Automatic STM32 clock tree configuration
    Supports: STM32F4, STM32F7, STM32L4, STM32H7
    """
    
    def __init__(self):
        # MCU-specific limits
        self.mcu_specs = {
            'stm32f4': {
                'max_sysclk': 168,
                'max_apb1': 42,
                'max_apb2': 84,
                'pll_vco_min': 100,
                'pll_vco_max': 432,
                'pll_input_min': 1,
                'pll_input_max': 2,
            },
            'stm32f7': {
                'max_sysclk': 216,
                'max_apb1': 54,
                'max_apb2': 108,
                'pll_vco_min': 100,
                'pll_vco_max': 432,
                'pll_input_min': 1,
                'pll_input_max': 2,
            },
            'stm32l4': {
                'max_sysclk': 80,
                'max_apb1': 80,
                'max_apb2': 80,
                'pll_vco_min': 64,
                'pll_vco_max': 344,
                'pll_input_min': 4,
                'pll_input_max': 16,
            },
            'stm32h7': {
                'max_sysclk': 480,
                'max_apb1': 120,
                'max_apb2': 120,
                'pll_vco_min': 150,
                'pll_vco_max': 960,
                'pll_input_min': 1,
                'pll_input_max': 16,
            }
        }
    
    def auto_configure(self, mcu_type: str, target_freq_mhz: int = None, 
                       hse_freq_mhz: int = 8) -> ClockConfig:
        """
        Automatically configure optimal clock settings
        
        Args:
            mcu_type: 'stm32f4', 'stm32f7', 'stm32l4', 'stm32h7'
            target_freq_mhz: Desired system clock (None = max)
            hse_freq_mhz: External crystal frequency
        
        Returns:
            ClockConfig with optimal settings
        """
        mcu_type = mcu_type.lower()
        specs = self.mcu_specs.get(mcu_type)
        
        if not specs:
            raise ValueError(f"Unsupported MCU type: {mcu_type}")
        
        # Use max frequency if not specified
        if target_freq_mhz is None:
            target_freq_mhz = specs['max_sysclk']
        
        # Calculate optimal PLL settings
        pll_m, pll_n, pll_p, pll_q = self._calculate_pll(
            hse_freq_mhz, target_freq_mhz, specs
        )
        
        # Calculate bus prescalers
        ahb_prescaler = 1
        apb1_prescaler = self._calculate_apb_prescaler(
            target_freq_mhz, specs['max_apb1']
        )
        apb2_prescaler = self._calculate_apb_prescaler(
            target_freq_mhz, specs['max_apb2']
        )
        
        # Calculate flash latency
        flash_latency = self._calculate_flash_latency(target_freq_mhz, mcu_type)
        
        return ClockConfig(
            hse_freq_mhz=hse_freq_mhz,
            target_sysclk_mhz=target_freq_mhz,
            pll_m=pll_m,
            pll_n=pll_n,
            pll_p=pll_p,
            pll_q=pll_q,
            ahb_prescaler=ahb_prescaler,
            apb1_prescaler=apb1_prescaler,
            apb2_prescaler=apb2_prescaler,
            flash_latency=flash_latency
        )
    
    def _calculate_pll(self, hse_mhz: int, target_mhz: int, 
                       specs: Dict) -> Tuple[int, int, int, int]:
        """
        Calculate optimal PLL multipliers and dividers
        
        PLL formula: VCO = (HSE / M) * N
                     SYSCLK = VCO / P
                     USB = VCO / Q (should be 48 MHz)
        """
        best_error = float('inf')
        best_config = (2, 168, 2, 7)  # Default fallback
        
        # Try different M values (PLL input divider)
        for m in range(2, 64):
            pll_input = hse_mhz / m
            
            # Check if PLL input is in valid range
            if not (specs['pll_input_min'] <= pll_input <= specs['pll_input_max']):
                continue
            
            # Try different N values (PLL multiplier)
            for n in range(50, 433):
                vco = pll_input * n
                
                # Check if VCO is in valid range
                if not (specs['pll_vco_min'] <= vco <= specs['pll_vco_max']):
                    continue
                
                # Try different P values (SYSCLK divider)
                for p in [2, 4, 6, 8]:
                    sysclk = vco / p
                    
                    # Check if SYSCLK matches target
                    error = abs(sysclk - target_mhz)
                    
                    if error < best_error and sysclk <= specs['max_sysclk']:
                        # Calculate Q for USB (48 MHz)
                        q = round(vco / 48)
                        if 2 <= q <= 15:
                            best_error = error
                            best_config = (m, n, p, q)
                            
                            # Perfect match found
                            if error == 0:
                                return best_config
        
        return best_config
    
    def _calculate_apb_prescaler(self, sysclk_mhz: int, max_apb_mhz: int) -> int:
        """Calculate APB prescaler to stay within limits"""
        prescalers = [1, 2, 4, 8, 16]
        
        for prescaler in prescalers:
            apb_freq = sysclk_mhz / prescaler
            if apb_freq <= max_apb_mhz:
                return prescaler
        
        return 16  # Maximum prescaler
    
    def _calculate_flash_latency(self, sysclk_mhz: int, mcu_type: str) -> int:
        """
        Calculate required flash wait states
        Based on voltage range and frequency
        """
        # Assuming 3.3V operation (voltage range 2.7-3.6V)
        latency_table = {
            'stm32f4': [
                (30, 0), (60, 1), (90, 2), (120, 3), (150, 4), (168, 5)
            ],
            'stm32f7': [
                (30, 0), (60, 1), (90, 2), (120, 3), (150, 4), 
                (180, 5), (210, 6), (216, 7)
            ],
            'stm32l4': [
                (16, 0), (32, 1), (48, 2), (64, 3), (80, 4)
            ],
            'stm32h7': [
                (70, 0), (140, 1), (210, 2), (280, 3), (480, 4)
            ]
        }
        
        table = latency_table.get(mcu_type, latency_table['stm32f4'])
        
        for freq_limit, latency in table:
            if sysclk_mhz <= freq_limit:
                return latency
        
        return table[-1][1]  # Return max latency
    
    def generate_code(self, config: ClockConfig, mcu_type: str) -> str:
        """
        Generate complete SystemClock_Config() function
        
        Returns:
            C code for clock configuration
        """
        code = f"""
/**
 * @brief System Clock Configuration
 * @note Auto-generated by Hardcore.ai
 * Target: {config.target_sysclk_mhz} MHz
 */
void SystemClock_Config(void)
{{
    RCC_OscInitTypeDef RCC_OscInitStruct = {{0}};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {{0}};

    /** Configure the main internal regulator output voltage */
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    /** Initializes the RCC Oscillators according to the specified parameters */
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    RCC_OscInitStruct.PLL.PLLM = {config.pll_m};
    RCC_OscInitStruct.PLL.PLLN = {config.pll_n};
    RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV{config.pll_p};
    RCC_OscInitStruct.PLL.PLLQ = {config.pll_q};
    
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {{
        Error_Handler();
    }}

    /** Initializes the CPU, AHB and APB buses clocks */
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV{config.ahb_prescaler};
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV{config.apb1_prescaler};
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV{config.apb2_prescaler};

    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_{config.flash_latency}) != HAL_OK) {{
        Error_Handler();
    }}
}}

/**
 * @brief Error Handler
 */
void Error_Handler(void)
{{
    __disable_irq();
    while (1) {{
        // Error occurred during clock configuration
    }}
}}
"""
        return code.strip()
    
    def get_clock_summary(self, config: ClockConfig) -> Dict[str, float]:
        """
        Calculate actual clock frequencies
        
        Returns:
            Dictionary with all clock frequencies in MHz
        """
        vco = (config.hse_freq_mhz / config.pll_m) * config.pll_n
        sysclk = vco / config.pll_p
        usb_clk = vco / config.pll_q
        ahb_clk = sysclk / config.ahb_prescaler
        apb1_clk = ahb_clk / config.apb1_prescaler
        apb2_clk = ahb_clk / config.apb2_prescaler
        
        return {
            'VCO': vco,
            'SYSCLK': sysclk,
            'AHB': ahb_clk,
            'APB1': apb1_clk,
            'APB2': apb2_clk,
            'USB': usb_clk,
            'APB1_Timer': apb1_clk * (2 if config.apb1_prescaler > 1 else 1),
            'APB2_Timer': apb2_clk * (2 if config.apb2_prescaler > 1 else 1),
        }


# Example usage
if __name__ == "__main__":
    configurator = STM32ClockConfigurator()
    
    # Configure STM32F4 for 168 MHz
    config = configurator.auto_configure('stm32f4', target_freq_mhz=168, hse_freq_mhz=8)
    
    print("Clock Configuration:")
    print(f"  PLL: M={config.pll_m}, N={config.pll_n}, P={config.pll_p}, Q={config.pll_q}")
    print(f"  Flash Latency: {config.flash_latency} wait states")
    
    print("\nActual Frequencies:")
    freqs = configurator.get_clock_summary(config)
    for name, freq in freqs.items():
        print(f"  {name}: {freq:.2f} MHz")
    
    print("\nGenerated Code:")
    print(configurator.generate_code(config, 'stm32f4'))
