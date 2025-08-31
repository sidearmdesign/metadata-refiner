# MetaData Refiner

![Flask](https://img.shields.io/badge/Flask-2.3.2-blue)
![OpenAI](https://img.shields.io/badge/OpenAI_API-1.0-green)

AI-powered image metadata generation tool with profile-based processing and Docker support.

## Features
- 🖼️ Automated metadata generation for images using GPT-5-nano
- Drag & drop image upload
- Generate metadata and then edit before export
- ⚙️ Profiles for different metadata types
- 🐳 Docker container for deployment
- 🔌 WebSocket-based real-time processing updates
- 📁 CSV export with profile-specific column mappings

## Installation

To install and run the MetaData Refiner, follow these steps:

### 1. Open a Terminal or Command Prompt

*   **Windows:**
    *   Press the Windows key, type `cmd` or `powershell`, and press Enter to open Command Prompt or PowerShell.
*   **macOS:**
    *   Open Finder, go to `Applications` -> `Utilities`, and double-click `Terminal`.
*   **Linux:**
    *   Press `Ctrl+Alt+T` or search for "terminal" in your applications.

### 2. Clone the GitHub Repository

First, you need to install Git if you don't have it already. You can download it from [https://git-scm.com/downloads](https://git-scm.com/downloads).

Once Git is installed, clone the repository using the following command:

```bash
git clone https://github.com/sidearmdesign/metadata-refiner.git
cd metadata-refiner
```

### 3. Install Docker

This project uses Docker for easy deployment. Follow the instructions for your operating system:

*   **Windows:**
    *   Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).
*   **macOS:**
    *   Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).
*   **Linux:**
    *   Follow the instructions for your distribution from [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/).

### 4. Build and Run the Docker Container

```bash
docker build -t mdr .
docker run -p 5001:5001 --name=metadata-refiner mdr
```

## Configuration
Open localhost:5001
Add your OpenAI API key to the Settings (button in the upper right)


### Profile Configuration
Edit `profiles.json` to customize:
- AI processing prompts
- Required metadata fields
- Valid categories
- CSV export columns

## API Documentation

| Endpoint       | Method | Description                          |
|----------------|--------|--------------------------------------|
| /api/profiles  | GET    | Get available processing profiles    |
| /upload        | POST   | Upload images for processing         |
| /export        | POST   | Export metadata as CSV               |

WebSocket Endpoint: `/socket.io`

## License
MIT License - See [LICENSE](LICENSE) for details
