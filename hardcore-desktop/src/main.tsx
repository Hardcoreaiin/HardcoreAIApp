import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ErrorBoundary } from 'react-error-boundary';
import { BoardProvider } from './context/BoardContext';
import { AuthProvider } from './context/AuthContext';

function ErrorFallback({ error }: { error: Error }) {
    return (
        <div className="min-h-screen bg-bg-dark flex items-center justify-center p-8">
            <div className="bg-bg-surface border border-red-500/30 rounded-xl p-8 max-w-lg">
                <h2 className="text-xl font-bold text-red-500 mb-4">Something went wrong</h2>
                <pre className="text-sm text-text-muted bg-bg-dark p-4 rounded overflow-auto">
                    {error.message}
                </pre>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-4 px-4 py-2 bg-accent-primary text-white rounded-lg"
                >
                    Reload App
                </button>
            </div>
        </div>
    );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
            <AuthProvider>
                <BoardProvider>
                    <App />
                </BoardProvider>
            </AuthProvider>
        </ErrorBoundary>
    </React.StrictMode>
);
