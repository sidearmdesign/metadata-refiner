from flask import Flask, render_template, request, jsonify, send_file
import json
from flask_socketio import SocketIO, emit
import os
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

# Configure Flask and SocketIO with async support
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app, 
                  cors_allowed_origins="*",
                  async_mode='threading',
                  max_http_buffer_size=100 * 1024 * 1024)  # 100MB max for base64 images
app.config['UPLOAD_FOLDER'] = 'static/images/'

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
    images = request.files.getlist('images')
    image_data = []
    
    for image in images:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        image_data.append({
            'full_path': filepath,
            'title': '',
            'description': '',
            'tags': '',
            'category': ''
        })

    return jsonify({'images': image_data})

from concurrent.futures import ThreadPoolExecutor
processing_executor = ThreadPoolExecutor(max_workers=4)

@socketio.on('generate_metadata')
def handle_generate_metadata(data):
    # Submit to thread pool and return immediately
    processing_executor.submit(process_image_async, data, request.sid, data.get('profile', 'zedge'))

def process_image_async(data, sid, profile_name):
    profile = PROFILES[profile_name]
    image_path = data['full_path']
    try:
        with app.app_context():
            print(f"\nAI processing started for {image_path}", flush=True)
            socketio.emit('processing_start', {'image': image_path}, room=sid)
        
        # Encode image to base64
            with Image.open(image_path) as img:
                # Resize and optimize image before sending to API
                img.thumbnail((1024, 1024))
                
                buffered = BytesIO()
                img.save(buffered, format='JPEG', quality=85, optimize=True)
                
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Call OpenAI API
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Use profile-specific configuration
        system_message = profile['prompt']
        valid_categories = set(profile['categories'])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        metadata = json.loads(response.choices[0].message.content)
        required_fields = profile['required_fields']
        if not all(field in metadata for field in required_fields):
            raise ValueError("Missing required fields in AI response")
            
        if metadata['category'] not in valid_categories:
            raise ValueError(
                f"Invalid category: {metadata['category']}. Must be one of: \n" +
                "\n".join(f"- {cat}" for cat in sorted(valid_categories))
            )

        print(f"AI processing completed for {image_path}", flush=True)
        try:
            print(f"Emitting metadata_update for {image_path} to room {sid}", flush=True)
            # Profile-specific response formatting
            response_data = {
                'image': image_path,
                'status': 'complete',
                'metadata': {k: metadata[k] for k in profile['required_fields']}
            }
            socketio.emit('metadata_update', response_data, room=sid)
            print("Metadata_update emission completed", flush=True)
        except Exception as e:
            print(f"Error emitting metadata_update: {str(e)}", flush=True)

    except Exception as e:
        try:
            print(f"Emitting error for {image_path} to room {sid}", flush=True)
            socketio.emit('error', {
                'image': image_path,
                'message': f"Metadata generation failed: {str(e)}"
            }, room=sid)
            print("Error emission completed", flush=True)
        except Exception as e:
            print(f"Error emitting error event: {str(e)}", flush=True)

@app.route('/export', methods=['POST'])
def export():
    metadata = request.json.get('data', [])
    profile_name = request.json.get('profile', 'zedge')
    profile = PROFILES[profile_name]
    
    # Map data to profile-specific CSV columns
    df = pd.DataFrame([{
        col: item.get(col, '')  # Match exact case from profile requirements
        for col in profile['csv_columns']
    } for item in metadata])
    
    csv_path = f'metadata_{profile_name}.csv'
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
