// Global type declarations for Electron API

interface ElectronAPI {
    openFolder: () => Promise<{ canceled: boolean; filePaths: string[] }>;
    saveFile: (path: string, content: string) => Promise<{ success: boolean }>;
    readFile: (path: string) => Promise<{ content: string }>;
    listDirectory: (path: string) => Promise<{ files: string[] }>;
    onBackendLog: (callback: (message: string) => void) => void;
    onBackendError: (callback: (message: string) => void) => void;
}

declare global {
    interface Window {
        electronAPI?: ElectronAPI;
    }
}

export { };
