import os
import whisper
from whisper.utils import get_writer


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

    print(f"VTT file saved as: {vtt_file_path}")
