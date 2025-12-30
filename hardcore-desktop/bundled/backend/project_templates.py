# Project Templates System
# Pre-configured templates for common embedded projects

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ProjectTemplate:
    """Project template definition"""
    name: str
    description: str
    board_type: str
    code: str
    libraries: List[str]
    wiring: List[Dict[str, str]]

class ProjectTemplates:
    """
    Manages project templates for quick start
    """
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """Load all available templates"""
        return {
            'blink_led': self._blink_led_template(),
            'uart_echo': self._uart_echo_template(),
            'i2c_sensor': self._i2c_sensor_template(),
            'spi_display': self._spi_display_template(),
            'pwm_motor': self._pwm_motor_template(),
            'freertos_starter': self._freertos_template(),
            'stm32_usb': self._stm32_usb_template(),
        }
    
    def _blink_led_template(self) -> ProjectTemplate:
        """Basic LED blink template"""
        code = """#include <Arduino.h>

#define LED_PIN 2

void setup() {
    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    digitalWrite(LED_PIN, HIGH);
    delay(1000);
    digitalWrite(LED_PIN, LOW);
    delay(1000);
}
"""
        return ProjectTemplate(
            name="Blink LED",
            description="Simple LED blink - Hello World for embedded",
            board_type="esp32",
            code=code,
            libraries=[],
            wiring=[
                {"component": "LED Anode", "pin": "GPIO 2"},
                {"component": "LED Cathode", "pin": "GND (via 220Ω resistor)"}
            ]
        )
    
    def _uart_echo_template(self) -> ProjectTemplate:
        """UART echo template"""
        code = """#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    Serial.println("UART Echo Ready!");
}

void loop() {
    if (Serial.available()) {
        char c = Serial.read();
        Serial.print("Echo: ");
        Serial.println(c);
    }
}
"""
        return ProjectTemplate(
            name="UART Echo",
            description="Serial communication echo server",
            board_type="esp32",
            code=code,
            libraries=[],
            wiring=[]
        )
    
    def _i2c_sensor_template(self) -> ProjectTemplate:
        """I2C sensor reader template"""
        code = """#include <Arduino.h>
#include <Wire.h>

#define I2C_SDA 21
#define I2C_SCL 22

void setup() {
    Serial.begin(115200);
    Wire.begin(I2C_SDA, I2C_SCL);
    Serial.println("I2C Scanner Ready!");
    
    // Scan for I2C devices
    scanI2C();
}

void loop() {
    // Read sensor data here
    delay(1000);
}

void scanI2C() {
    Serial.println("Scanning I2C bus...");
    byte count = 0;
    
    for (byte i = 1; i < 127; i++) {
        Wire.beginTransmission(i);
        if (Wire.endTransmission() == 0) {
            Serial.print("Found device at 0x");
            Serial.println(i, HEX);
            count++;
        }
    }
    
    Serial.print("Found ");
    Serial.print(count);
    Serial.println(" device(s)");
}
"""
        return ProjectTemplate(
            name="I2C Sensor Reader",
            description="Read data from I2C sensors",
            board_type="esp32",
            code=code,
            libraries=["Wire"],
            wiring=[
                {"component": "Sensor SDA", "pin": "GPIO 21"},
                {"component": "Sensor SCL", "pin": "GPIO 22"},
                {"component": "Sensor VCC", "pin": "3.3V"},
                {"component": "Sensor GND", "pin": "GND"}
            ]
        )
    
    def _spi_display_template(self) -> ProjectTemplate:
        """SPI display template"""
        code = """#include <Arduino.h>
#include <SPI.h>

#define SPI_SCK  18
#define SPI_MISO 19
#define SPI_MOSI 23
#define SPI_CS   5

void setup() {
    Serial.begin(115200);
    
    SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI, SPI_CS);
    SPI.setFrequency(1000000); // 1 MHz
    
    Serial.println("SPI Display Ready!");
}

void loop() {
    // Send data to display
    delay(100);
}
"""
        return ProjectTemplate(
            name="SPI Display",
            description="Control SPI-based displays",
            board_type="esp32",
            code=code,
            libraries=["SPI"],
            wiring=[
                {"component": "Display SCK", "pin": "GPIO 18"},
                {"component": "Display MISO", "pin": "GPIO 19"},
                {"component": "Display MOSI", "pin": "GPIO 23"},
                {"component": "Display CS", "pin": "GPIO 5"}
            ]
        )
    
    def _pwm_motor_template(self) -> ProjectTemplate:
        """PWM motor control template"""
        code = """#include <Arduino.h>

#define MOTOR_PIN 13
#define PWM_FREQ 5000
#define PWM_CHANNEL 0
#define PWM_RESOLUTION 8

void setup() {
    Serial.begin(115200);
    
    // Configure PWM
    ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(MOTOR_PIN, PWM_CHANNEL);
    
    Serial.println("PWM Motor Control Ready!");
}

void loop() {
    // Ramp up
    for (int dutyCycle = 0; dutyCycle <= 255; dutyCycle++) {
        ledcWrite(PWM_CHANNEL, dutyCycle);
        delay(10);
    }
    
    // Ramp down
    for (int dutyCycle = 255; dutyCycle >= 0; dutyCycle--) {
        ledcWrite(PWM_CHANNEL, dutyCycle);
        delay(10);
    }
}
"""
        return ProjectTemplate(
            name="PWM Motor Control",
            description="Control motors with PWM",
            board_type="esp32",
            code=code,
            libraries=[],
            wiring=[
                {"component": "Motor Driver IN", "pin": "GPIO 13"},
                {"component": "Motor Driver VCC", "pin": "5V"},
                {"component": "Motor Driver GND", "pin": "GND"}
            ]
        )
    
    def _freertos_template(self) -> ProjectTemplate:
        """FreeRTOS starter template"""
        code = """#include <Arduino.h>

void task1(void *parameter) {
    while (true) {
        Serial.println("Task 1 running");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}

void task2(void *parameter) {
    while (true) {
        Serial.println("Task 2 running");
        vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
}

void setup() {
    Serial.begin(115200);
    
    // Create tasks
    xTaskCreate(task1, "Task1", 2048, NULL, 1, NULL);
    xTaskCreate(task2, "Task2", 2048, NULL, 1, NULL);
    
    Serial.println("FreeRTOS Tasks Created!");
}

void loop() {
    // Empty - tasks handle everything
}
"""
        return ProjectTemplate(
            name="FreeRTOS Starter",
            description="Multi-tasking with FreeRTOS",
            board_type="esp32",
            code=code,
            libraries=[],
            wiring=[]
        )
    
    def _stm32_usb_template(self) -> ProjectTemplate:
        """STM32 with USB template"""
        code = """#include "main.h"
#include "usb_device.h"
#include "usbd_cdc_if.h"

// Auto-generated clock config will be inserted here

void setup() {
    // Initialize USB
    MX_USB_DEVICE_Init();
    
    HAL_Delay(1000);
    
    // Send test message
    uint8_t msg[] = "STM32 USB Ready!\\r\\n";
    CDC_Transmit_FS(msg, sizeof(msg)-1);
}

void loop() {
    HAL_Delay(1000);
    
    uint8_t msg[] = "Heartbeat\\r\\n";
    CDC_Transmit_FS(msg, sizeof(msg)-1);
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    setup();
    
    while (1) {
        loop();
    }
}
"""
        return ProjectTemplate(
            name="STM32 USB CDC",
            description="STM32 with USB communication",
            board_type="stm32f4",
            code=code,
            libraries=["USB_DEVICE"],
            wiring=[]
        )
    
    def get_template(self, template_id: str) -> ProjectTemplate:
        """Get a specific template"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                'id': key,
                'name': template.name,
                'description': template.description,
                'board_type': template.board_type
            }
            for key, template in self.templates.items()
        ]


# Example usage
if __name__ == "__main__":
    templates = ProjectTemplates()
    
    print("Available Templates:")
    for template_info in templates.list_templates():
        print(f"  - {template_info['name']}: {template_info['description']}")
    
    print("\nBlink LED Template:")
    blink = templates.get_template('blink_led')
    print(blink.code)
