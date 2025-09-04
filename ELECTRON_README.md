# MetaData Refiner - Desktop Application

This is the cross-platform desktop version of MetaData Refiner built with Electron.

## Prerequisites

1. **Node.js** (version 16 or higher)
   - Download from https://nodejs.org/
   - Verify installation: `node --version`

2. **Python 3** (for the backend server)
   - Should already be installed for the Flask app
   - Required Python packages are in `requirements.txt`

## Quick Start

1. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

2. **Install Python dependencies (if not already done):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the desktop app:**
   ```bash
   npm start
   ```

## Development

- **Development mode with DevTools:**
  ```bash
  npm run dev
  ```

- **Build for current platform:**
  ```bash
  npm run build
  ```

- **Build for all platforms:**
  ```bash
  npm run build-all
  ```

- **Build for specific platforms:**
  ```bash
  npm run build-mac    # macOS
  npm run build-win    # Windows
  npm run build-linux  # Linux
  ```

## Features

### Desktop-Specific Features
- **Native file dialogs** - Better file selection experience
- **System notifications** - Get notified when processing completes
- **System tray integration** - Minimize to system tray
- **Auto-updater ready** - Built-in update mechanism
- **Offline capable** - No need for Docker or server setup

### Cross-Platform Support
- **Windows** - .exe installer with NSIS
- **macOS** - .dmg installer with Apple Silicon support
- **Linux** - AppImage and .deb packages

## Configuration

### API Key Setup
Same as the web version - you can set your OpenAI API key in:
1. `.env` file (recommended)
2. Settings dialog within the app

### Customizing Builds
- Edit `package.json` under the `"build"` section
- Replace icons in `build/` directory with your own
- Update app metadata and signing certificates

## Troubleshooting

### Common Issues

1. **Python server won't start:**
   - Ensure all Python dependencies are installed
   - Check that port 5001 (or next available) is free

2. **Build fails:**
   - Make sure all dependencies are installed: `npm install`
   - For macOS builds on non-Mac systems, use GitHub Actions

3. **Icons look wrong:**
   - Replace placeholder icons in `build/` directory
   - Use proper icon formats (.icns for Mac, .ico for Windows)

### Getting Help
- Check the main README.md for Flask app configuration
- File issues on the GitHub repository
- Ensure Python and Node.js versions meet requirements

## Distribution

The built applications will be in the `dist/` directory:
- **macOS**: `dist/MetaData Refiner-1.0.0.dmg`
- **Windows**: `dist/MetaData Refiner Setup 1.0.0.exe`
- **Linux**: `dist/MetaData Refiner-1.0.0.AppImage`

## Updating from Web Version

If you're migrating from the web/Docker version:
1. Your existing `.env` file and `profiles.json` will work as-is
2. No need to run Docker anymore
3. The desktop app includes the Flask server automatically