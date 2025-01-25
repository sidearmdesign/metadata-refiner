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

## Requirements
- Docker installed
- OpenAI API key
- Secret key for Flask sessions

## Environment Variables
Create a .env file with:
```ini
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
```

## Development Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
