import React, { useState, useEffect, useRef } from 'react';

interface SerialMonitorProps {
    selectedBoard?: string;
}

interface SerialMessage {
    id: number;
    text: string;
    type: 'rx' | 'tx' | 'info';
}

const SerialMonitor: React.FC<SerialMonitorProps> = () => {
    const [messages, setMessages] = useState<SerialMessage[]>([]);
    const [input, setInput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages((prev) => [
            ...prev,
            { id: Date.now(), text: input, type: 'tx' },
        ]);
        setInput('');
    };

    const handleClear = () => {
        setMessages([]);
    };

    return (
        <div className="h-full flex flex-col bg-bg-dark">
            {/* Toolbar */}
            <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-bg-surface">
                <div className="flex items-center gap-2">
                    <div
                        className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'
                            }`}
                    />
                    <span className="text-xs text-text-muted">
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>

                <div className="flex-1" />

                <button
                    onClick={handleClear}
                    className="px-3 py-1 text-xs font-medium bg-bg-hover text-text-primary rounded hover:bg-bg-elevated transition-colors"
                >
                    Clear
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
                {messages.length === 0 ? (
                    <div className="text-center text-text-muted py-12">
                        No serial output. Connect to a device to see data.
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`mb-1 ${msg.type === 'tx' ? 'text-blue-400' : 'text-text-primary'
                                }`}
                        >
                            {msg.type === 'tx' && <span className="text-text-muted">{'> '}</span>}
                            {msg.text}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex items-center gap-2 px-4 py-2 border-t border-border">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type command..."
                    className="flex-1 bg-bg-elevated border border-border rounded px-3 py-1.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary"
                />
                <button
                    onClick={handleSend}
                    className="px-4 py-1.5 bg-accent-primary text-white text-sm font-medium rounded hover:bg-accent-primary/80 transition-colors"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default SerialMonitor;
