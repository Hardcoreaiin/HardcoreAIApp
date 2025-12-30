import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useBoard } from '../../context/BoardContext';

// Desktop bypass header for local authentication
const API_HEADERS = {
    'Content-Type': 'application/json',
    'X-Desktop-Key': 'desktop_local_bypass_hardcore_ai',
};

interface Message { id: string; role: 'user' | 'assistant'; content: string; }

const AIAssistant: React.FC = () => {
    const { selectedBoard, detectedBoard } = useBoard();
    const [messages, setMessages] = useState<Message[]>([{ id: '1', role: 'assistant', content: 'Hello! I\'m HardcoreAI, your embedded systems copilot. What would you like to build today?' }]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    const send = async () => {
        if (!input.trim() || loading) return;
        const userMsg = input.trim();
        setMessages(prev => [...prev, { id: `u${Date.now()}`, role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);

        try {
            // Use /chat endpoint with intent gate (NOT /execute)
            const res = await fetch('http://localhost:8003/chat', {
                method: 'POST',
                headers: API_HEADERS,
                body: JSON.stringify({
                    message: userMsg,
                    board_type: selectedBoard || 'esp32dev',
                    detected_board: detectedBoard || null,
                }),
            });
            const data = await res.json();

            // Handle response based on type
            if (data.response_type === 'code' && data.firmware) {
                // ONLY dispatch code-generated when response_type is 'code'
                window.dispatchEvent(new CustomEvent('code-generated', {
                    detail: { code: data.firmware, fileName: 'main.cpp' }
                }));
                setMessages(prev => [...prev, {
                    id: `a${Date.now()}`,
                    role: 'assistant',
                    content: '✅ ' + (data.message || 'Firmware generated! Check the editor.')
                }]);
            } else {
                // Text or clarification - just show message (NO code generation)
                setMessages(prev => [...prev, {
                    id: `a${Date.now()}`,
                    role: 'assistant',
                    content: data.message || 'I\'m here to help. What would you like to build?'
                }]);
            }
        } catch (e) {
            setMessages(prev => [...prev, {
                id: `a${Date.now()}`,
                role: 'assistant',
                content: 'Failed to connect to backend. Make sure the server is running.'
            }]);
        }

        setLoading(false);
        inputRef.current?.focus();
    };

    return (
        <div className="h-full flex flex-col bg-neutral-950">
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {messages.map(m => (
                    <div key={m.id}>
                        <div className="text-xs text-neutral-500 mb-1">{m.role === 'user' ? 'You' : 'Assistant'}</div>
                        <div className={`text-sm rounded px-3 py-2 whitespace-pre-wrap ${m.role === 'user' ? 'bg-neutral-800 text-neutral-200 ml-8' : 'bg-neutral-900 border border-neutral-800 text-neutral-300'}`}>{m.content}</div>
                    </div>
                ))}
                {loading && <div><div className="text-xs text-neutral-500 mb-1">Assistant</div><div className="bg-neutral-900 border border-neutral-800 rounded px-3 py-2 inline-block"><Loader2 className="w-4 h-4 animate-spin text-neutral-400" /></div></div>}
                <div ref={endRef} />
            </div>
            <div className="p-3 border-t border-neutral-800">
                <div className="flex items-center gap-2 bg-neutral-900 border border-neutral-800 rounded px-3 py-2">
                    <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder="Describe what you want to build..." className="flex-1 bg-transparent text-sm text-neutral-200 placeholder-neutral-600 outline-none" disabled={loading} />
                    <button onClick={send} disabled={loading || !input.trim()} className="p-1 text-neutral-500 hover:text-neutral-300 disabled:opacity-30"><Send className="w-4 h-4" /></button>
                </div>
            </div>
        </div>
    );
};

export default AIAssistant;
