import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Shell operations
    shell: {
        openExternal: (url: string) => ipcRenderer.invoke('shell:openExternal', url),
    },

    // App info
    app: {
        getInfo: () => ipcRenderer.invoke('app:getInfo'),
    },

    // AI communication (uses HTTP to backend)
    ai: {
        sendMessage: async (history: any[], board: string) => {
            const response = await fetch('http://localhost:8003/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: history[history.length - 1]?.content || '',
                    board_type: board,
                    history: history,
                }),
            });
            return response.json();
        },
    },

    // PlatformIO operations
    platformio: {
        build: async (projectPath: string, board: string) => {
            const response = await fetch('http://localhost:8003/build', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_path: projectPath, board }),
            });
            return response.json();
        },

        flash: async (projectPath: string, port: string, board: string) => {
            const response = await fetch('http://localhost:8003/flash', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_path: projectPath, port, board }),
            });
            return response.json();
        },

        onBuildOutput: (callback: (data: any) => void) => {
            // For now, we'll use polling or WebSocket in future
            return () => { }; // Cleanup function
        },
    },

    // Device detection
    devices: {
        detect: async () => {
            const response = await fetch('http://localhost:8003/detect');
            return response.json();
        },
    },

    // Driver installation
    drivers: {
        install: async () => {
            const response = await fetch('http://localhost:8003/install-drivers', {
                method: 'POST',
            });
            return response.json();
        },
    },
});

// Type definitions
declare global {
    interface Window {
        electronAPI: {
            shell: {
                openExternal: (url: string) => Promise<void>;
            };
            app: {
                getInfo: () => Promise<{ version: string; platform: string; isDev: boolean }>;
            };
            ai: {
                sendMessage: (history: any[], board: string) => Promise<any>;
            };
            platformio: {
                build: (projectPath: string, board: string) => Promise<any>;
                flash: (projectPath: string, port: string, board: string) => Promise<any>;
                onBuildOutput: (callback: (data: any) => void) => () => void;
            };
            devices: {
                detect: () => Promise<any>;
            };
            drivers: {
                install: () => Promise<any>;
            };
        };
    }
}
