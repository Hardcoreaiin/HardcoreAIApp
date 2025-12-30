import React, { useState } from 'react';
import { X, FolderPlus, ChevronRight, ChevronLeft, Check } from 'lucide-react';

interface NewProjectWizardProps {
    isOpen: boolean;
    onClose: () => void;
    onCreateProject: (name: string, board: string, path: string) => void;
}

const boards = [
    { id: 'esp32dev', name: 'ESP32 DevKit', description: 'Dual-core, WiFi, Bluetooth' },
    { id: 'esp32-s3', name: 'ESP32-S3', description: 'AI acceleration, USB OTG' },
    { id: 'uno', name: 'Arduino Uno', description: 'ATmega328P, 16MHz' },
    { id: 'nano', name: 'Arduino Nano', description: 'Compact, breadboard-friendly' },
    { id: 'mega', name: 'Arduino Mega', description: '54 I/O pins, 4 UARTs' },
];

const NewProjectWizard: React.FC<NewProjectWizardProps> = ({ isOpen, onClose, onCreateProject }) => {
    const [step, setStep] = useState(1);
    const [projectName, setProjectName] = useState('');
    const [selectedBoard, setSelectedBoard] = useState('esp32dev');
    const [projectPath, setProjectPath] = useState('');

    if (!isOpen) return null;

    const handleCreate = () => {
        if (projectName.trim()) {
            onCreateProject(projectName, selectedBoard, projectPath || `./projects/${projectName}`);
            onClose();
            // Reset state
            setStep(1);
            setProjectName('');
            setSelectedBoard('esp32dev');
            setProjectPath('');
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-bg-surface border border-border rounded-2xl shadow-2xl w-[600px] max-h-[80vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <FolderPlus className="w-5 h-5 text-accent-primary" />
                        <h2 className="text-lg font-semibold text-text-primary">New Project</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-bg-hover rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-text-muted" />
                    </button>
                </div>

                {/* Progress */}
                <div className="flex items-center px-6 py-3 border-b border-border">
                    <div className={`flex items-center gap-2 ${step >= 1 ? 'text-accent-primary' : 'text-text-muted'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step >= 1 ? 'bg-accent-primary text-white' : 'bg-bg-elevated'}`}>
                            {step > 1 ? <Check className="w-4 h-4" /> : '1'}
                        </div>
                        <span className="text-sm">Project Info</span>
                    </div>
                    <div className="flex-1 h-px bg-border mx-4" />
                    <div className={`flex items-center gap-2 ${step >= 2 ? 'text-accent-primary' : 'text-text-muted'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step >= 2 ? 'bg-accent-primary text-white' : 'bg-bg-elevated'}`}>
                            {step > 2 ? <Check className="w-4 h-4" /> : '2'}
                        </div>
                        <span className="text-sm">Select Board</span>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6">
                    {step === 1 && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-text-primary mb-2">
                                    Project Name
                                </label>
                                <input
                                    type="text"
                                    value={projectName}
                                    onChange={(e) => setProjectName(e.target.value)}
                                    placeholder="my_project"
                                    className="w-full px-4 py-2 bg-bg-elevated border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-primary mb-2">
                                    Location (optional)
                                </label>
                                <input
                                    type="text"
                                    value={projectPath}
                                    onChange={(e) => setProjectPath(e.target.value)}
                                    placeholder="./projects/my_project"
                                    className="w-full px-4 py-2 bg-bg-elevated border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-primary"
                                />
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-3">
                            <p className="text-sm text-text-muted mb-4">Select a target board:</p>
                            {boards.map((board) => (
                                <button
                                    key={board.id}
                                    onClick={() => setSelectedBoard(board.id)}
                                    className={`w-full flex items-center gap-4 p-4 rounded-lg border transition-colors ${selectedBoard === board.id
                                            ? 'border-accent-primary bg-accent-primary/10'
                                            : 'border-border hover:bg-bg-hover'
                                        }`}
                                >
                                    <div className="w-10 h-10 bg-bg-elevated rounded-lg flex items-center justify-center">
                                        <span className="text-lg">🔌</span>
                                    </div>
                                    <div className="text-left">
                                        <div className="text-sm font-medium text-text-primary">{board.name}</div>
                                        <div className="text-xs text-text-muted">{board.description}</div>
                                    </div>
                                    {selectedBoard === board.id && (
                                        <Check className="w-5 h-5 text-accent-primary ml-auto" />
                                    )}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-bg-elevated">
                    <button
                        onClick={() => setStep(Math.max(1, step - 1))}
                        disabled={step === 1}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-text-muted hover:text-text-primary disabled:opacity-50 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        Back
                    </button>

                    {step < 2 ? (
                        <button
                            onClick={() => setStep(step + 1)}
                            disabled={!projectName.trim()}
                            className="flex items-center gap-2 px-4 py-2 bg-accent-primary text-white text-sm font-medium rounded-lg hover:bg-accent-primary/80 disabled:opacity-50 transition-colors"
                        >
                            Next
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    ) : (
                        <button
                            onClick={handleCreate}
                            className="flex items-center gap-2 px-4 py-2 bg-accent-primary text-white text-sm font-medium rounded-lg hover:bg-accent-primary/80 transition-colors"
                        >
                            <FolderPlus className="w-4 h-4" />
                            Create Project
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NewProjectWizard;
