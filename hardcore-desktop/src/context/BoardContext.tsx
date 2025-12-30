import React, { createContext, useContext, useState, ReactNode } from 'react';

interface BoardContextType {
    selectedBoard: string | null;
    setSelectedBoard: (board: string) => void;
    detectedBoard: string | null;
    setDetectedBoard: (board: string | null) => void;
    connectedPort: string | null;
    setConnectedPort: (port: string | null) => void;
}

const BoardContext = createContext<BoardContextType | undefined>(undefined);

export function BoardProvider({ children }: { children: ReactNode }) {
    const [selectedBoard, setSelectedBoard] = useState<string | null>('esp32dev');
    const [detectedBoard, setDetectedBoard] = useState<string | null>(null);
    const [connectedPort, setConnectedPort] = useState<string | null>(null);

    return (
        <BoardContext.Provider
            value={{
                selectedBoard,
                setSelectedBoard,
                detectedBoard,
                setDetectedBoard,
                connectedPort,
                setConnectedPort,
            }}
        >
            {children}
        </BoardContext.Provider>
    );
}

export function useBoard() {
    const context = useContext(BoardContext);
    if (context === undefined) {
        throw new Error('useBoard must be used within a BoardProvider');
    }
    return context;
}
