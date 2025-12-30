import React, { useState, useCallback } from 'react';
import { ChevronRight, ChevronDown, Folder, FileText } from 'lucide-react';

interface ProjectExplorerProps {
    onFileClick: (path: string, content: string) => void;
    currentProject: { id: string; name: string; path: string } | null;
}

interface FileNode { name: string; path: string; type: 'file' | 'folder'; children?: FileNode[]; content?: string; }

const defaultProject: FileNode = {
    name: 'current_project', path: '/current_project', type: 'folder',
    children: [{ name: 'main.cpp', path: '/current_project/main.cpp', type: 'file', content: '#include <Arduino.h>\n\nvoid setup() {\n    Serial.begin(115200);\n    Serial.println("Hello from Hardcore.ai!");\n}\n\nvoid loop() {\n    delay(1000);\n}\n' }],
};

const ProjectExplorer: React.FC<ProjectExplorerProps> = ({ onFileClick }) => {
    const [expanded, setExpanded] = useState<Set<string>>(new Set(['/current_project']));
    const [selected, setSelected] = useState<string | null>(null);

    const toggle = useCallback((path: string) => setExpanded(prev => { const n = new Set(prev); n.has(path) ? n.delete(path) : n.add(path); return n; }), []);
    const click = useCallback((node: FileNode) => { if (node.type === 'file') { setSelected(node.path); onFileClick(node.path, node.content || ''); } }, [onFileClick]);

    const render = (node: FileNode, depth = 0): JSX.Element => {
        const open = expanded.has(node.path);
        const sel = selected === node.path;
        const pad = depth * 12 + 8;

        if (node.type === 'folder') return (
            <div key={node.path}>
                <div onClick={() => toggle(node.path)} className="flex items-center gap-1 py-0.5 cursor-pointer hover:bg-neutral-800" style={{ paddingLeft: pad }}>
                    {open ? <ChevronDown className="w-3.5 h-3.5 text-neutral-500" /> : <ChevronRight className="w-3.5 h-3.5 text-neutral-500" />}
                    <Folder className="w-3.5 h-3.5 text-neutral-400" />
                    <span className="text-sm text-neutral-300 ml-1">{node.name}</span>
                </div>
                {open && node.children?.map(c => render(c, depth + 1))}
            </div>
        );

        return (
            <div key={node.path} onClick={() => click(node)} className={`flex items-center gap-1 py-0.5 cursor-pointer ${sel ? 'bg-neutral-800' : 'hover:bg-neutral-800'}`} style={{ paddingLeft: pad + 16 }}>
                <FileText className="w-3.5 h-3.5 text-neutral-500" />
                <span className="text-sm text-neutral-400 ml-1">{node.name}</span>
            </div>
        );
    };

    return <div className="h-full py-2 overflow-y-auto bg-neutral-950">{render(defaultProject)}</div>;
};

export default ProjectExplorer;
