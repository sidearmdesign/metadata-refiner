# MetaData Refiner

![Flask](https://img.shields.io/badge/Flask-2.3.2-blue)
![OpenAI](https://img.shields.io/badge/OpenAI_API-1.0-green)

AI-powered image metadata generation tool with profile-based processing and Docker support.

## Features
- 🖼️ Automated metadata generation for images using GPT-4
- ⚙️ Profile-based processing configurations
- 🐳 Docker containerization for production deployment
- 🔌 WebSocket-based real-time processing updates
- 📁 CSV export with profile-specific column mappings
- 🔒 Secure session management with cryptographic secrets

## Installation

### Docker (Production)
```bash
docker build -t metadata-refiner .
docker run -d -p 5001:5001 \
  -e OPENAI_API_KEY=your_openai_key \
  -e SECRET_KEY=your_secret_key \
  metadata-refiner
```

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with:
echo "OPENAI_API_KEY=your_openai_key" > .env
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(20))')" >> .env

# Start development server
flask run --port 5001
```

## Configuration

### Environment Variables
```ini
# Required OpenAI API key - get from https://platform.openai.com
OPENAI_API_KEY=your_openai_key

# Cryptographic secret for session security
SECRET_KEY=your_generated_secret
```

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
