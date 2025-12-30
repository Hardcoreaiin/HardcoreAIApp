import React, { useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { useBoard } from '../../context/BoardContext';

const FlashButton: React.FC = () => {
    const { selectedBoard, connectedPort } = useBoard();
    const [isFlashing, setIsFlashing] = useState(false);

    const handleFlash = async () => {
        if (!connectedPort) {
            alert('No device connected. Please detect a device first.');
            return;
        }

        setIsFlashing(true);
        window.dispatchEvent(new CustomEvent('flash-start'));

        try {
            // Call backend to build and flash
            const response = await fetch('http://localhost:8003/flash', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    port: connectedPort,
                    board: selectedBoard || 'esp32dev',
                }),
            });

            const data = await response.json();

            if (data.success) {
                console.log('Flash successful!');
            } else {
                console.error('Flash failed:', data.error);
                alert('Flash failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Flash error:', error);
            alert('Flash failed. Make sure the backend is running.');
        } finally {
            setIsFlashing(false);
            window.dispatchEvent(new CustomEvent('flash-complete'));
        }
    };

    return (
        <button
            onClick={handleFlash}
            disabled={isFlashing}
            className="flex items-center gap-2 px-4 py-1.5 bg-accent-primary text-white rounded-lg text-sm font-medium hover:bg-accent-primary/80 disabled:opacity-50 transition-colors"
        >
            {isFlashing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
                <Zap className="w-4 h-4" />
            )}
            {isFlashing ? 'Flashing...' : 'Flash'}
        </button>
    );
};

export default FlashButton;
