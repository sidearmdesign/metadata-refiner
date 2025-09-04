# MetaData Refiner

![Flask](https://img.shields.io/badge/Flask-2.3.2-blue)
![OpenAI](https://img.shields.io/badge/OpenAI_API-1.0-green)
![Electron](https://img.shields.io/badge/Electron-28.0-purple)
![Cross-Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-brightgreen)

AI-powered image metadata generation tool available as both a **cross-platform desktop app** and web application with Docker support.

## 🚀 Features
- 🖼️ **AI-powered metadata generation** using GPT-5-nano
- 🖥️ **Cross-platform desktop app** (Windows, macOS, Linux)
- 🌐 **Web interface** with Docker deployment
- 📂 **Native file dialogs** and drag & drop support
- 🔔 **System notifications** for processing completion
- ⚙️ **Multiple output profiles** (Zedge, Adobe Stock)
- 🔌 **Real-time processing updates** via WebSocket
- 📊 **CSV export** with profile-specific formatting
- 🔧 **Auto-updater ready** for desktop releases

## 📥 Installation Options

Choose your preferred installation method:

## Option 1: 🖥️ Desktop App (Recommended for Personal Use)

**Perfect for**: Personal productivity, client work, offline usage

### Prerequisites
- **Node.js** (v16+): Download from [nodejs.org](https://nodejs.org/)
- **Python 3** (for AI processing backend)

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/sidearmdesign/metadata-refiner.git
   cd metadata-refiner
   ```

2. **Install dependencies:**
   ```bash
   npm install                    # Desktop app dependencies
   pip install -r requirements.txt  # Python AI backend
   ```

3. **Launch desktop app:**
   ```bash
   npm start
   ```
   The app will open automatically with native desktop features!

### Building for Distribution
```bash
npm run build-all    # Build for Windows, macOS, Linux
npm run build-mac    # macOS only (.dmg)
npm run build-win    # Windows only (.exe)
npm run build-linux  # Linux only (.AppImage, .deb)
```

---

## Option 2: 🐳 Docker (Recommended for Server Deployment)

**Perfect for**: Team sharing, server deployment, web access

### Prerequisites
- **Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)

### Quick Start
1. **Clone and build:**
   ```bash
   git clone https://github.com/sidearmdesign/metadata-refiner.git
   cd metadata-refiner
   docker build -t mdr .
   ```

2. **Run container:**
   ```bash
   docker run -p 5001:5001 --name=metadata-refiner mdr
   ```

3. **Access:** Open http://localhost:5001 in your browser

---

## Option 3: 🐍 Direct Python (Development)

**Perfect for**: Development, customization, debugging

### Quick Start
1. **Clone and install:**
   ```bash
   git clone https://github.com/sidearmdesign/metadata-refiner.git
   cd metadata-refiner
   pip install -r requirements.txt
   ```

2. **Run Flask app:**
   ```bash
   python app.py
   ```

3. **Access:** Open http://localhost:5001 in your browser

---

## ⚙️ Configuration

### API Key Setup
**Required**: You need an OpenAI API key to use the AI metadata generation.

**Method 1: Environment Variable (Recommended)**
```bash
# Create .env file in project root
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-secret-key-here
```

**Method 2: Settings UI**
- **Desktop App**: Click Settings button in the app
- **Web Version**: Click Settings button at localhost:5001

The app checks for the API key in `.env` first, then falls back to the Settings UI.

### Profile Configuration
Edit `profiles.json` to customize output formats:

**Zedge Profile**: Wallpaper marketplace format
- Title (30-60 chars), Description (100-150 chars)
- 10 comma-separated tags, Predefined categories

**Adobe Stock Profile**: Stock photography format
- SEO-optimized title (70-90 chars)
- 23-28 keyword tags for discoverability

**Add Custom Profiles**: Define your own metadata formats

---

## 🔍 Desktop vs Web Comparison

| Feature | Desktop App | Web/Docker |
|---------|-------------|------------|
| **Installation** | Node.js + npm install | Docker only |
| **User Experience** | Native menus, dialogs, notifications | Browser-based |
| **File Access** | Direct file system access | Upload required |
| **Offline Usage** | ✅ Full offline capability | ❌ Requires server |
| **Multi-user** | ❌ Single user | ✅ Multiple users |
| **System Integration** | ✅ System tray, shortcuts | ❌ Browser only |
| **Auto-updates** | ✅ Built-in updater | ❌ Manual update |
| **Best for** | Personal productivity | Team/server deployment |

---

## 🔧 API Documentation

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/profiles` | GET | Get available processing profiles |
| `/upload` | POST | Upload images for processing |
| `/export` | POST | Export metadata as CSV |

**WebSocket**: `/socket.io` - Real-time processing updates

---

## 🔄 Updating

### Desktop App
```bash
git pull                    # Get latest changes
npm install                 # Update dependencies
npm start                   # Run updated app
```

### Docker Version
```bash
git pull                    # Get latest changes  
docker build -t mdr .       # Rebuild container
docker run -p 5001:5001 --name=metadata-refiner mdr  # Run updated container
```

### Direct Python
```bash
git pull                           # Get latest changes
pip install -r requirements.txt   # Update Python packages
python app.py                      # Run updated app
```

---

## 🐛 Troubleshooting

**Desktop App Issues:**
- Ensure Node.js v16+ and Python 3 are installed
- Check that ports 5001+ are available
- Run `npm install` to update dependencies

**Docker Issues:**
- Ensure Docker Desktop is running
- Check port 5001 is not in use
- Try `docker system prune` to clean up

**API Errors:**
- Verify OpenAI API key is valid and has credits
- Check `.env` file format and location
- Categories not in profile list will auto-set to "Other"

---

## 📄 License
MIT License - See [LICENSE](LICENSE) for details

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both desktop and web versions
5. Submit a pull request

**Development Setup:**
```bash
# For desktop development
npm install && npm run dev

# For web development  
python app.py
```