"""Centralized configuration for MetaData Refiner."""

import os
import secrets
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AppConfig:
    """Application configuration with environment variable support."""

    # Server settings
    host: str = field(default_factory=lambda: os.getenv('HOST', '127.0.0.1'))
    port: int = field(default_factory=lambda: int(os.getenv('PORT', '5001')))
    debug: bool = field(default_factory=lambda: os.getenv('FLASK_DEBUG', '1') == '1')

    # Security
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY') or secrets.token_hex(32))

    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: tuple = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')

    # Rate limiting
    default_rate_limits: List[str] = field(default_factory=lambda: ["200 per day", "50 per hour"])
    upload_rate_limit: str = "30 per minute"
    export_rate_limit: str = "20 per minute"
    socket_rate_limit: int = 60  # requests per minute per client
    socket_rate_window: int = 60  # seconds

    # API settings
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv('OPENAI_API_KEY'))
    openai_model: str = "gpt-5-nano-2025-08-07"
    openai_timeout: float = 60.0

    # Caching
    cache_ttl: int = 3600  # 1 hour
    max_image_dimension: int = 1024
    jpeg_quality: int = 85

    # Paths
    upload_folder: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'static/images/'
    ))

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return os.getenv('FLASK_ENV') == 'production'

    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed CORS origins for Socket.IO."""
        return [
            f'http://localhost:{self.port}',
            f'http://127.0.0.1:{self.port}',
            'http://localhost:5001',
            'http://127.0.0.1:5001'
        ]

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings."""
        warnings = []

        if not self.secret_key or self.secret_key == 'change-me-in-production':
            if self.is_production:
                warnings.append("WARNING: Using generated SECRET_KEY. Set SECRET_KEY environment variable for deployed servers.")

        if not self.openai_api_key:
            warnings.append("NOTE: OPENAI_API_KEY not set. Users must provide API key via Settings.")

        if self.max_file_size > 50 * 1024 * 1024:
            warnings.append("WARNING: Max file size is very large (>50MB). Consider reducing for better performance.")

        return warnings


# Global configuration instance
config = AppConfig()
