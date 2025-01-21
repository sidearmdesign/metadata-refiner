# Instructions for Cline AI Coding Assistant

## Web App Features

### General Overview
The web app will allow users to manage metadata for a collection of images. Key features include:

- Drag-and-drop functionality for images or selection of a folder of images.
- Display each image on the page with associated editable metadata fields.
- AI-powered metadata generation for each image.
- Export functionality for the metadata as a CSV file.

---

### Required Features

#### **1. Input Handling**
- **Drag-and-drop images**: Users can drag individual or multiple images onto the app.
- **Folder selection**: Users can select an entire folder of images.
- Accepted formats: `.jpg`, `.png`, `.jpeg`, `.gif`.

#### **2. Display**
- Display all uploaded images on the page.
- For each image, show:
  - Path-to-image
  - File name
  - Title (editable text field)
  - Description (editable text field)
  - Tags (editable text field)
  - Category (editable dropdown field or text field).

#### **3. AI Integration**
- **AI Model**: Use `gpt4o-mini` to analyze images and generate metadata.
- Functionality:
  - A button for each image to generate or regenerate metadata using AI.
  - A button to generate metadata for all images at once.

#### **4. Export**
- Export all metadata fields as a single CSV file.

---

## Implementation Steps

### **Frontend**
#### Libraries:
- Use `Flask` for backend API.
- Use `Flask-SocketIO` for real-time communication.
- Use HTML5/JavaScript for the user interface.
- Use libraries like `Dropzone.js` for drag-and-drop functionality.
- Use Bootstrap for a responsive and clean UI.

### **Backend**
#### Libraries:
- Use `Flask` for handling requests.
- Use `Pillow` for image handling.
- Use `OpenAI API` to connect to `gpt4o-mini`.
- Use `pandas` for CSV creation.

### **Database** (Optional)
Use an in-memory store like `SQLite` to temporarily store image metadata.

---

## Code Outline

### **Backend Code (Python)**
#### Modules:
- `Flask`
- `Pillow`
- `OpenAI API`
- `pandas`
- `os`

#### File Structure:
```plaintext
project/
├── app.py
├── static/
│   ├── images/
│   └── js/
├── templates/
│   ├── index.html
└── requirements.txt
```

#### Sample Code:
```python
from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd
import openai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/'

# Route: Home
@app.route('/')
def index():
    return render_template('index.html')

# Route: Upload Images
@app.route('/upload', methods=['POST'])
def upload():
    images = request.files.getlist('images')
    image_data = []
    
    for image in images:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Add metadata for UI display
        image_data.append({
            'path': filepath,
            'filename': filename,
            'title': '',
            'description': '',
            'tags': '',
            'category': ''
        })

    return jsonify({'images': image_data})

# Route: Generate Metadata
@app.route('/generate-metadata', methods=['POST'])
def generate_metadata():
    data = request.json
    image_path = data['path']

    # Placeholder AI function
    ai_response = {
        'title': 'Generated Title',
        'description': 'Generated Description',
        'tags': 'tag1, tag2, tag3',
        'category': 'Generated Category'
    }

    return jsonify(ai_response)

# Route: Export Metadata to CSV
@app.route('/export', methods=['POST'])
def export():
    metadata = request.json
    df = pd.DataFrame(metadata)
    csv_path = 'metadata.csv'
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
```

### **Frontend Code (HTML/JS)**
#### Components:
- Drag-and-drop UI.
- Metadata fields for each image.
- Buttons for AI generation and CSV export.

#### Example Snippet:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image Metadata Manager</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap/dist/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h1>Image Metadata Manager</h1>
        <form id="upload-form">
            <input type="file" id="image-input" multiple>
            <button type="submit">Upload</button>
        </form>

        <div id="image-container">
            <!-- Images will be displayed here -->
        </div>

        <button id="generate-all">Generate Metadata for All</button>
        <button id="export">Export to CSV</button>
    </div>

    <script>
        // JavaScript for handling uploads and generating metadata
    </script>
</body>
</html>
