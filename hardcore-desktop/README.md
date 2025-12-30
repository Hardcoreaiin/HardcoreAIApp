# Hardcore.ai Desktop App

Electron + React + Vite desktop application for AI-powered hardware development.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Build

```bash
# Build for Windows
npm run package:win

# Build for macOS
npm run package:mac

# Build for Linux
npm run package:linux
```

## Structure

```
hardcore-desktop/
├── electron/          # Electron main & preload
├── src/               # React frontend
│   ├── components/    # UI components
│   ├── context/       # React contexts
│   └── App.tsx        # Main app
├── package.json
└── vite.config.ts
```
