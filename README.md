# 🔥 Hardcore.ai - AI-Powered Hardware IDE

> **"Cursor for Hardware"** - The first AI-powered IDE that lets you describe hardware behavior in plain English and generates ready-to-flash firmware.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Node](https://img.shields.io/badge/node-18+-green)
![Python](https://img.shields.io/badge/python-3.10+-yellow)

## ✨ Features

- 🤖 **AI Code Generation** - Describe what you want in plain English, get working firmware
- ⚡ **One-Click Flash** - Build and flash directly from the IDE
- 🔌 **Auto-Detect Boards** - Automatic USB device detection (ESP32, Arduino, STM32)
- 📊 **Visual Pin Diagrams** - Interactive board visualizations with pin highlighting
- 📡 **Serial Monitor** - Real-time serial communication
- 🎨 **Modern Dark UI** - Beautiful, professional interface

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.10+ ([Download](https://python.org/))
- **PlatformIO Core** ([Install Guide](https://docs.platformio.org/en/latest/core/installation.html))

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/hardcoreai.git
cd hardcoreai

# Install Desktop App
cd hardcore-desktop
npm install

# Install Backend
cd ../Hardcore.ai
pip install -r requirements.txt
```

### Running the App

**Option 1: One-Click Launch (Windows)**
```bash
# From root directory
./LAUNCH_DESKTOP.bat
```

**Option 2: Manual Launch**
```bash
# Terminal 1: Start Backend
cd Hardcore.ai/orchestrator
python main.py

# Terminal 2: Start Desktop App
cd hardcore-desktop
npm run dev
```

The app will open at `http://localhost:5173`

## 📁 Project Structure

```
hardcoreai/
├── hardcore-desktop/     # Electron + React Desktop App
│   ├── src/             # React components & frontend
│   ├── electron/        # Electron main process
│   └── package.json
│
├── Hardcore.ai/         # Python Backend (AI + Build)
│   ├── orchestrator/    # AI & firmware generation
│   │   ├── ai.py       # Gemini AI integration
│   │   ├── main.py     # FastAPI server
│   │   └── ...
│   └── requirements.txt
│
└── LAUNCH_DESKTOP.bat   # One-click launcher
```

## ⚙️ Configuration

### Gemini API Key

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Create `Hardcore.ai/.env`:
   ```
   LLM_API_KEY=your_gemini_api_key_here
   ```

### Supported Boards

- ESP32 DevKit
- Arduino Uno/Nano/Mega
- STM32 (various)
- RP2040 (Pico)

## 🛠️ Building for Distribution

```bash
cd hardcore-desktop

# Windows
npm run package:win

# macOS
npm run package:mac

# Linux
npm run package:linux

# All platforms
npm run package:all
```

Outputs will be in `hardcore-desktop/dist/`

## 📖 Usage

1. **Detect your board** - Click "Detect" in the top bar
2. **Describe your project** - Type in the AI assistant:
   > "Make a motor controller using L298N with pins ENA-19, IN1-21, IN2-18, move forward for 3 seconds then stop"
3. **Review generated code** - Check the editor
4. **Flash to hardware** - Click "Flash" button

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- PlatformIO for build system
- Electron & React for desktop framework

---

**Made with ❤️ by the Hardcore.ai Team**
