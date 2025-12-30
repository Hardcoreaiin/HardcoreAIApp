import React, { useState, useEffect, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useBoard } from './context/BoardContext';
import { useAuth } from './context/AuthContext';
import TopBar from './components/TopBar/TopBar';
import ProjectExplorer from './components/Explorer/ProjectExplorer';
import AIAssistant from './components/AIAssistant/AIAssistant';
import BottomPanel from './components/BottomPanel/BottomPanel';
import LoginScreen from './components/Auth/LoginScreen';
import NewProjectWizard from './components/Wizard/NewProjectWizard';
import MonacoEditor from './components/Editor/MonacoEditor';

interface OpenFile {
    path: string;
    name: string;
    content: string;
    isDirty: boolean;
}

function App() {
    const { selectedBoard, setSelectedBoard, detectedBoard, connectedPort, setConnectedPort } = useBoard();
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
    const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
    const [showNewProjectWizard, setShowNewProjectWizard] = useState(false);
    const [peripheralCounts, setPeripheralCounts] = useState({ gpio: 0, i2c: 0, spi: 0, uart: 0, timers: 0 });

    const activeFile = openFiles.find(f => f.path === activeFilePath);

    useEffect(() => {
        const handler = (e: CustomEvent) => setPeripheralCounts(e.detail);
        window.addEventListener('peripheral-update', handler as EventListener);
        return () => window.removeEventListener('peripheral-update', handler as EventListener);
    }, []);

    useEffect(() => {
        const handler = (e: CustomEvent) => {
            const { code, fileName } = e.detail;
            if (!code) return;
            const filePath = `/src/${fileName || 'main.cpp'}`;
            setOpenFiles(prev => {
                const existing = prev.find(f => f.path === filePath);
                if (existing) return prev.map(f => f.path === filePath ? { ...f, content: code, isDirty: true } : f);
                return [...prev, { path: filePath, name: fileName || 'main.cpp', content: code, isDirty: true }];
            });
            setActiveFilePath(filePath);
        };
        window.addEventListener('code-generated', handler as EventListener);
        return () => window.removeEventListener('code-generated', handler as EventListener);
    }, []);

    const handleFileClick = useCallback((path: string, content: string) => {
        const name = path.split('/').pop() || 'unknown';
        setOpenFiles(prev => prev.find(f => f.path === path) ? prev : [...prev, { path, name, content, isDirty: false }]);
        setActiveFilePath(path);
    }, []);

    const handleEditorChange = useCallback((value: string | undefined) => {
        if (!value || !activeFilePath) return;
        setOpenFiles(prev => prev.map(f => f.path === activeFilePath ? { ...f, content: value, isDirty: true } : f));
    }, [activeFilePath]);

    const handleTabClick = useCallback((path: string) => setActiveFilePath(path), []);
    const handleTabClose = useCallback((path: string) => {
        setOpenFiles(prev => {
            const filtered = prev.filter(f => f.path !== path);
            if (path === activeFilePath) setActiveFilePath(filtered.length ? filtered[filtered.length - 1].path : null);
            return filtered;
        });
    }, [activeFilePath]);

    if (authLoading) return <div className="h-screen w-screen flex items-center justify-center bg-neutral-950 text-neutral-500">Loading...</div>;
    if (!isAuthenticated) return <LoginScreen />;

    return (
        <div className="h-screen w-screen flex flex-col overflow-hidden bg-neutral-950 text-neutral-100">
            <NewProjectWizard isOpen={showNewProjectWizard} onClose={() => setShowNewProjectWizard(false)} onCreateProject={(_, board) => { setSelectedBoard(board); setShowNewProjectWizard(false); }} />
            <TopBar onPortChange={setConnectedPort} onBoardChange={setSelectedBoard} />

            <PanelGroup direction="horizontal" className="flex-1">
                <Panel defaultSize={15} minSize={10} maxSize={25}>
                    <ProjectExplorer onFileClick={handleFileClick} currentProject={{ id: '1', name: 'current_project', path: '/current_project' }} />
                </Panel>
                <PanelResizeHandle className="w-px bg-neutral-800 hover:bg-neutral-600 transition-colors" />
                <Panel defaultSize={55}>
                    <PanelGroup direction="vertical">
                        <Panel defaultSize={65} minSize={30}>
                            {activeFile ? (
                                <MonacoEditor value={activeFile.content} onChange={handleEditorChange} language="cpp" openFiles={openFiles} activeFilePath={activeFilePath || ''} onTabClick={handleTabClick} onTabClose={handleTabClose} />
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center bg-neutral-900 text-neutral-500">
                                    <div className="text-base mb-1">No file open</div>
                                    <div className="text-sm">Open a file from the explorer or create a new project</div>
                                </div>
                            )}
                        </Panel>
                        <PanelResizeHandle className="h-px bg-neutral-800 hover:bg-neutral-600 transition-colors" />
                        <Panel defaultSize={35} minSize={15}>
                            <BottomPanel
                                selectedBoard={selectedBoard || 'esp32'}
                                detectedBoard={detectedBoard}
                                connectedPort={connectedPort}
                                onNewProject={() => setShowNewProjectWizard(true)}
                                onOpenProject={() => window.electronAPI?.openFolder?.()}
                                onGenerateCode={() => window.dispatchEvent(new CustomEvent('generate-from-peripherals'))}
                                {...peripheralCounts}
                            />
                        </Panel>
                    </PanelGroup>
                </Panel>
                <PanelResizeHandle className="w-px bg-neutral-800 hover:bg-neutral-600 transition-colors" />
                <Panel defaultSize={30} minSize={20} maxSize={40}>
                    <AIAssistant />
                </Panel>
            </PanelGroup>
        </div>
    );
}

export default App;
