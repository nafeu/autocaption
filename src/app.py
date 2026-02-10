import os
import socket
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from generate_captions import generate_captions
from overlay_captions import overlay_captions
from transcript_edit import (
    load_transcript,
    get_transcript_path,
    compute_cut_ranges,
    render_video_with_cuts,
)
from trim_video import get_video_duration, trim_video

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_video():
    """Upload a video only (no processing). Used in Trim stage."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(video_path)
    return jsonify({"filename": filename})


@app.route("/preview/<filename>")
def preview_video(filename):
    """Serve uploaded video for preview (Trim stage)."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, mimetype="video/mp4")


@app.route("/video_info/<filename>")
def video_info(filename):
    """Return duration (seconds) for an uploaded video."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    try:
        duration = get_video_duration(path)
        return jsonify({"duration": duration})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/trim/<filename>", methods=["POST"])
def trim_video_route(filename):
    """Trim video to [start_seconds, end_seconds]. Writes to uploads/{base}_trimmed.mp4."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    payload = request.get_json() or {}
    start_s = float(payload.get("start_seconds", 0))
    end_s = float(payload.get("end_seconds", 0))
    try:
        duration = get_video_duration(path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    start_s = max(0, min(start_s, duration - 0.01))
    end_s = max(start_s + 0.01, min(end_s, duration))
    base, ext = os.path.splitext(filename)
    trimmed_name = f"{base}_trimmed{ext}"
    out_path = os.path.join(app.config["UPLOAD_FOLDER"], trimmed_name)
    try:
        trim_video(path, out_path, start_s, end_s)
        return jsonify({"trimmed_filename": trimmed_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/process_existing/<filename>", methods=["POST"])
def process_existing_video(filename):
    """Run caption generation + overlay on an already-uploaded file (e.g. after Trim)."""
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(video_path):
        return jsonify({"error": "File not found"}), 404
    output_filename = f"processed_{filename}"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)
    try:
        generate_captions(video_path)
        overlay_captions(video_path, output_path)
        return jsonify(
            {"message": "Video processed successfully", "output_file": output_filename}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/process", methods=["POST"])
def process_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(video_path)

    output_filename = f"processed_{filename}"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)

    try:
        generate_captions(video_path)
        overlay_captions(video_path, output_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(
        {"message": "Video processed successfully", "output_file": output_filename}
    )


@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(app.config["PROCESSED_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True)


@app.route("/download_vtt/<filename>")
def download_vtt(filename):
    path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{os.path.splitext(filename)[0]}.vtt"
    )
    if not os.path.exists(path):
        return jsonify({"error": "VTT file not found"}), 404
    return send_file(path, as_attachment=True, mimetype="text/vtt")


@app.route("/get_vtt/<filename>")
def get_vtt(filename):
    vtt_file = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{os.path.splitext(filename)[0]}.vtt"
    )
    if os.path.exists(vtt_file):
        with open(vtt_file, "r", encoding="utf-8") as file:
            return jsonify({"vtt_content": file.read()})
    else:
        return jsonify({"error": "VTT file not found"}), 404


@app.route("/save_vtt/<filename>", methods=["POST"])
def save_vtt(filename):
    vtt_file = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{os.path.splitext(filename)[0]}.vtt"
    )
    vtt_content = request.json.get("vtt_content", "")

    try:
        with open(vtt_file, "w", encoding="utf-8") as file:
            file.write(vtt_content)
        return jsonify({"message": "VTT file updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reprocess/<filename>", methods=["POST"])
def reprocess_video(filename):
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    output_filename = f"processed_{filename}"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)

    try:
        overlay_captions(video_path, output_path)
        return jsonify(
            {
                "message": "Video re-processed successfully",
                "output_file": output_filename,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_transcript/<filename>")
def get_transcript(filename):
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    transcript_path = get_transcript_path(video_path)
    if not os.path.exists(transcript_path):
        return jsonify({"error": "Transcript not found. Process the video first."}), 404
    try:
        data = load_transcript(transcript_path)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reprocess_edited/<filename>", methods=["POST"])
def reprocess_edited(filename):
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    transcript_path = get_transcript_path(video_path)
    if not os.path.exists(transcript_path):
        return jsonify({"error": "Transcript not found. Process the video first."}), 404

    payload = request.get_json() or {}
    deleted_ids = payload.get("deleted_ids", [])
    if not isinstance(deleted_ids, list):
        return jsonify({"error": "deleted_ids must be a list"}), 400

    try:
        data = load_transcript(transcript_path)
        segments = data.get("segments", [])
        cut_ranges = compute_cut_ranges(segments, deleted_ids)
        output_filename = f"edited_{filename}"
        final_output_path = os.path.join(
            app.config["PROCESSED_FOLDER"], output_filename
        )

        if not cut_ranges:
            # No deletions: output full captioned video (same as reprocess)
            overlay_captions(video_path, final_output_path)
            return jsonify(
                {
                    "message": "Video re-rendered (full video with captions)",
                    "output_file": output_filename,
                    "cut_ranges": [],
                }
            )

        base, _ = os.path.splitext(filename)
        captioned_temp_filename = f"edited_{base}_captioned.mp4"
        captioned_temp_path = os.path.join(
            app.config["PROCESSED_FOLDER"], captioned_temp_filename
        )

        # 1) Apply captions (with highlights) to the original video — same as reprocess
        overlay_captions(video_path, captioned_temp_path)

        # 2) Cut the captioned video by removing deleted segments (last step)
        render_video_with_cuts(captioned_temp_path, final_output_path, cut_ranges)

        try:
            os.remove(captioned_temp_path)
        except OSError:
            pass

        return jsonify(
            {
                "message": "Video re-rendered with captions and cuts applied",
                "output_file": output_filename,
                "cut_ranges": cut_ranges,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def find_free_port(start=5000, end=5010):
    """Return the first port in [start, end) that is not in use."""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return start  # fallback


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0)) or find_free_port()
    url = f"http://localhost:{port}"
    print(f" * Running at {url}")
    app.run(debug=True, host="0.0.0.0", port=port)
