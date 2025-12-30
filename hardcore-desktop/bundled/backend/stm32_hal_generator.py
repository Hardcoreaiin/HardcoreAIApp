# STM32 HAL Code Generator
# Automatically generates peripheral initialization code

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PinConfig:
    """GPIO Pin Configuration"""
    port: str  # 'A', 'B', 'C', etc.
    pin: int   # 0-15
    af: int    # Alternate function number
    mode: str  # 'GPIO_MODE_AF_PP', 'GPIO_MODE_AF_OD', etc.
    pull: str  # 'GPIO_NOPULL', 'GPIO_PULLUP', 'GPIO_PULLDOWN'
    speed: str # 'GPIO_SPEED_FREQ_LOW', 'GPIO_SPEED_FREQ_HIGH', etc.

class STM32HALGenerator:
    """
    Generate HAL initialization code for STM32 peripherals
    Eliminates need for CubeMX
    """
    
    def __init__(self):
        # STM32F4 Alternate Function mappings
        self.af_mappings = {
            'USART1': {'TX': {'PA9': 7, 'PB6': 7}, 'RX': {'PA10': 7, 'PB7': 7}},
            'USART2': {'TX': {'PA2': 7, 'PD5': 7}, 'RX': {'PA3': 7, 'PD6': 7}},
            'USART3': {'TX': {'PB10': 7, 'PC10': 7, 'PD8': 7}, 'RX': {'PB11': 7, 'PC11': 7, 'PD9': 7}},
            'SPI1': {'SCK': {'PA5': 5, 'PB3': 5}, 'MISO': {'PA6': 5, 'PB4': 5}, 'MOSI': {'PA7': 5, 'PB5': 5}},
            'SPI2': {'SCK': {'PB10': 5, 'PB13': 5}, 'MISO': {'PB14': 5, 'PC2': 5}, 'MOSI': {'PB15': 5, 'PC3': 5}},
            'I2C1': {'SCL': {'PB6': 4, 'PB8': 4}, 'SDA': {'PB7': 4, 'PB9': 4}},
            'I2C2': {'SCL': {'PB10': 4, 'PF1': 4}, 'SDA': {'PB11': 4, 'PF0': 4}},
            'TIM1': {'CH1': {'PA8': 1, 'PE9': 1}, 'CH2': {'PA9': 1, 'PE11': 1}},
            'TIM2': {'CH1': {'PA0': 1, 'PA5': 1, 'PA15': 1}, 'CH2': {'PA1': 1, 'PB3': 1}},
            'TIM3': {'CH1': {'PA6': 2, 'PB4': 2, 'PC6': 2}, 'CH2': {'PA7': 2, 'PB5': 2, 'PC7': 2}},
        }
    
    def generate_uart_init(self, uart_num: int, baudrate: int, 
                          tx_pin: str, rx_pin: str) -> str:
        """
        Generate UART/USART initialization code
        
        Args:
            uart_num: 1, 2, 3, etc.
            baudrate: 9600, 115200, etc.
            tx_pin: 'PA9', 'PB6', etc.
            rx_pin: 'PA10', 'PB7', etc.
        """
        uart_name = f"USART{uart_num}"
        handle_name = f"huart{uart_num}"
        
        # Get AF numbers
        tx_af = self.af_mappings[uart_name]['TX'].get(tx_pin, 7)
        rx_af = self.af_mappings[uart_name]['RX'].get(rx_pin, 7)
        
        # Parse pin names
        tx_port, tx_num = tx_pin[1], int(tx_pin[2:])
        rx_port, rx_num = rx_pin[1], int(rx_pin[2:])
        
        code = f"""
/* UART{uart_num} Initialization */
UART_HandleTypeDef {handle_name};

void MX_{uart_name}_Init(void)
{{
    {handle_name}.Instance = {uart_name};
    {handle_name}.Init.BaudRate = {baudrate};
    {handle_name}.Init.WordLength = UART_WORDLENGTH_8B;
    {handle_name}.Init.StopBits = UART_STOPBITS_1;
    {handle_name}.Init.Parity = UART_PARITY_NONE;
    {handle_name}.Init.Mode = UART_MODE_TX_RX;
    {handle_name}.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    {handle_name}.Init.OverSampling = UART_OVERSAMPLING_16;
    
    if (HAL_UART_Init(&{handle_name}) != HAL_OK) {{
        Error_Handler();
    }}
}}

void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{{
    GPIO_InitTypeDef GPIO_InitStruct = {{0}};
    
    if(uartHandle->Instance == {uart_name}) {{
        /* Peripheral clock enable */
        __HAL_RCC_{uart_name}_CLK_ENABLE();
        __HAL_RCC_GPIO{tx_port}_CLK_ENABLE();
        __HAL_RCC_GPIO{rx_port}_CLK_ENABLE();
        
        /* UART GPIO Configuration */
        /* {tx_pin} -> {uart_name}_TX */
        GPIO_InitStruct.Pin = GPIO_PIN_{tx_num};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF{tx_af}_{uart_name};
        HAL_GPIO_Init(GPIO{tx_port}, &GPIO_InitStruct);
        
        /* {rx_pin} -> {uart_name}_RX */
        GPIO_InitStruct.Pin = GPIO_PIN_{rx_num};
        GPIO_InitStruct.Alternate = GPIO_AF{rx_af}_{uart_name};
        HAL_GPIO_Init(GPIO{rx_port}, &GPIO_InitStruct);
    }}
}}
"""
        return code.strip()
    
    def generate_spi_init(self, spi_num: int, mode: str, 
                         sck_pin: str, miso_pin: str, mosi_pin: str) -> str:
        """
        Generate SPI initialization code
        
        Args:
            spi_num: 1, 2, 3
            mode: 'Master' or 'Slave'
            sck_pin, miso_pin, mosi_pin: Pin names
        """
        spi_name = f"SPI{spi_num}"
        handle_name = f"hspi{spi_num}"
        
        # Parse pins
        sck_port, sck_num = sck_pin[1], int(sck_pin[2:])
        miso_port, miso_num = miso_pin[1], int(miso_pin[2:])
        mosi_port, mosi_num = mosi_pin[1], int(mosi_pin[2:])
        
        # Get AF
        sck_af = self.af_mappings[spi_name]['SCK'].get(sck_pin, 5)
        miso_af = self.af_mappings[spi_name]['MISO'].get(miso_pin, 5)
        mosi_af = self.af_mappings[spi_name]['MOSI'].get(mosi_pin, 5)
        
        code = f"""
/* SPI{spi_num} Initialization */
SPI_HandleTypeDef {handle_name};

void MX_{spi_name}_Init(void)
{{
    {handle_name}.Instance = {spi_name};
    {handle_name}.Init.Mode = SPI_MODE_{mode.upper()};
    {handle_name}.Init.Direction = SPI_DIRECTION_2LINES;
    {handle_name}.Init.DataSize = SPI_DATASIZE_8BIT;
    {handle_name}.Init.CLKPolarity = SPI_POLARITY_LOW;
    {handle_name}.Init.CLKPhase = SPI_PHASE_1EDGE;
    {handle_name}.Init.NSS = SPI_NSS_SOFT;
    {handle_name}.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_16;
    {handle_name}.Init.FirstBit = SPI_FIRSTBIT_MSB;
    {handle_name}.Init.TIMode = SPI_TIMODE_DISABLE;
    {handle_name}.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    
    if (HAL_SPI_Init(&{handle_name}) != HAL_OK) {{
        Error_Handler();
    }}
}}

void HAL_SPI_MspInit(SPI_HandleTypeDef* spiHandle)
{{
    GPIO_InitTypeDef GPIO_InitStruct = {{0}};
    
    if(spiHandle->Instance == {spi_name}) {{
        /* Peripheral clock enable */
        __HAL_RCC_{spi_name}_CLK_ENABLE();
        __HAL_RCC_GPIO{sck_port}_CLK_ENABLE();
        __HAL_RCC_GPIO{miso_port}_CLK_ENABLE();
        __HAL_RCC_GPIO{mosi_port}_CLK_ENABLE();
        
        /* SPI GPIO Configuration */
        /* SCK */
        GPIO_InitStruct.Pin = GPIO_PIN_{sck_num};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF{sck_af}_{spi_name};
        HAL_GPIO_Init(GPIO{sck_port}, &GPIO_InitStruct);
        
        /* MISO */
        GPIO_InitStruct.Pin = GPIO_PIN_{miso_num};
        GPIO_InitStruct.Alternate = GPIO_AF{miso_af}_{spi_name};
        HAL_GPIO_Init(GPIO{miso_port}, &GPIO_InitStruct);
        
        /* MOSI */
        GPIO_InitStruct.Pin = GPIO_PIN_{mosi_num};
        GPIO_InitStruct.Alternate = GPIO_AF{mosi_af}_{spi_name};
        HAL_GPIO_Init(GPIO{mosi_port}, &GPIO_InitStruct);
    }}
}}
"""
        return code.strip()
    
    def generate_i2c_init(self, i2c_num: int, speed: int,
                         scl_pin: str, sda_pin: str) -> str:
        """
        Generate I2C initialization code
        
        Args:
            i2c_num: 1, 2, 3
            speed: 100000 (standard), 400000 (fast)
            scl_pin, sda_pin: Pin names
        """
        i2c_name = f"I2C{i2c_num}"
        handle_name = f"hi2c{i2c_num}"
        
        # Parse pins
        scl_port, scl_num = scl_pin[1], int(scl_pin[2:])
        sda_port, sda_num = sda_pin[1], int(sda_pin[2:])
        
        # Get AF
        scl_af = self.af_mappings[i2c_name]['SCL'].get(scl_pin, 4)
        sda_af = self.af_mappings[i2c_name]['SDA'].get(sda_pin, 4)
        
        code = f"""
/* I2C{i2c_num} Initialization */
I2C_HandleTypeDef {handle_name};

void MX_{i2c_name}_Init(void)
{{
    {handle_name}.Instance = {i2c_name};
    {handle_name}.Init.ClockSpeed = {speed};
    {handle_name}.Init.DutyCycle = I2C_DUTYCYCLE_2;
    {handle_name}.Init.OwnAddress1 = 0;
    {handle_name}.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    {handle_name}.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    {handle_name}.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    {handle_name}.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    
    if (HAL_I2C_Init(&{handle_name}) != HAL_OK) {{
        Error_Handler();
    }}
}}

void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{{
    GPIO_InitTypeDef GPIO_InitStruct = {{0}};
    
    if(i2cHandle->Instance == {i2c_name}) {{
        /* Peripheral clock enable */
        __HAL_RCC_{i2c_name}_CLK_ENABLE();
        __HAL_RCC_GPIO{scl_port}_CLK_ENABLE();
        __HAL_RCC_GPIO{sda_port}_CLK_ENABLE();
        
        /* I2C GPIO Configuration */
        /* SCL */
        GPIO_InitStruct.Pin = GPIO_PIN_{scl_num};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF{scl_af}_{i2c_name};
        HAL_GPIO_Init(GPIO{scl_port}, &GPIO_InitStruct);
        
        /* SDA */
        GPIO_InitStruct.Pin = GPIO_PIN_{sda_num};
        GPIO_InitStruct.Alternate = GPIO_AF{sda_af}_{i2c_name};
        HAL_GPIO_Init(GPIO{sda_port}, &GPIO_InitStruct);
    }}
}}
"""
        return code.strip()
    
    def generate_pwm_init(self, tim_num: int, channel: int, 
                         pin: str, frequency_hz: int) -> str:
        """
        Generate PWM (Timer) initialization code
        
        Args:
            tim_num: 1, 2, 3, etc.
            channel: 1, 2, 3, 4
            pin: Pin name
            frequency_hz: PWM frequency
        """
        tim_name = f"TIM{tim_num}"
        handle_name = f"htim{tim_num}"
        
        # Parse pin
        port, pin_num = pin[1], int(pin[2:])
        
        # Get AF
        ch_name = f"CH{channel}"
        af = self.af_mappings.get(tim_name, {}).get(ch_name, {}).get(pin, 1)
        
        code = f"""
/* TIM{tim_num} PWM Initialization */
TIM_HandleTypeDef {handle_name};

void MX_{tim_name}_Init(void)
{{
    TIM_OC_InitTypeDef sConfigOC = {{0}};
    
    {handle_name}.Instance = {tim_name};
    {handle_name}.Init.Prescaler = 84-1;  // Adjust for desired frequency
    {handle_name}.Init.CounterMode = TIM_COUNTERMODE_UP;
    {handle_name}.Init.Period = 1000-1;   // Adjust for desired frequency
    {handle_name}.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    {handle_name}.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    
    if (HAL_TIM_PWM_Init(&{handle_name}) != HAL_OK) {{
        Error_Handler();
    }}
    
    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = 500;  // 50% duty cycle
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    
    if (HAL_TIM_PWM_ConfigChannel(&{handle_name}, &sConfigOC, TIM_CHANNEL_{channel}) != HAL_OK) {{
        Error_Handler();
    }}
    
    HAL_TIM_PWM_Start(&{handle_name}, TIM_CHANNEL_{channel});
}}

void HAL_TIM_PWM_MspInit(TIM_HandleTypeDef* timHandle)
{{
    GPIO_InitTypeDef GPIO_InitStruct = {{0}};
    
    if(timHandle->Instance == {tim_name}) {{
        /* Peripheral clock enable */
        __HAL_RCC_{tim_name}_CLK_ENABLE();
        __HAL_RCC_GPIO{port}_CLK_ENABLE();
        
        /* PWM GPIO Configuration */
        GPIO_InitStruct.Pin = GPIO_PIN_{pin_num};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
        GPIO_InitStruct.Alternate = GPIO_AF{af}_{tim_name};
        HAL_GPIO_Init(GPIO{port}, &GPIO_InitStruct);
    }}
}}
"""
        return code.strip()


# Example usage
if __name__ == "__main__":
    generator = STM32HALGenerator()
    
    print("=== UART1 Init (115200 baud, PA9/PA10) ===")
    print(generator.generate_uart_init(1, 115200, 'PA9', 'PA10'))
    
    print("\n\n=== SPI1 Init (Master mode) ===")
    print(generator.generate_spi_init(1, 'Master', 'PA5', 'PA6', 'PA7'))
    
    print("\n\n=== I2C1 Init (400kHz, PB8/PB9) ===")
    print(generator.generate_i2c_init(1, 400000, 'PB8', 'PB9'))
    
    print("\n\n=== TIM2 PWM Init (CH1, PA0) ===")
    print(generator.generate_pwm_init(2, 1, 'PA0', 1000))
