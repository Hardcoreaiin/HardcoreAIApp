import React, { useState } from 'react';
import { Plus, Trash2, Cable, ArrowRight } from 'lucide-react';

interface PinConnectionsTabProps {
    selectedBoard: string;
}

interface PinConnection {
    id: string;
    gpio: number;
    component: string;
    componentPin: string;
    wireColor: string;
    notes: string;
}

const wireColors = [
    { id: 'red', name: 'Red', color: '#ef4444' },
    { id: 'black', name: 'Black', color: '#1f2937' },
    { id: 'yellow', name: 'Yellow', color: '#eab308' },
    { id: 'green', name: 'Green', color: '#22c55e' },
    { id: 'blue', name: 'Blue', color: '#3b82f6' },
    { id: 'orange', name: 'Orange', color: '#f97316' },
    { id: 'white', name: 'White', color: '#f5f5f5' },
    { id: 'purple', name: 'Purple', color: '#a855f7' },
];

const commonComponents = [
    'LED',
    'Button',
    'Motor',
    'Servo',
    'Ultrasonic Sensor',
    'Temperature Sensor',
    'LCD Display',
    'OLED Display',
    'Relay',
    'Buzzer',
    'Potentiometer',
    'Photoresistor',
    'Custom',
];

const PinConnectionsTab: React.FC<PinConnectionsTabProps> = ({ selectedBoard }) => {
    const [connections, setConnections] = useState<PinConnection[]>([]);
    const [viewMode, setViewMode] = useState<'table' | 'json'>('table');

    const availablePins = [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35];

    const addConnection = () => {
        const usedPins = connections.map(c => c.gpio);
        const nextPin = availablePins.find(p => !usedPins.includes(p)) || 2;

        setConnections([...connections, {
            id: `conn_${Date.now()}`,
            gpio: nextPin,
            component: 'LED',
            componentPin: 'Anode',
            wireColor: 'red',
            notes: ''
        }]);
    };

    const removeConnection = (id: string) => {
        setConnections(connections.filter(c => c.id !== id));
    };

    const updateConnection = (id: string, field: keyof PinConnection, value: any) => {
        setConnections(connections.map(c =>
            c.id === id ? { ...c, [field]: value } : c
        ));
    };

    const getWireColor = (id: string) => wireColors.find(w => w.id === id)?.color || '#888';

    const exportJSON = () => {
        const data = connections.map(({ gpio, component, componentPin, wireColor, notes }) => ({
            gpio, component, componentPin, wireColor, notes
        }));
        return JSON.stringify(data, null, 2);
    };

    return (
        <div className="h-full flex flex-col bg-bg-dark">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-border">
                <div className="flex items-center gap-2">
                    <Cable className="w-4 h-4 text-accent-primary" />
                    <span className="text-sm font-medium text-text-primary">Pin Connections</span>
                    <span className="text-xs text-text-muted">({connections.length} wires)</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setViewMode(viewMode === 'table' ? 'json' : 'table')}
                        className="px-3 py-1 text-xs text-text-muted hover:text-text-primary bg-bg-elevated rounded transition-colors"
                    >
                        {viewMode === 'table' ? 'View JSON' : 'View Table'}
                    </button>
                    <button
                        onClick={addConnection}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-accent-primary hover:bg-accent-primary/10 rounded-md transition-colors"
                    >
                        <Plus className="w-4 h-4" /> Add Wire
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {viewMode === 'json' ? (
                    <pre className="text-sm font-mono text-text-primary bg-bg-surface p-4 rounded-lg overflow-auto">
                        {exportJSON()}
                    </pre>
                ) : connections.length === 0 ? (
                    <div className="text-center py-12 text-text-muted">
                        <Cable className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p className="text-sm">No connections configured</p>
                        <p className="text-xs mt-1">Click "Add Wire" to document your wiring</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {connections.map(conn => (
                            <div key={conn.id} className="flex items-center gap-3 p-3 bg-bg-surface rounded-lg border border-border">
                                {/* GPIO Pin */}
                                <select
                                    value={conn.gpio}
                                    onChange={e => updateConnection(conn.id, 'gpio', parseInt(e.target.value))}
                                    className="w-24 px-2 py-1.5 bg-bg-elevated border border-border rounded text-sm text-text-primary"
                                >
                                    {availablePins.map(p => <option key={p} value={p}>GPIO {p}</option>)}
                                </select>

                                {/* Wire indicator */}
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-12 h-1 rounded-full"
                                        style={{ backgroundColor: getWireColor(conn.wireColor) }}
                                    />
                                    <ArrowRight className="w-4 h-4 text-text-muted" />
                                </div>

                                {/* Component */}
                                <select
                                    value={conn.component}
                                    onChange={e => updateConnection(conn.id, 'component', e.target.value)}
                                    className="w-36 px-2 py-1.5 bg-bg-elevated border border-border rounded text-sm text-text-primary"
                                >
                                    {commonComponents.map(c => <option key={c} value={c}>{c}</option>)}
                                </select>

                                {/* Component Pin */}
                                <input
                                    type="text"
                                    value={conn.componentPin}
                                    onChange={e => updateConnection(conn.id, 'componentPin', e.target.value)}
                                    placeholder="Pin"
                                    className="w-24 px-2 py-1.5 bg-bg-elevated border border-border rounded text-sm text-text-primary"
                                />

                                {/* Wire Color */}
                                <select
                                    value={conn.wireColor}
                                    onChange={e => updateConnection(conn.id, 'wireColor', e.target.value)}
                                    className="w-24 px-2 py-1.5 bg-bg-elevated border border-border rounded text-sm text-text-primary"
                                    style={{ borderLeftColor: getWireColor(conn.wireColor), borderLeftWidth: 4 }}
                                >
                                    {wireColors.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                                </select>

                                {/* Notes */}
                                <input
                                    type="text"
                                    value={conn.notes}
                                    onChange={e => updateConnection(conn.id, 'notes', e.target.value)}
                                    placeholder="Notes..."
                                    className="flex-1 px-2 py-1.5 bg-bg-elevated border border-border rounded text-sm text-text-primary"
                                />

                                {/* Delete */}
                                <button
                                    onClick={() => removeConnection(conn.id)}
                                    className="p-1.5 text-text-muted hover:text-red-500 transition-colors"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default PinConnectionsTab;
