# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies globally to avoid PATH issues
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy global Python packages from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY . .

# Set the PATH to ensure globally installed packages are accessible
ENV PATH=/usr/local/bin:/usr/local/sbin:$PATH

# Set production environment variables
ENV FLASK_DEBUG=0
ENV FLASK_ENV=production

# Create a non-root user and set proper permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application's port
EXPOSE 5001

# Run Gunicorn with the desired configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--worker-class", "eventlet", "-w", "1", "app:app"]
