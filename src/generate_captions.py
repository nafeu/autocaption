import json
import os
import whisper
from whisper.utils import get_writer
from moviepy import VideoFileClip


def get_video_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return float(clip.duration)


def build_edit_transcript(result, video_duration):
    """
    Build a linear list of segments: words (with start/end) and silences ("...").
    Each segment has id, type ('word' | 'silence'), text, start, end.
    Silences fill gaps from 0 to first word, between words, and from last word to end.
    """
    segments = []
    seg_id = 0
    last_end = 0.0

    for seg in result.get("segments", []):
        words = seg.get("words") or []
        if not words:
            # Segment has no word-level data; treat whole segment as one "word"
            start = float(seg["start"])
            end = float(seg["end"])
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            if start > last_end + 0.01:
                segments.append({
                    "id": seg_id,
                    "type": "silence",
                    "text": "...",
                    "start": round(last_end, 3),
                    "end": round(start, 3),
                })
                seg_id += 1
            segments.append({
                "id": seg_id,
                "type": "word",
                "text": text,
                "start": round(start, 3),
                "end": round(end, 3),
            })
            seg_id += 1
            last_end = end
            continue

        for w in words:
            start = float(w["start"])
            end = float(w["end"])
            text = (w.get("word") or "").strip()
            if start > last_end + 0.01:
                segments.append({
                    "id": seg_id,
                    "type": "silence",
                    "text": "...",
                    "start": round(last_end, 3),
                    "end": round(start, 3),
                })
                seg_id += 1
            segments.append({
                "id": seg_id,
                "type": "word",
                "text": text,
                "start": round(start, 3),
                "end": round(end, 3),
            })
            seg_id += 1
            last_end = end

    if video_duration > last_end + 0.01:
        segments.append({
            "id": seg_id,
            "type": "silence",
            "text": "...",
            "start": round(last_end, 3),
            "end": round(video_duration, 3),
        })

    return segments


def generate_captions(video_path="input_video.mp4"):
    model = whisper.load_model("base")
    result = model.transcribe(video_path, word_timestamps=True)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    uploads_folder = os.path.join(os.path.dirname(__file__), "uploads")

    os.makedirs(uploads_folder, exist_ok=True)

    vtt_file_path = os.path.join(uploads_folder, f"{video_name}.vtt")

    word_options = {"highlight_words": True, "max_line_count": 1, "max_line_width": 20}

    vtt_writer = get_writer(output_format="vtt", output_dir=uploads_folder)
    vtt_writer(result, vtt_file_path, word_options)

    # Build and save word-level edit transcript (words + silences)
    video_duration = get_video_duration(video_path)
    edit_transcript = build_edit_transcript(result, video_duration)
    transcript_path = os.path.join(uploads_folder, f"{video_name}_transcript.json")
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump({"segments": edit_transcript, "duration": video_duration}, f, indent=2)

    print(f"VTT file saved as: {vtt_file_path}")
    print(f"Edit transcript saved as: {transcript_path}")
