# MetaData Refiner Installation Guide

## Docker Setup (Recommended for Production)

1. Build the Docker image:
```bash
docker build -t metadata-refiner .
```

2. Run the container:
```bash
docker run -d -p 5001:5001 \
  -e OPENAI_API_KEY=your_openai_key \
  -e SECRET_KEY=your_secret_key \
  metadata-refiner
```

# SECRET_KEY explanation:
# This is a cryptographic key used to secure Flask session cookies. 
# It should be a long, random string (40+ characters). Generate one with:
# python -c 'import secrets; print(secrets.token_hex(20))'

## Requirements
- Docker installed
- OpenAI API key (Get from https://platform.openai.com)
- Secret key for Flask sessions - Used to cryptographically secure 
  user sessions and flash messages. Never share this key!

## Environment Variables
Create a .env file with:
```ini
# Required for AI processing - get from OpenAI dashboard
OPENAI_API_KEY=your_openai_key

# Cryptographic secret for session security - generate with:
# python -c 'import secrets; print(secrets.token_hex(20))'
SECRET_KEY=your_secret_key
```

## Development Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
