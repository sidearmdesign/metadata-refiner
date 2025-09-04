from flask import Flask, render_template, request, jsonify, send_file, g, url_for
import json
from flask_socketio import SocketIO, emit
import os
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd
import openai
from dotenv import load_dotenv
import base64
from io import BytesIO

# Load environment variables and profiles
load_dotenv()
with open('profiles.json') as f:
    PROFILES = json.load(f)['profiles']

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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  async_mode='threading',
                  max_http_buffer_size=100 * 1024 * 1024)  # 100MB max for base64 images
# Use absolute path for upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images/')

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

@app.route('/upload', methods=['POST'])
def upload():
    try:
        images = request.files.getlist('images')
        if not images or all(img.filename == '' for img in images):
            return jsonify({'error': 'No files selected'}), 400
        
        image_data = []
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
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
                
            # Check file size (10MB limit)
            image.seek(0, os.SEEK_END)
            file_size = image.tell()
            image.seek(0)
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
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
    # Check for API key in this order:
    # 1. Environment variable (.env file)
    # 2. Settings passed from frontend (localStorage)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = data.get('settings', {}).get('apiKey')
    
    if not api_key:
        emit('error', {'image': data['full_path'], 'message': 'No API key provided. Please set OPENAI_API_KEY in .env file or provide it in Settings.'})
        return
    
    # Submit to thread pool with explicit API key
    processing_executor.submit(process_image_async, data, request.sid, data.get('profile', 'zedge'), api_key)

def process_image_async(data, sid, profile_name, api_key):
    profile = PROFILES[profile_name]
    # Use file_path if available, otherwise reconstruct from full_path
    image_path = data.get('file_path')
    if not image_path:
        # Extract filename from the URL and construct proper path
        filename = os.path.basename(data['full_path'])
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        with app.app_context():
            print(f"\nAI processing started for {data['full_path']}", flush=True)
            socketio.emit('processing_start', {'image': data['full_path']}, room=sid)
            
            if not api_key:
                raise ValueError("No API key provided for OpenAI request")

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
            # Call OpenAI API
            client = openai.OpenAI(api_key=api_key)
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
        try:
            print(f"Emitting metadata_update for {data['full_path']} to room {sid}", flush=True)
            # Profile-specific response formatting
            response_data = {
                'image': data['full_path'],
                'status': 'complete',
                'metadata': {k: metadata[k] for k in profile['required_fields']}
            }
            socketio.emit('metadata_update', response_data, room=sid)
            print("Metadata_update emission completed", flush=True)
        except Exception as e:
            print(f"Error emitting metadata_update: {str(e)}", flush=True)

    except Exception as e:
        try:
            print(f"Emitting error for {data['full_path']} to room {sid}", flush=True)
            socketio.emit('error', {
                'image': data['full_path'],
                'message': f"Metadata generation failed: {str(e)}"
            }, room=sid)
            print("Error emission completed", flush=True)
        except Exception as e:
            print(f"Error emitting error event: {str(e)}", flush=True)

@app.route('/export', methods=['POST'])
def export():
    metadata = request.json.get('data', [])
    profile_name = request.json.get('profile', 'zedge')
    base_path = request.json.get('base_path', '').strip()
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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
