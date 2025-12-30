import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Trash2 } from 'lucide-react';

interface BuildOutputProps {
    selectedBoard?: string;
}

interface BuildMessage {
    id: number;
    type: 'error' | 'warning' | 'info' | 'success';
    message: string;
    timestamp: Date;
}

const BuildOutput: React.FC<BuildOutputProps> = () => {
    const [messages, setMessages] = useState<BuildMessage[]>([]);
    const [isBuilding, setIsBuilding] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        const handleFlashStart = () => {
            setMessages([
                { id: 1, type: 'info', message: 'Starting build...', timestamp: new Date() }
            ]);
            setIsBuilding(true);
        };

        const handleFlashComplete = (event: CustomEvent) => {
            const { success, error } = event.detail || {};
            if (success) {
                setMessages(prev => [...prev,
                { id: Date.now(), type: 'success', message: 'Build completed successfully!', timestamp: new Date() },
                { id: Date.now() + 1, type: 'success', message: 'Uploading to device...', timestamp: new Date() },
                { id: Date.now() + 2, type: 'success', message: 'Upload complete!', timestamp: new Date() }
                ]);
            } else {
                setMessages(prev => [...prev,
                { id: Date.now(), type: 'error', message: error || 'Build failed', timestamp: new Date() }
                ]);
            }
            setIsBuilding(false);
        };

        window.addEventListener('flash-start', handleFlashStart);
        window.addEventListener('flash-complete', handleFlashComplete as EventListener);

        return () => {
            window.removeEventListener('flash-start', handleFlashStart);
            window.removeEventListener('flash-complete', handleFlashComplete as EventListener);
        };
    }, []);

    const handleClear = () => setMessages([]);

    const getIcon = (type: string) => {
        switch (type) {
            case 'error': return <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />;
            case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500 flex-shrink-0" />;
            case 'success': return <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />;
            default: return null;
        }
    };

    const errorCount = messages.filter(m => m.type === 'error').length;
    const warningCount = messages.filter(m => m.type === 'warning').length;

    return (
        <div className="h-full flex flex-col bg-bg-dark">
            {/* Toolbar */}
            <div className="flex items-center gap-4 px-4 py-2 border-b border-border bg-bg-surface">
                <div className="flex items-center gap-2 text-xs">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <span className="text-text-muted">{errorCount} errors</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    <span className="text-text-muted">{warningCount} warnings</span>
                </div>
                {isBuilding && (
                    <span className="text-xs text-accent-primary animate-pulse">Building...</span>
                )}
                <div className="flex-1" />
                <button
                    onClick={handleClear}
                    className="p-1.5 text-text-muted hover:text-text-primary hover:bg-bg-hover rounded transition-colors"
                    title="Clear"
                >
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
                {messages.length === 0 ? (
                    <div className="text-center text-text-muted py-12">
                        No build output yet. Click Flash to build and upload.
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className="flex items-start gap-2 mb-2">
                            {getIcon(msg.type)}
                            <span className="text-text-muted text-xs">
                                [{msg.timestamp.toLocaleTimeString()}]
                            </span>
                            <span className={`flex-1 ${msg.type === 'error' ? 'text-red-400' :
                                    msg.type === 'warning' ? 'text-yellow-400' :
                                        msg.type === 'success' ? 'text-green-400' :
                                            'text-text-primary'
                                }`}>
                                {msg.message}
                            </span>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};

export default BuildOutput;
