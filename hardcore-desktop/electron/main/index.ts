import { app, BrowserWindow, ipcMain, shell } from 'electron';
import path from 'path';
import { spawn } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let backendProcess: ReturnType<typeof spawn> | null = null;

const isDev = !app.isPackaged;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 700,
        frame: true,
        backgroundColor: '#0a0a0f',
        webPreferences: {
            preload: path.join(__dirname, '../preload/index.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    // Load the app
    if (isDev) {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../../dist-react/index.html'));
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startBackend() {
    const pythonPath = isDev
        ? 'python'
        : path.join(process.resourcesPath, 'python', 'python.exe');

    const backendDir = isDev
        ? path.join(__dirname, '../../../Hardcore.ai/orchestrator')
        : path.join(process.resourcesPath, 'backend');

    console.log('[Electron] Starting backend...');
    console.log('[Electron] Python:', pythonPath);
    console.log('[Electron] Backend Dir:', backendDir);

    try {
        // Run uvicorn to start FastAPI server
        backendProcess = spawn(pythonPath, [
            '-m', 'uvicorn',
            'main:app',
            '--host', '127.0.0.1',
            '--port', '8003'
        ], {
            cwd: backendDir,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env },
        });

        backendProcess.stdout?.on('data', (data) => {
            console.log(`[Backend] ${data}`);
        });

        backendProcess.stderr?.on('data', (data) => {
            console.error(`[Backend Error] ${data}`);
        });

        backendProcess.on('close', (code) => {
            console.log(`[Backend] Exited with code ${code}`);
        });

        backendProcess.on('error', (error) => {
            console.error('[Electron] Failed to start backend:', error);
        });
    } catch (error) {
        console.error('[Electron] Failed to start backend:', error);
    }
}

function stopBackend() {
    if (backendProcess) {
        console.log('[Electron] Stopping backend...');
        backendProcess.kill();
        backendProcess = null;
    }
}

// App lifecycle
app.whenReady().then(() => {
    startBackend();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopBackend();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    stopBackend();
});

// IPC Handlers
ipcMain.handle('shell:openExternal', async (_, url: string) => {
    await shell.openExternal(url);
});

ipcMain.handle('app:getInfo', () => {
    return {
        version: app.getVersion(),
        platform: process.platform,
        isDev,
    };
});
