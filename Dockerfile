# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy and install dependencies globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Ensure the non-root user exists before changing permissions
RUN getent group appuser || groupadd -r appuser && useradd -r -g appuser appuser

# Ensure necessary directories exist for static files and uploads
RUN mkdir -p /app/static/images && chown -R appuser:appuser /app/static

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy the entire application, including profiles.json
COPY . .

# Set ownership of application files to appuser
RUN chown -R appuser:appuser /app

# Set the PATH to include global Python packages
ENV PATH=/usr/local/bin:/usr/local/sbin:$PATH

# Set production environment variables
ENV FLASK_DEBUG=0
ENV FLASK_ENV=production

# Switch to the non-root user
USER appuser

# Expose the application's port
EXPOSE 5001

# Command to start Gunicorn with desired configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--worker-class", "eventlet", "-w", "1", "app:app"]
