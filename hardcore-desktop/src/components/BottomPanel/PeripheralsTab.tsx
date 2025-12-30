import React, { useState, useEffect } from 'react';
import { Settings, Plus, Trash2 } from 'lucide-react';

interface PeripheralsTabProps { selectedBoard: string; }

// Export these types so other components can use them
export interface GPIOConfig { id: string; pin: number; label: string; mode: string; }
export interface I2CConfig { id: string; name: string; address: string; sda: number; scl: number; }
export interface SPIConfig { id: string; name: string; cs: number; mosi: number; miso: number; sck: number; }
export interface UARTConfig { id: string; name: string; tx: number; rx: number; baud: number; }
export interface TimerConfig { id: string; name: string; interval: number; unit: string; }
export interface ClockConfig { frequency: number; }

export interface PeripheralConfiguration {
    gpio: GPIOConfig[];
    i2c: I2CConfig[];
    spi: SPIConfig[];
    uart: UARTConfig[];
    timers: TimerConfig[];
    clock: ClockConfig;
}

const pins = [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35];
type Tab = 'gpio' | 'i2c' | 'spi' | 'uart' | 'timers' | 'clock';

// Store peripheral config globally so BottomPanel can access it
let globalPeripheralConfig: PeripheralConfiguration = {
    gpio: [], i2c: [], spi: [], uart: [], timers: [], clock: { frequency: 240 }
};

export function getPeripheralConfig(): PeripheralConfiguration {
    return globalPeripheralConfig;
}

const PeripheralsTab: React.FC<PeripheralsTabProps> = ({ selectedBoard }) => {
    const [tab, setTab] = useState<Tab>('gpio');
    const [gpio, setGpio] = useState<GPIOConfig[]>([]);
    const [i2c, setI2c] = useState<I2CConfig[]>([]);
    const [spi, setSpi] = useState<SPIConfig[]>([]);
    const [uart, setUart] = useState<UARTConfig[]>([]);
    const [timers, setTimers] = useState<TimerConfig[]>([]);
    const [clock, setClock] = useState(240);

    // Update global config and notify parent
    useEffect(() => {
        globalPeripheralConfig = { gpio, i2c, spi, uart, timers, clock: { frequency: clock } };
        window.dispatchEvent(new CustomEvent('peripheral-update', {
            detail: { gpio: gpio.length, i2c: i2c.length, spi: spi.length, uart: uart.length, timers: timers.length }
        }));
    }, [gpio, i2c, spi, uart, timers, clock]);

    const tabs: { id: Tab; label: string }[] = [
        { id: 'gpio', label: 'GPIO Pins' }, { id: 'i2c', label: 'I2C' }, { id: 'spi', label: 'SPI' },
        { id: 'uart', label: 'UART' }, { id: 'timers', label: 'Timers' }, { id: 'clock', label: 'Clock' },
    ];

    const input = "px-2 py-1 text-sm bg-neutral-800 border border-neutral-700 rounded text-neutral-200 focus:border-neutral-500 outline-none";
    const row = "flex items-center gap-3 p-3 bg-neutral-900 border border-neutral-800 rounded mb-2";

    return (
        <div className="h-full flex flex-col bg-neutral-950">
            <div className="flex items-center justify-between px-4 py-2 border-b border-neutral-800">
                <div className="flex items-center gap-2 text-neutral-400"><Settings className="w-4 h-4" /><span className="text-sm">Peripheral Configuration</span></div>
                <span className="text-xs text-neutral-500">Board: {selectedBoard}</span>
            </div>
            <div className="flex items-center gap-4 px-4 py-2 border-b border-neutral-800">
                {tabs.map(t => <button key={t.id} onClick={() => setTab(t.id)} className={`text-sm transition-colors ${tab === t.id ? 'text-neutral-100' : 'text-neutral-500 hover:text-neutral-300'}`}>{t.label}</button>)}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
                {tab === 'gpio' && <>
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-neutral-500">Configure GPIO pins</span>
                        <button onClick={() => setGpio([...gpio, { id: `g${Date.now()}`, pin: pins.find(p => !gpio.some(g => g.pin === p)) || 2, label: '', mode: 'OUTPUT' }])} className="flex items-center gap-1 text-sm text-neutral-300 hover:text-neutral-100"><Plus className="w-4 h-4" /> Add Pin</button>
                    </div>
                    {gpio.map(g => <div key={g.id} className={row}>
                        <select value={g.pin} onChange={e => setGpio(gpio.map(x => x.id === g.id ? { ...x, pin: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p} value={p}>GPIO {p}</option>)}</select>
                        <input value={g.label} onChange={e => setGpio(gpio.map(x => x.id === g.id ? { ...x, label: e.target.value } : x))} placeholder="Label (e.g., LED, BUTTON)" className={`${input} flex-1`} />
                        <select value={g.mode} onChange={e => setGpio(gpio.map(x => x.id === g.id ? { ...x, mode: e.target.value } : x))} className={input}><option>INPUT</option><option>OUTPUT</option><option>INPUT_PULLUP</option><option>INPUT_PULLDOWN</option><option>PWM</option><option>ANALOG</option></select>
                        <button onClick={() => setGpio(gpio.filter(x => x.id !== g.id))} className="text-neutral-500 hover:text-neutral-300"><Trash2 className="w-4 h-4" /></button>
                    </div>)}
                </>}
                {tab === 'i2c' && <>
                    <div className="flex items-center justify-between mb-3"><span className="text-sm text-neutral-500">Configure I2C devices</span><button onClick={() => setI2c([...i2c, { id: `i${Date.now()}`, name: '', address: '0x3C', sda: 21, scl: 22 }])} className="flex items-center gap-1 text-sm text-neutral-300 hover:text-neutral-100"><Plus className="w-4 h-4" /> Add Device</button></div>
                    {i2c.map(d => <div key={d.id} className="p-3 bg-neutral-900 border border-neutral-800 rounded mb-2">
                        <div className="flex items-center gap-3 mb-2"><input value={d.name} onChange={e => setI2c(i2c.map(x => x.id === d.id ? { ...x, name: e.target.value } : x))} placeholder="Device name (e.g., OLED, BME280)" className={`${input} flex-1`} /><input value={d.address} onChange={e => setI2c(i2c.map(x => x.id === d.id ? { ...x, address: e.target.value } : x))} placeholder="0x3C" className={`${input} w-20`} /><button onClick={() => setI2c(i2c.filter(x => x.id !== d.id))} className="text-neutral-500 hover:text-neutral-300"><Trash2 className="w-4 h-4" /></button></div>
                        <div className="flex items-center gap-3 text-xs text-neutral-500"><span>SDA:</span><select value={d.sda} onChange={e => setI2c(i2c.map(x => x.id === d.id ? { ...x, sda: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select><span>SCL:</span><select value={d.scl} onChange={e => setI2c(i2c.map(x => x.id === d.id ? { ...x, scl: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select></div>
                    </div>)}
                </>}
                {tab === 'spi' && <>
                    <div className="flex items-center justify-between mb-3"><span className="text-sm text-neutral-500">Configure SPI devices</span><button onClick={() => setSpi([...spi, { id: `s${Date.now()}`, name: '', cs: 5, mosi: 23, miso: 19, sck: 18 }])} className="flex items-center gap-1 text-sm text-neutral-300 hover:text-neutral-100"><Plus className="w-4 h-4" /> Add Device</button></div>
                    {spi.map(d => <div key={d.id} className="p-3 bg-neutral-900 border border-neutral-800 rounded mb-2">
                        <div className="flex items-center gap-3 mb-2"><input value={d.name} onChange={e => setSpi(spi.map(x => x.id === d.id ? { ...x, name: e.target.value } : x))} placeholder="Device name (e.g., SD Card, Display)" className={`${input} flex-1`} /><button onClick={() => setSpi(spi.filter(x => x.id !== d.id))} className="text-neutral-500 hover:text-neutral-300"><Trash2 className="w-4 h-4" /></button></div>
                        <div className="flex items-center gap-3 text-xs text-neutral-500 flex-wrap"><span>CS:</span><select value={d.cs} onChange={e => setSpi(spi.map(x => x.id === d.id ? { ...x, cs: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select><span>MOSI:</span><select value={d.mosi} onChange={e => setSpi(spi.map(x => x.id === d.id ? { ...x, mosi: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select><span>MISO:</span><select value={d.miso} onChange={e => setSpi(spi.map(x => x.id === d.id ? { ...x, miso: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select><span>SCK:</span><select value={d.sck} onChange={e => setSpi(spi.map(x => x.id === d.id ? { ...x, sck: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select></div>
                    </div>)}
                </>}
                {tab === 'uart' && <>
                    <div className="flex items-center justify-between mb-3"><span className="text-sm text-neutral-500">Configure UART ports</span><button onClick={() => setUart([...uart, { id: `u${Date.now()}`, name: '', tx: 17, rx: 16, baud: 115200 }])} className="flex items-center gap-1 text-sm text-neutral-300 hover:text-neutral-100"><Plus className="w-4 h-4" /> Add UART</button></div>
                    {uart.map(u => <div key={u.id} className="p-3 bg-neutral-900 border border-neutral-800 rounded mb-2">
                        <div className="flex items-center gap-3 mb-2"><input value={u.name} onChange={e => setUart(uart.map(x => x.id === u.id ? { ...x, name: e.target.value } : x))} placeholder="Name (e.g., GPS, Bluetooth)" className={`${input} flex-1`} /><select value={u.baud} onChange={e => setUart(uart.map(x => x.id === u.id ? { ...x, baud: +e.target.value } : x))} className={input}><option>9600</option><option>19200</option><option>38400</option><option>57600</option><option>115200</option><option>230400</option><option>460800</option><option>921600</option></select><button onClick={() => setUart(uart.filter(x => x.id !== u.id))} className="text-neutral-500 hover:text-neutral-300"><Trash2 className="w-4 h-4" /></button></div>
                        <div className="flex items-center gap-3 text-xs text-neutral-500"><span>TX:</span><select value={u.tx} onChange={e => setUart(uart.map(x => x.id === u.id ? { ...x, tx: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select><span>RX:</span><select value={u.rx} onChange={e => setUart(uart.map(x => x.id === u.id ? { ...x, rx: +e.target.value } : x))} className={input}>{pins.map(p => <option key={p}>{p}</option>)}</select></div>
                    </div>)}
                </>}
                {tab === 'timers' && <>
                    <div className="flex items-center justify-between mb-3"><span className="text-sm text-neutral-500">Configure timers</span><button onClick={() => setTimers([...timers, { id: `t${Date.now()}`, name: '', interval: 1000, unit: 'ms' }])} className="flex items-center gap-1 text-sm text-neutral-300 hover:text-neutral-100"><Plus className="w-4 h-4" /> Add Timer</button></div>
                    {timers.map(t => <div key={t.id} className={row}><input value={t.name} onChange={e => setTimers(timers.map(x => x.id === t.id ? { ...x, name: e.target.value } : x))} placeholder="Timer name" className={`${input} flex-1`} /><input type="number" value={t.interval} onChange={e => setTimers(timers.map(x => x.id === t.id ? { ...x, interval: +e.target.value } : x))} className={`${input} w-24`} /><select value={t.unit} onChange={e => setTimers(timers.map(x => x.id === t.id ? { ...x, unit: e.target.value } : x))} className={input}><option>us</option><option>ms</option><option>s</option></select><button onClick={() => setTimers(timers.filter(x => x.id !== t.id))} className="text-neutral-500 hover:text-neutral-300"><Trash2 className="w-4 h-4" /></button></div>)}
                </>}
                {tab === 'clock' && <div><span className="text-sm text-neutral-500">Configure CPU clock</span><div className="mt-3 p-3 bg-neutral-900 border border-neutral-800 rounded"><label className="text-xs text-neutral-500">CPU Frequency</label><select value={clock} onChange={e => setClock(+e.target.value)} className={`${input} w-full mt-2`}><option value={80}>80 MHz (Low Power)</option><option value={160}>160 MHz (Balanced)</option><option value={240}>240 MHz (Performance)</option></select></div></div>}
            </div>
        </div>
    );
};

export default PeripheralsTab;
