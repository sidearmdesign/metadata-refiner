# Super Tagger Installation Guide

## Prerequisites
- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Python 3.11+ (for local development without Docker)
- pip package manager
- Git (recommended)

## Installation Steps

### 1. Clone repository
```bash
git clone https://github.com/your-username/super-tagger.git
cd super-tagger
```

### 2. Build Docker image
```bash
docker build -t super-tagger .
```

### 3. Run container
```bash
docker run -dp 5001:5001 --name super-tagger-app super-tagger
```

### 4. Environment setup
```bash
cp .env.example .env  # Update values in .env as needed
```

## Running the Application

### Docker (Production)
```bash
docker start super-tagger-app
```

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run --port 5001
```

## Configuration
Environment variables (set in `.env`):
- `FLASK_DEBUG=0` (production) / `1` (development)
- `FLASK_ENV=production` or `development`
- `PORT=5001`

## Troubleshooting

### Common Issues
1. **Docker not running**: Ensure Docker Desktop is active
2. **Port conflict**: Check if port 5001 is available
3. **Missing dependencies**: Run `docker system prune -a` and rebuild
4. **Permission issues**: Add `USER root` to Dockerfile for debugging

## Verify Installation
Access the application at:  
http://localhost:5001

To stop the container:
```bash
docker stop super-tagger-app
```
