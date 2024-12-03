import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from generate_captions import generate_captions
from overlay_captions import overlay_captions

# Get the directory of this script
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configure upload and processed folders relative to the script's location
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')

# Create the folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    # Get the uploaded video
    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the video to the upload folder
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(video_path)

    # Define the output path for the processed video
    output_filename = f"processed_{filename}"
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

    # Process the video
    try:
        # Replace with your actual processing logic
        generate_captions(video_path)
        overlay_captions(video_path, output_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Video processed successfully', 'output_file': output_filename})

@app.route('/download/<filename>')
def download_file(filename):
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/get_vtt/<filename>')
def get_vtt(filename):
    """
    Returns the content of the generated .vtt file for editing.
    """
    vtt_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.vtt")
    if os.path.exists(vtt_file):
        with open(vtt_file, 'r', encoding='utf-8') as file:
            return jsonify({"vtt_content": file.read()})
    else:
        return jsonify({'error': 'VTT file not found'}), 404

@app.route('/save_vtt/<filename>', methods=['POST'])
def save_vtt(filename):
    """
    Saves the updated content of the .vtt file.
    """
    vtt_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.vtt")
    vtt_content = request.json.get('vtt_content', '')

    try:
        with open(vtt_file, 'w', encoding='utf-8') as file:
            file.write(vtt_content)
        return jsonify({'message': 'VTT file updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reprocess/<filename>', methods=['POST'])
def reprocess_video(filename):
    """
    Re-runs the overlay_captions function with the updated VTT file.
    """
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_filename = f"processed_{filename}"
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

    try:
        overlay_captions(video_path, output_path)  # Re-run overlay_captions
        return jsonify({'message': 'Video re-processed successfully', 'output_file': output_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
