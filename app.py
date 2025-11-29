from flask import Flask, render_template, request, jsonify, send_file, g, url_for
import json
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import re
import hashlib
import time
from functools import wraps
from collections import defaultdict
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd
import openai
from dotenv import load_dotenv
import base64
from io import BytesIO
import httpx

# Load environment variables and profiles
load_dotenv()

# Import centralized configuration
from config import config

# Handle profiles.json path for both development and bundled app
profiles_path = 'profiles.json'
if not os.path.exists(profiles_path):
    # Try alternate path for bundled app
    profiles_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles.json')

with open(profiles_path) as f:
    PROFILES = json.load(f)['profiles']


# API Response Caching
metadata_cache = {}
CACHE_TTL = config.cache_ttl


def get_image_hash(image_path):
    """Generate consistent hash for image content."""
    try:
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def get_cached_metadata(image_hash, profile_name):
    """Retrieve cached metadata if available and not expired."""
    cache_key = f"{image_hash}:{profile_name}"
    if cache_key in metadata_cache:
        entry = metadata_cache[cache_key]
        if time.time() - entry['timestamp'] < CACHE_TTL:
            return entry['metadata']
        # Cache expired, remove it
        del metadata_cache[cache_key]
    return None


def cache_metadata(image_hash, profile_name, metadata):
    """Store metadata in cache with timestamp."""
    cache_key = f"{image_hash}:{profile_name}"
    metadata_cache[cache_key] = {
        'metadata': metadata,
        'timestamp': time.time()
    }


# Security: Validation helpers
def validate_api_key_format(key):
    """Validate OpenAI API key format (sk- prefix, alphanumeric)."""
    if not key or not isinstance(key, str):
        return False
    # OpenAI keys typically start with 'sk-' followed by alphanumeric chars
    # Some newer keys may have different formats (sk-proj-, sk-svcacct-, etc.)
    return bool(re.match(r'^sk-[a-zA-Z0-9_-]{20,}$', key))


def validate_profile_name(profile_name):
    """Validate profile name exists in configuration."""
    return profile_name in PROFILES


def validate_file_path(file_path, base_dir):
    """Prevent path traversal attacks by ensuring path is within base directory."""
    if not file_path or not isinstance(file_path, str):
        return False
    # Normalize paths
    base_dir = os.path.realpath(base_dir)
    full_path = os.path.realpath(os.path.join(base_dir, os.path.basename(file_path)))
    # Ensure path is within base directory
    return full_path.startswith(base_dir)


def classify_error(exception):
    """Classify exception into user-friendly category with actionable guidance."""
    error_str = str(exception).lower()

    if 'unauthorized' in error_str or 'invalid api key' in error_str or '401' in error_str:
        return {
            'category': 'auth',
            'title': 'Authentication Error',
            'message': 'Invalid or expired API key',
            'action': 'Check your API key in Settings',
            'retry_allowed': False
        }
    elif 'rate limit' in error_str or 'quota' in error_str or '429' in error_str:
        return {
            'category': 'quota',
            'title': 'Rate Limit Exceeded',
            'message': 'Too many requests or quota exceeded',
            'action': 'Wait a moment and try again',
            'retry_allowed': True
        }
    elif 'timeout' in error_str or 'timed out' in error_str:
        return {
            'category': 'timeout',
            'title': 'Request Timeout',
            'message': 'The AI service took too long to respond',
            'action': 'Try again - the service may be busy',
            'retry_allowed': True
        }
    elif 'connection' in error_str or 'network' in error_str or 'unreachable' in error_str:
        return {
            'category': 'network',
            'title': 'Network Error',
            'message': 'Could not connect to OpenAI',
            'action': 'Check your internet connection',
            'retry_allowed': True
        }
    elif 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str):
        return {
            'category': 'model',
            'title': 'Model Error',
            'message': 'The AI model is not available',
            'action': 'Contact support or check model configuration',
            'retry_allowed': False
        }
    else:
        return {
            'category': 'server',
            'title': 'Processing Error',
            'message': str(exception)[:200],  # Truncate long errors
            'action': 'Try again or contact support',
            'retry_allowed': True
        }


def check_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-OpenAI-Key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        g.api_key = api_key
        return f(*args, **kwargs)
    return decorated_function

# Configure Flask and SocketIO with async support
app = Flask(__name__)

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=config.default_rate_limits,
    storage_uri="memory://",
    strategy="fixed-window"
)

# Socket.IO rate limiting (simple in-memory tracker)
socket_rate_limits = defaultdict(lambda: {'count': 0, 'reset_time': 0})
SOCKET_RATE_LIMIT = config.socket_rate_limit
SOCKET_RATE_WINDOW = config.socket_rate_window


def check_socket_rate_limit(sid):
    """Check if socket client has exceeded rate limit."""
    now = time.time()
    client = socket_rate_limits[sid]

    # Reset counter if window has passed
    if now >= client['reset_time']:
        client['count'] = 0
        client['reset_time'] = now + SOCKET_RATE_WINDOW

    client['count'] += 1
    return client['count'] <= SOCKET_RATE_LIMIT


# Security: Use config for SECRET_KEY
app.config['SECRET_KEY'] = config.secret_key

# Print any configuration warnings
for warning in config.validate():
    print(warning, flush=True)

socketio = SocketIO(app,
                  cors_allowed_origins=config.allowed_origins,
                  async_mode='threading',
                  max_http_buffer_size=100 * 1024 * 1024)  # 100MB max for base64 images

# Use config for upload folder
app.config['UPLOAD_FOLDER'] = config.upload_folder


# Security: Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to prevent common attacks."""
    # Content Security Policy - allows inline scripts/styles needed by Bootstrap
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/profiles')
def get_profiles():
    """Return profile configurations for UI rendering"""
    return jsonify({
        'profiles': PROFILES,
        'default_profile': 'zedge'
    })


def save_profiles_to_file():
    """Save profiles to profiles.json file."""
    try:
        with open(profiles_path, 'w') as f:
            json.dump({'profiles': PROFILES}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving profiles: {e}", flush=True)
        return False


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create a new profile."""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Profile name is required'}), 400

    # Generate profile ID from name
    profile_id = data['name'].lower().replace(' ', '_')
    profile_id = re.sub(r'[^a-z0-9_]', '', profile_id)

    if not profile_id:
        return jsonify({'error': 'Invalid profile name'}), 400

    if profile_id in PROFILES:
        return jsonify({'error': 'Profile already exists'}), 400

    required_fields = data.get('required_fields', ['title', 'description', 'tags'])

    PROFILES[profile_id] = {
        'name': data['name'],
        'prompt': data.get('prompt', ''),
        'required_fields': required_fields,
        'categories': data.get('categories', []),
        'csv_columns': ['full_path'] + required_fields
    }

    if save_profiles_to_file():
        return jsonify({'id': profile_id, 'profile': PROFILES[profile_id]})
    else:
        # Rollback in-memory change if save failed
        del PROFILES[profile_id]
        return jsonify({'error': 'Failed to save profile'}), 500


@app.route('/api/profiles/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update an existing profile."""
    if profile_id not in PROFILES:
        return jsonify({'error': 'Profile not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Store old values for rollback
    old_profile = PROFILES[profile_id].copy()

    required_fields = data.get('required_fields', old_profile.get('required_fields', []))

    PROFILES[profile_id].update({
        'name': data.get('name', old_profile['name']),
        'prompt': data.get('prompt', old_profile.get('prompt', '')),
        'required_fields': required_fields,
        'categories': data.get('categories', old_profile.get('categories', [])),
        'csv_columns': ['full_path'] + required_fields
    })

    if save_profiles_to_file():
        return jsonify({'id': profile_id, 'profile': PROFILES[profile_id]})
    else:
        # Rollback in-memory change if save failed
        PROFILES[profile_id] = old_profile
        return jsonify({'error': 'Failed to save profile'}), 500


@app.route('/upload', methods=['POST'])
@limiter.limit(config.upload_rate_limit)
def upload():
    try:
        images = request.files.getlist('images')
        if not images or all(img.filename == '' for img in images):
            return jsonify({'error': 'No files selected'}), 400
        
        image_data = []
        allowed_extensions = set(config.allowed_extensions)

        for image in images:
            if not image or image.filename == '':
                continue

            # Validate file extension
            filename = secure_filename(image.filename)
            if not filename:
                continue

            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in allowed_extensions:
                continue

            # Check file size
            image.seek(0, os.SEEK_END)
            file_size = image.tell()
            image.seek(0)

            if file_size > config.max_file_size:
                continue
                
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                image.save(filepath)
                # Verify it's a valid image
                with Image.open(filepath) as img:
                    img.verify()
            except Exception as e:
                # Remove invalid file if it was saved
                if os.path.exists(filepath):
                    os.remove(filepath)
                continue
        
            # Use url_for to generate proper URL for the image
            image_url = url_for('static', filename=f'images/{filename}')
            
            image_data.append({
                'full_path': image_url,  # Use URL instead of filesystem path
                'file_path': filepath,   # Keep internal filesystem path for processing
                'title': '',
                'description': '',
                'tags': '',
                'category': ''
            })

        if not image_data:
            return jsonify({'error': 'No valid images uploaded. Please ensure files are images under 10MB.'}), 400
            
        return jsonify({'images': image_data})
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

from concurrent.futures import ThreadPoolExecutor
processing_executor = ThreadPoolExecutor(max_workers=4)

@socketio.on('generate_metadata')
def handle_generate_metadata(data):
    """Handle metadata generation request with input validation and rate limiting."""
    # Rate limiting for socket connections
    if not check_socket_rate_limit(request.sid):
        emit('error', {
            'message': 'Rate limit exceeded. Please wait before sending more requests.',
            'category': 'quota',
            'title': 'Too Many Requests',
            'action': 'Wait a moment before generating more metadata',
            'retry_allowed': True
        })
        return

    # Security: Validate request data structure
    if not isinstance(data, dict):
        emit('error', {'message': 'Invalid request format'})
        return

    # Security: Validate required fields exist
    full_path = data.get('full_path')
    if not full_path or not isinstance(full_path, str):
        emit('error', {'message': 'Missing or invalid image path'})
        return

    # Security: Validate profile name against known profiles
    profile_name = data.get('profile', 'zedge')
    if not validate_profile_name(profile_name):
        emit('error', {'image': full_path, 'message': f'Invalid profile: {profile_name}'})
        return

    # Check for API key in this order:
    # 1. Environment variable (.env file)
    # 2. Settings passed from frontend (localStorage)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = data.get('settings', {}).get('apiKey')

    if not api_key:
        emit('error', {'image': full_path, 'message': 'No API key provided. Please set OPENAI_API_KEY in .env file or provide it in Settings.'})
        return

    # Security: Validate API key format (basic check)
    if not validate_api_key_format(api_key):
        emit('error', {'image': full_path, 'message': 'Invalid API key format. OpenAI keys should start with "sk-".'})
        return

    # Submit to thread pool with explicit API key
    processing_executor.submit(process_image_async, data, request.sid, profile_name, api_key)

def process_image_async(data, sid, profile_name, api_key):
    profile = PROFILES[profile_name]
    # Use file_path if available, otherwise reconstruct from full_path
    image_path = data.get('file_path')
    if not image_path:
        # Extract filename from the URL and construct proper path
        filename = os.path.basename(data['full_path'])
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Security: Validate file path is within upload folder (prevent path traversal)
    if not validate_file_path(image_path, app.config['UPLOAD_FOLDER']):
        with app.app_context():
            socketio.emit('error', {
                'image': data['full_path'],
                'message': 'Invalid file path'
            }, room=sid)
        return

    try:
        with app.app_context():
            print(f"\nAI processing started for {data['full_path']}", flush=True)
            socketio.emit('processing_start', {'image': data['full_path']}, room=sid)

            if not api_key:
                raise ValueError("No API key provided for OpenAI request")

            # Check cache first
            image_hash = get_image_hash(image_path)
            if image_hash:
                cached = get_cached_metadata(image_hash, profile_name)
                if cached:
                    print(f"Cache hit for {data['full_path']}", flush=True)
                    response_data = {
                        'image': data['full_path'],
                        'status': 'complete',
                        'cached': True,
                        'metadata': cached
                    }
                    socketio.emit('metadata_update', response_data, room=sid)
                    return

            # Encode image to base64
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize intelligently - maintain aspect ratio
                max_dimension = 1024
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Optimize for API transmission
                buffered = BytesIO()
                img.save(buffered, format='JPEG', quality=85, optimize=True, progressive=True)
                
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        with app.app_context():
            # Call OpenAI API using a custom httpx client to avoid httpx>=0.28 proxies incompatibility
            http_timeout = httpx.Timeout(60.0)
            # Do not pass deprecated 'proxies' arg; env vars will be respected by httpx automatically
            http_client = httpx.Client(timeout=http_timeout, follow_redirects=True)
            client = openai.OpenAI(api_key=api_key, http_client=http_client)
            # Use profile-specific configuration
            system_message = profile['prompt']
        # Only validate categories if the profile has them defined
        valid_categories = set(profile.get('categories', []))

        response = client.chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Generate metadata for this image following the provided rules"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )

        # Parse and validate response
        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from AI model")
            metadata = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")
        except (IndexError, AttributeError) as e:
            raise ValueError(f"Malformed response structure: {str(e)}")
            
        required_fields = profile['required_fields']
        missing_fields = [field for field in required_fields if field not in metadata or not metadata[field]]
        if missing_fields:
            raise ValueError(f"Missing required fields in AI response: {', '.join(missing_fields)}")
            
        # Only validate category if the profile has categories defined
        if valid_categories and 'category' in metadata:
            if metadata['category'] not in valid_categories:
                # Instead of raising an error, set category to "Other"
                metadata['category'] = "Other"

        print(f"AI processing completed for {data['full_path']}", flush=True)

        # Cache the successful response
        response_metadata = {k: metadata[k] for k in profile['required_fields']}
        if image_hash:
            cache_metadata(image_hash, profile_name, response_metadata)
            print(f"Cached metadata for {data['full_path']}", flush=True)

        try:
            print(f"Emitting metadata_update for {data['full_path']} to room {sid}", flush=True)
            # Profile-specific response formatting
            response_data = {
                'image': data['full_path'],
                'status': 'complete',
                'cached': False,
                'metadata': response_metadata
            }
            socketio.emit('metadata_update', response_data, room=sid)
            print("Metadata_update emission completed", flush=True)
        except Exception as e:
            print(f"Error emitting metadata_update: {str(e)}", flush=True)

    except Exception as e:
        try:
            print(f"Emitting error for {data['full_path']} to room {sid}", flush=True)
            # Use categorized error handling for better UX
            error_info = classify_error(e)
            socketio.emit('error', {
                'image': data['full_path'],
                **error_info
            }, room=sid)
            print(f"Error emission completed: {error_info['category']}", flush=True)
        except Exception as emit_err:
            print(f"Error emitting error event: {str(emit_err)}", flush=True)
    finally:
        try:
            if 'http_client' in locals():
                http_client.close()
        except Exception:
            pass


@socketio.on('disconnect')
def handle_disconnect():
    """Clean up rate limit tracking when client disconnects."""
    sid = request.sid
    if sid in socket_rate_limits:
        del socket_rate_limits[sid]


@app.route('/export', methods=['POST'])
@limiter.limit(config.export_rate_limit)
def export():
    """Export metadata to CSV with input validation."""
    metadata = request.json.get('data', [])
    profile_name = request.json.get('profile', 'zedge')
    base_path = request.json.get('base_path', '').strip()

    # Security: Validate profile name
    if not validate_profile_name(profile_name):
        return jsonify({'error': f'Invalid profile: {profile_name}'}), 400

    profile = PROFILES[profile_name]
    
    # Process metadata with optional base path
    processed_metadata = []
    for item in metadata:
        processed_item = {}
        for col in profile['csv_columns']:
            value = item.get(col, '')
            # If this is the full_path column and we have a base path, prepend it
            if col == 'full_path' and base_path:
                # Convert /static/images/file.jpg to base_path/file.jpg
                filename = os.path.basename(value)
                value = os.path.join(base_path, filename)
            processed_item[col] = value
        processed_metadata.append(processed_item)
    
    # Create DataFrame with processed metadata
    df = pd.DataFrame(processed_metadata)
    
    csv_path = f'metadata_{profile_name}.csv'
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)


# Health check endpoint for monitoring
from datetime import datetime
app_start_time = datetime.now()

@app.route('/health')
def health_check():
    """Health check endpoint for container/service monitoring."""
    try:
        uptime = (datetime.now() - app_start_time).total_seconds()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': round(uptime, 2),
            'version': '1.0.0',
            'checks': {
                'api_configured': bool(config.openai_api_key),
                'upload_dir_exists': os.path.isdir(app.config['UPLOAD_FOLDER']),
                'upload_dir_writable': os.access(app.config['UPLOAD_FOLDER'], os.W_OK),
                'profiles_loaded': len(PROFILES) > 0
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print(f"Starting MetaData Refiner server on {config.host}:{config.port}")
    socketio.run(app, host=config.host, port=config.port, debug=config.debug, allow_unsafe_werkzeug=True)
