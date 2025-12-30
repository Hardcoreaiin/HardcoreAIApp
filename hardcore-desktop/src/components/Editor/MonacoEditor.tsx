import React, { memo } from 'react';
import Editor from '@monaco-editor/react';
import { X } from 'lucide-react';

interface OpenFile { path: string; name: string; content: string; isDirty?: boolean; }
interface MonacoEditorProps {
    value: string;
    onChange: (value: string | undefined) => void;
    language?: string;
    openFiles?: OpenFile[];
    activeFilePath?: string;
    onTabClick?: (path: string) => void;
    onTabClose?: (path: string) => void;
}

const MonacoEditor: React.FC<MonacoEditorProps> = memo(({ value, onChange, language = 'cpp', openFiles = [], activeFilePath, onTabClick, onTabClose }) => (
    <div className="h-full w-full flex flex-col bg-neutral-950">
        <div className="h-9 flex items-center bg-neutral-900 border-b border-neutral-800 overflow-x-auto">
            {openFiles.map(f => (
                <div key={f.path} onClick={() => onTabClick?.(f.path)} className={`flex items-center gap-2 px-3 h-full border-r border-neutral-800 cursor-pointer transition-colors ${activeFilePath === f.path ? 'bg-neutral-950 text-neutral-100' : 'bg-neutral-900 text-neutral-500 hover:text-neutral-300'}`}>
                    <span className="text-sm">{f.name}</span>
                    {f.isDirty && <span className="text-neutral-400">•</span>}
                    <button onClick={e => { e.stopPropagation(); onTabClose?.(f.path); }} className="p-0.5 rounded hover:bg-neutral-800 text-neutral-500 hover:text-neutral-300"><X className="w-3.5 h-3.5" /></button>
                </div>
            ))}
        </div>
        <div className="flex-1">
            <Editor height="100%" language={language} value={value} onChange={onChange} theme="vs-dark" options={{ fontSize: 14, fontFamily: "'JetBrains Mono', Consolas, monospace", minimap: { enabled: true }, scrollBeyondLastLine: false, wordWrap: 'on', lineNumbers: 'on', renderLineHighlight: 'all', smoothScrolling: true, padding: { top: 16, bottom: 16 }, automaticLayout: true }} />
        </div>
    </div>
));

MonacoEditor.displayName = 'MonacoEditor';
export default MonacoEditor;
