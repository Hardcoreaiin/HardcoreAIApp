import React, { useState } from 'react';
import { FolderPlus, FolderOpen } from 'lucide-react';
import SerialMonitor from './SerialMonitor';
import BuildOutput from './BuildOutput';
import PinConnectionsTab from './PinConnectionsTab';
import PeripheralsTab, { getPeripheralConfig, PeripheralConfiguration, GPIOConfig, I2CConfig, SPIConfig, UARTConfig, TimerConfig } from './PeripheralsTab';

// Desktop bypass header for local authentication
const API_HEADERS = {
    'Content-Type': 'application/json',
    'X-Desktop-Key': 'desktop_local_bypass_hardcore_ai',
};

interface BottomPanelProps {
    selectedBoard: string;
    detectedBoard?: string | null;
    connectedPort?: string | null;
    onNewProject?: () => void;
    onOpenProject?: () => void;
    onGenerateCode?: () => void;
    gpio?: number;
    i2c?: number;
    spi?: number;
    uart?: number;
    timers?: number;
}

type Tab = 'pins' | 'serial' | 'build' | 'peripherals';

// Generate a detailed prompt from peripheral configuration
function generatePromptFromConfig(config: PeripheralConfiguration, board: string): string {
    const lines: string[] = [`Generate PlatformIO firmware code for ${board} with the following peripheral configuration:`];

    if (config.gpio.length > 0) {
        lines.push('\nGPIO Pins:');
        config.gpio.forEach((g: GPIOConfig) => {
            lines.push(`  - GPIO ${g.pin}: ${g.mode}${g.label ? ` (${g.label})` : ''}`);
        });
    }

    if (config.i2c.length > 0) {
        lines.push('\nI2C Devices:');
        config.i2c.forEach((d: I2CConfig) => {
            lines.push(`  - ${d.name || 'Device'} at address ${d.address}, SDA=GPIO${d.sda}, SCL=GPIO${d.scl}`);
        });
    }

    if (config.spi.length > 0) {
        lines.push('\nSPI Devices:');
        config.spi.forEach((d: SPIConfig) => {
            lines.push(`  - ${d.name || 'Device'}: CS=GPIO${d.cs}, MOSI=GPIO${d.mosi}, MISO=GPIO${d.miso}, SCK=GPIO${d.sck}`);
        });
    }

    if (config.uart.length > 0) {
        lines.push('\nUART Ports:');
        config.uart.forEach((u: UARTConfig) => {
            lines.push(`  - ${u.name || 'UART'}: TX=GPIO${u.tx}, RX=GPIO${u.rx}, Baud=${u.baud}`);
        });
    }

    if (config.timers.length > 0) {
        lines.push('\nTimers:');
        config.timers.forEach((t: TimerConfig) => {
            lines.push(`  - ${t.name || 'Timer'}: ${t.interval}${t.unit} interval`);
        });
    }

    lines.push(`\nCPU Clock: ${config.clock.frequency} MHz`);
    lines.push('\nGenerate complete, working code with proper pin definitions, initialization in setup(), and a main loop.');

    return lines.join('\n');
}

const BottomPanel: React.FC<BottomPanelProps> = ({ selectedBoard, detectedBoard, connectedPort, onNewProject, onOpenProject, onGenerateCode, gpio = 0, i2c = 0, spi = 0, uart = 0, timers = 0 }) => {
    const [tab, setTab] = useState<Tab>('peripherals');
    const [generating, setGenerating] = useState(false);

    const tabs: { id: Tab; label: string }[] = [
        { id: 'pins', label: 'Pin Connections' },
        { id: 'serial', label: 'Serial Monitor' },
        { id: 'build', label: 'Build Output' },
        { id: 'peripherals', label: 'Peripherals' },
    ];

    const handleGenerateCode = async () => {
        const config = getPeripheralConfig();
        const total = config.gpio.length + config.i2c.length + config.spi.length + config.uart.length + config.timers.length;

        if (total === 0) {
            alert('Add at least one peripheral (GPIO, I2C, SPI, UART, or Timer) before generating code.');
            return;
        }

        setGenerating(true);
        const prompt = generatePromptFromConfig(config, selectedBoard);
        console.log('Generating code with prompt:', prompt);
        console.log('Peripheral config:', config);
        console.log('Detected board:', detectedBoard, 'Connected port:', connectedPort);

        try {
            const res = await fetch('http://localhost:8003/execute', {
                method: 'POST',
                headers: API_HEADERS,
                body: JSON.stringify({
                    prompt,
                    board_type: selectedBoard,
                    peripheral_config: config,
                    detected_board: detectedBoard || null,
                    detected_port: connectedPort || null,
                }),
            });
            const data = await res.json();

            if (data.status === 'success' && data.firmware) {
                window.dispatchEvent(new CustomEvent('code-generated', { detail: { code: data.firmware, fileName: 'main.cpp' } }));
                alert(`Code generated for ${data.board_used || selectedBoard}! Check the editor.`);
            } else if (data.message) {
                // Show AI message in case it needs clarification
                window.dispatchEvent(new CustomEvent('code-generated', { detail: { code: `// ${data.message}`, fileName: 'main.cpp' } }));
                alert(data.message);
            } else {
                alert('Failed to generate code. Check backend logs.');
            }
        } catch (e) {
            alert('Backend not running. Start the backend server.');
        }
        setGenerating(false);
        onGenerateCode?.();
    };

    const handleNewProject = () => onNewProject?.();
    const handleOpen = async () => {
        if (window.electronAPI?.openFolder) {
            const result = await window.electronAPI.openFolder();
            if (!result.canceled && result.filePaths?.length) alert(`Opened: ${result.filePaths[0]}`);
        }
        onOpenProject?.();
    };

    return (
        <div className="h-full flex flex-col bg-neutral-950">
            <div className="flex border-b border-neutral-800 bg-neutral-900">
                {tabs.map(t => (
                    <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 text-sm border-b-2 transition-colors ${tab === t.id ? 'border-neutral-100 text-neutral-100' : 'border-transparent text-neutral-500 hover:text-neutral-300'}`}>{t.label}</button>
                ))}
            </div>
            <div className="flex-1 overflow-hidden">
                {tab === 'pins' && <PinConnectionsTab selectedBoard={selectedBoard} />}
                {tab === 'serial' && <SerialMonitor />}
                {tab === 'build' && <BuildOutput />}
                {tab === 'peripherals' && <PeripheralsTab selectedBoard={selectedBoard} />}
            </div>
            <div className="h-10 flex items-center justify-between px-4 border-t border-neutral-800 bg-neutral-900">
                <div className="flex items-center gap-2">
                    <button onClick={handleNewProject} className="flex items-center gap-2 px-3 py-1.5 text-sm border border-neutral-700 bg-neutral-800 text-neutral-300 rounded hover:bg-neutral-700 transition-colors">
                        <FolderPlus className="w-4 h-4" /> New Project
                    </button>
                    <button onClick={handleOpen} className="flex items-center gap-2 px-3 py-1.5 text-sm border border-neutral-700 bg-neutral-800 text-neutral-300 rounded hover:bg-neutral-700 transition-colors">
                        <FolderOpen className="w-4 h-4" /> Open
                    </button>
                </div>
                <div className="text-xs text-neutral-500">{gpio} GPIO • {i2c} I2C • {spi} SPI • {uart} UART • {timers} Timers</div>
                <button onClick={handleGenerateCode} disabled={generating} className="px-4 py-1.5 text-sm font-medium bg-neutral-100 text-neutral-900 rounded hover:bg-neutral-200 transition-colors disabled:opacity-50">
                    {generating ? 'Generating...' : 'Generate Code'}
                </button>
            </div>
        </div>
    );
};

export default BottomPanel;
