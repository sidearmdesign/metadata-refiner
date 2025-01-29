# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy and install dependencies globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Ensure the static/images directory exists
RUN mkdir -p /static/images
RUN chown -R appuser:appuser /static

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local

# Copy the entire application, including necessary files like profiles.json
COPY . .

# Set the PATH to include global Python packages
ENV PATH=/usr/local/bin:/usr/local/sbin:$PATH

# Set production environment variables
ENV FLASK_DEBUG=0
ENV FLASK_ENV=production

# Create a non-root user and adjust permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the application's port
EXPOSE 5001

# Command to start Gunicorn with desired configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--worker-class", "eventlet", "-w", "1", "app:app"]
