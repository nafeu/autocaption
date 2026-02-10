"""
Trim a video to a start and end time (in seconds). Used for the Trim stage.
"""
from moviepy import VideoFileClip


def get_video_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return float(clip.duration)


def trim_video(video_path, output_path, start_seconds, end_seconds):
    """
    Write a new video containing only the segment from start_seconds to end_seconds.
    """
    with VideoFileClip(video_path) as clip:
        sub = clip.subclipped(start_seconds, end_seconds)
        sub.write_videofile(output_path, codec="libx264", audio_codec="aac")
        sub.close()
    return output_path
