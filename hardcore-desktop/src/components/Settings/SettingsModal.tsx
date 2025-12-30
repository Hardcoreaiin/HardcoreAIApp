import React, { useState, useEffect } from 'react';
import { Settings, Key, Save, X, ExternalLink } from 'lucide-react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const API_HEADERS = {
    'Content-Type': 'application/json',
    'X-Desktop-Key': 'desktop_local_bypass_hardcore_ai',
};

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const [apiKey, setApiKey] = useState('');
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        if (isOpen) {
            // Load saved API key on open
            const savedKey = localStorage.getItem('gemini_api_key') || '';
            setApiKey(savedKey);
            setMessage(null);
        }
    }, [isOpen]);

    const handleSave = async () => {
        if (!apiKey.trim()) {
            setMessage({ type: 'error', text: 'Please enter an API key' });
            return;
        }

        setSaving(true);
        setMessage(null);

        try {
            // Save to localStorage
            localStorage.setItem('gemini_api_key', apiKey.trim());

            // Send to backend to update environment
            const res = await fetch('http://localhost:8003/settings/api-key', {
                method: 'POST',
                headers: API_HEADERS,
                body: JSON.stringify({ api_key: apiKey.trim() }),
            });

            if (res.ok) {
                setMessage({ type: 'success', text: 'API key saved successfully!' });
                setTimeout(() => onClose(), 1500);
            } else {
                // Even if backend fails, key is saved locally
                setMessage({ type: 'success', text: 'API key saved locally. Restart app to apply.' });
            }
        } catch {
            // Backend might not be running, save locally anyway
            setMessage({ type: 'success', text: 'API key saved. Restart app to apply.' });
        }

        setSaving(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-neutral-900 border border-neutral-700 rounded-lg w-full max-w-md mx-4 shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800">
                    <div className="flex items-center gap-2">
                        <Settings className="w-5 h-5 text-neutral-400" />
                        <span className="font-medium text-neutral-100">Settings</span>
                    </div>
                    <button onClick={onClose} className="p-1 text-neutral-500 hover:text-neutral-300">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-4">
                    <div>
                        <label className="flex items-center gap-2 text-sm text-neutral-400 mb-2">
                            <Key className="w-4 h-4" />
                            Gemini API Key
                        </label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Enter your Gemini API key..."
                            className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded text-neutral-200 placeholder-neutral-500 focus:border-neutral-500 outline-none"
                        />
                        <p className="mt-2 text-xs text-neutral-500">
                            Your API key is stored locally and never shared.
                        </p>
                    </div>

                    <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
                    >
                        <ExternalLink className="w-4 h-4" />
                        Get a free Gemini API key
                    </a>

                    {message && (
                        <div className={`px-3 py-2 rounded text-sm ${message.type === 'success' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                            {message.text}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-2 px-4 py-3 border-t border-neutral-800">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-neutral-400 hover:text-neutral-200"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-4 py-2 text-sm bg-neutral-100 text-neutral-900 rounded hover:bg-neutral-200 disabled:opacity-50"
                    >
                        <Save className="w-4 h-4" />
                        {saving ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
