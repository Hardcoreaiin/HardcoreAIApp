import React, { useState } from 'react';
import { Usb, Loader2, ChevronDown } from 'lucide-react';

interface DetectButtonProps {
    onPortChange?: (port: string | null) => void;
}

interface DetectedDevice {
    port: string;
    board: string;
    chipType?: string;
}

const DetectButton: React.FC<DetectButtonProps> = ({ onPortChange }) => {
    const [isDetecting, setIsDetecting] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [detectedDevices, setDetectedDevices] = useState<DetectedDevice[]>([]);

    const handleDetect = async () => {
        setIsDetecting(true);
        setShowDropdown(false);

        try {
            // Call backend to detect devices
            const response = await fetch('http://localhost:8003/detect', {
                method: 'GET',
            });

            if (response.ok) {
                const data = await response.json();
                if (data.devices && data.devices.length > 0) {
                    setDetectedDevices(data.devices);
                    setShowDropdown(true);
                } else {
                    // No devices found
                    setDetectedDevices([]);
                    alert('No devices detected. Please connect a board via USB.');
                }
            }
        } catch (error) {
            console.error('Detection failed:', error);
            alert('Detection failed. Make sure the backend is running.');
        } finally {
            setIsDetecting(false);
        }
    };

    const selectDevice = (device: DetectedDevice) => {
        if (onPortChange) {
            onPortChange(device.port);
        }
        setShowDropdown(false);
    };

    return (
        <div className="relative">
            <button
                onClick={handleDetect}
                disabled={isDetecting}
                className="flex items-center gap-2 px-4 py-1.5 bg-bg-elevated border border-border rounded-lg text-sm font-medium text-text-primary hover:bg-bg-hover disabled:opacity-50 transition-colors"
            >
                {isDetecting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <Usb className="w-4 h-4" />
                )}
                Detect
                <ChevronDown className="w-4 h-4 text-text-muted" />
            </button>

            {/* Dropdown */}
            {showDropdown && detectedDevices.length > 0 && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowDropdown(false)}
                    />
                    <div className="absolute top-full left-0 mt-2 w-64 bg-bg-surface border border-border rounded-xl shadow-xl z-50 py-2">
                        {detectedDevices.map((device) => (
                            <button
                                key={device.port}
                                onClick={() => selectDevice(device)}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-bg-hover transition-colors"
                            >
                                <Usb className="w-4 h-4 text-green-500" />
                                <div className="text-left">
                                    <div className="text-sm font-medium text-text-primary">
                                        {device.board}
                                    </div>
                                    <div className="text-xs text-text-muted">{device.port}</div>
                                </div>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

export default DetectButton;
