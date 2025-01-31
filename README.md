# MetaData Refiner

![Flask](https://img.shields.io/badge/Flask-2.3.2-blue)
![OpenAI](https://img.shields.io/badge/OpenAI_API-1.0-green)

AI-powered image metadata generation tool with profile-based processing and Docker support.

## Features
- 🖼️ Automated metadata generation for images using GPT-4o-mini
- Drag & drop image upload
- Generate metadata and then edit before export
- ⚙️ Profiles for different metadata types
- 🐳 Docker container for deployment
- 🔌 WebSocket-based real-time processing updates
- 📁 CSV export with profile-specific column mappings

## Installation

### Docker
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
