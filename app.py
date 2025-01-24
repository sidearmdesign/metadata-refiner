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

# Load environment variables
load_dotenv()

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

@app.route('/upload', methods=['POST'])
def upload():
    images = request.files.getlist('images')
    image_data = []
    
    for image in images:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        image_data.append({
            'path': filepath,
            'filename': filename,
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
    processing_executor.submit(process_image_async, data, request.sid)

def process_image_async(data, sid):
    image_path = data['path']
    try:
        with app.app_context():
            print(f"\nAI processing started for {image_path}", flush=True)
            socketio.emit('processing_start', {'image': image_path}, room=sid)
        
        # Encode image to base64
        with Image.open(image_path) as img:
            buffered = BytesIO()
            img.save(buffered, format=img.format)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Call OpenAI API
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Single source of truth for valid categories
        valid_categories = {
            'Animals', 'Anime', 'Cars & Vehicles', 'Comics', 'Designs',
            'Drawings', 'Entertainment', 'Funny', 'Games', 'Holidays',
            'Love', 'Music', 'Nature', 'Other', 'Patterns', 'People',
            'Sayings', 'Space', 'Spiritual', 'Sports', 'Technology'
        }
        
        # Build validation-aware prompt using the categories
        category_list = '\n'.join(f'- {cat}' for cat in sorted(valid_categories))
        system_message = f"""You MUST follow these rules:
1. Category MUST be exactly one of:
{category_list}
2. Title: 30-60 chars, no filler words/punctuation
3. Description: 100-150 SEO-optimized chars
4. Tags: 10 comma-separated single words"""

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
                        {"type": "text", "text": data.get('prompt', """CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. CATEGORY MUST BE FROM THIS EXACT LIST (NO variations/additions):
   - Animals
   - Anime
   - Cars & Vehicles
   - Comics
   - Designs
   - Drawings
   - Entertainment
   - Funny
   - Games
   - Holidays
   - Love
   - Music
   - Nature
   - Other
   - Patterns
   - People
   - Sayings
   - Space
   - Spiritual
   - Sports
   - Technology

OTHER RULES:

**TITLE RULES**
- 30-60 characters
- Descriptive and creative
- NO filler words (with/of/from/in/on/at)
- NO punctuation

**TAGS RULES** 
- Exactly 10 single-word tags
- Specific and relevant to image content
- Separated by commas

**DESCRIPTION RULES**
- 100-150 characters
- SEO-optimized
- Descriptive narrative

**CATEGORY RULES**
- MUST CHOOSE ONE FROM THIS EXACT LIST:
  Animals, Anime, Cars & Vehicles, Comics, Designs, 
  Drawings, Entertainment, Funny, Games, Holidays,
  Love, Music, Nature, Other, Patterns, People,
  Sayings, Space, Spiritual, Sports, Technology

RETURN JSON FORMAT:
{
  "title": "...",
  "description": "...",
  "tags": "tag1,tag2,...,tag10",
  "category": "EXACT_CATEGORY_FROM_LIST"
}""")},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{img.format};base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )

        # Parse and validate response
        metadata = json.loads(response.choices[0].message.content)
        required_fields = ['title', 'description', 'tags', 'category']
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
            socketio.emit('metadata_update', {
                'image': image_path,
                'metadata': metadata,
                'status': 'complete'
            }, room=sid)
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
    metadata = request.json
    df = pd.DataFrame(metadata)
    csv_path = 'metadata.csv'
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
