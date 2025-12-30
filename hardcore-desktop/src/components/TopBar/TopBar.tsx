import React, { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useBoard } from '../../context/BoardContext';
import { useAuth } from '../../context/AuthContext';
import { Cpu, Wifi, Zap, ChevronDown, LogOut, Loader2, Settings } from 'lucide-react';
import SettingsModal from '../Settings/SettingsModal';
// Desktop bypass header for local authentication
const API_HEADERS = {
    'Content-Type': 'application/json',
    'X-Desktop-Key': 'desktop_local_bypass_hardcore_ai',
};

interface TopBarProps {
    onPortChange?: (port: string | null) => void;
    onBoardChange?: (board: string) => void;
}

const boards = [
    { id: 'esp32dev', name: 'ESP32 DevKit' },
    { id: 'esp32-s3', name: 'ESP32-S3' },
    { id: 'uno', name: 'Arduino Uno' },
    { id: 'nano', name: 'Arduino Nano' },
    { id: 'mega', name: 'Arduino Mega' },
];

const TopBar: React.FC<TopBarProps> = ({ onPortChange, onBoardChange }) => {
    const { selectedBoard, setSelectedBoard, connectedPort, setConnectedPort } = useBoard();
    const { user, logout } = useAuth();
    const [showProfile, setShowProfile] = useState(false);
    const [showBoards, setShowBoards] = useState(false);
    const [showWireless, setShowWireless] = useState(false);
    const [detecting, setDetecting] = useState(false);
    const [flashing, setFlashing] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const profileRef = useRef<HTMLButtonElement>(null);
    const boardRef = useRef<HTMLButtonElement>(null);
    const wirelessRef = useRef<HTMLButtonElement>(null);

    const detect = async () => {
        setDetecting(true);
        setShowBoards(false);
        try {
            const res = await fetch('http://localhost:8003/detect', { headers: API_HEADERS });
            const data = await res.json();
            if (data.devices?.length) {
                const device = data.devices[0];
                onPortChange?.(device.port);
                setConnectedPort(device.port);
                if (device.board) {
                    setSelectedBoard(device.board);
                    onBoardChange?.(device.board);
                }
                alert(`Detected: ${device.board || 'Unknown'} on ${device.port}`);
            } else {
                alert('No devices detected. Connect a board and try again.');
            }
        } catch (e) {
            alert('Backend not running. Start the backend server first.');
        }
        setDetecting(false);
    };

    const flash = async () => {
        if (!connectedPort && !selectedBoard) {
            alert('No board detected. Click "Detect Board" first.');
            return;
        }
        setFlashing(true);
        window.dispatchEvent(new CustomEvent('flash-start'));
        try {
            const res = await fetch('http://localhost:8003/flash', {
                method: 'POST',
                headers: API_HEADERS,
                body: JSON.stringify({ port: connectedPort, board: selectedBoard }),
            });
            const data = await res.json();
            window.dispatchEvent(new CustomEvent('flash-complete', { detail: data }));
            alert(data.success ? 'Flash successful!' : `Flash failed: ${data.error || 'Unknown error'}`);
        } catch (e) {
            window.dispatchEvent(new CustomEvent('flash-complete', { detail: { success: false, error: String(e) } }));
            alert('Flash failed: Backend not running');
        }
        setFlashing(false);
    };

    const selectBoard = (id: string) => {
        setSelectedBoard(id);
        onBoardChange?.(id);
        setShowBoards(false);
    };

    const btn = "flex items-center gap-2 px-3 py-1.5 text-sm border border-neutral-700 bg-neutral-900 text-neutral-300 rounded hover:bg-neutral-800 transition-colors";

    return (
        <div className="h-11 flex items-center justify-between px-4 border-b border-neutral-800 bg-neutral-950">
            <div className="font-medium text-neutral-100">HardcoreAI</div>

            <div className="flex items-center gap-2">
                <button ref={boardRef} onClick={() => setShowBoards(!showBoards)} className={btn}>
                    <Cpu className="w-4 h-4" /> Detect Board <ChevronDown className="w-3 h-3 opacity-50" />
                </button>
                {showBoards && createPortal(
                    <>
                        <div className="fixed inset-0 z-50" onClick={() => setShowBoards(false)} />
                        <div className="fixed z-50 w-48 border border-neutral-700 bg-neutral-900 rounded shadow-xl py-1" style={{ top: (boardRef.current?.getBoundingClientRect().bottom || 0) + 4, left: boardRef.current?.getBoundingClientRect().left || 0 }}>
                            <button onClick={detect} disabled={detecting} className="w-full text-left px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-800 border-b border-neutral-700">
                                {detecting ? 'Detecting...' : 'Auto Detect'}
                            </button>
                            <div className="py-1 text-xs text-neutral-500 px-3">Or select manually:</div>
                            {boards.map(b => (
                                <button key={b.id} onClick={() => selectBoard(b.id)} className={`w-full text-left px-3 py-2 text-sm hover:bg-neutral-800 ${selectedBoard === b.id ? 'text-neutral-100' : 'text-neutral-400'}`}>{b.name}</button>
                            ))}
                        </div>
                    </>,
                    document.body
                )}

                <button ref={wirelessRef} onClick={() => setShowWireless(!showWireless)} className={btn}>
                    <Wifi className="w-4 h-4" /> Wireless <ChevronDown className="w-3 h-3 opacity-50" />
                </button>
                {showWireless && createPortal(
                    <>
                        <div className="fixed inset-0 z-50" onClick={() => setShowWireless(false)} />
                        <div className="fixed z-50 w-48 border border-neutral-700 bg-neutral-900 rounded shadow-xl py-1" style={{ top: (wirelessRef.current?.getBoundingClientRect().bottom || 0) + 4, left: wirelessRef.current?.getBoundingClientRect().left || 0 }}>
                            <button className="w-full text-left px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-800">OTA Update</button>
                            <button className="w-full text-left px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-800">WiFi Config</button>
                            <button className="w-full text-left px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-800">Bluetooth</button>
                        </div>
                    </>,
                    document.body
                )}
            </div>

            <div className="flex items-center gap-2">
                <button onClick={flash} disabled={flashing} className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-neutral-100 text-neutral-900 rounded hover:bg-neutral-200 transition-colors disabled:opacity-50">
                    {flashing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Flash
                </button>
                <button ref={profileRef} onClick={() => setShowProfile(!showProfile)} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-neutral-800 text-neutral-200 rounded-full hover:bg-neutral-700 transition-colors">
                    <div className="w-5 h-5 rounded-full bg-neutral-600 flex items-center justify-center text-xs font-medium">{user?.name?.charAt(0) || 'D'}</div>
                    {user?.name || 'Demo User'} <ChevronDown className="w-3 h-3 opacity-50" />
                </button>
                {showProfile && createPortal(
                    <>
                        <div className="fixed inset-0 z-50" onClick={() => setShowProfile(false)} />
                        <div className="fixed z-50 w-44 border border-neutral-700 bg-neutral-900 rounded shadow-xl py-1" style={{ top: (profileRef.current?.getBoundingClientRect().bottom || 0) + 4, right: window.innerWidth - (profileRef.current?.getBoundingClientRect().right || 0) }}>
                            <div className="px-3 py-2 border-b border-neutral-800">
                                <div className="text-sm text-neutral-100">{user?.name}</div>
                                <div className="text-xs text-neutral-500">{user?.email}</div>
                            </div>
                            <button onClick={() => { setShowSettings(true); setShowProfile(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-neutral-400 hover:bg-neutral-800"><Settings className="w-4 h-4" /> Settings</button>
                            <button onClick={() => { logout(); setShowProfile(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-neutral-400 hover:bg-neutral-800"><LogOut className="w-4 h-4" /> Sign Out</button>
                        </div>
                    </>,
                    document.body
                )}
            </div>
            <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
        </div>
    );
};

export default TopBar;
