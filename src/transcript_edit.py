"""
Text-based video edit model: compute cut ranges from deleted segment IDs,
and re-render video by removing those ranges.
"""
import json
import os
from moviepy import VideoFileClip, concatenate_videoclips


def load_transcript(transcript_path):
    with open(transcript_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_transcript_path(video_path):
    base, _ = os.path.splitext(video_path)
    return f"{base}_transcript.json"


def compute_cut_ranges(segments, deleted_ids):
    """
    Given the list of segments (each with id, start, end) and a set of
    deleted segment IDs, return a list of (start, end) ranges to remove
    from the video. Overlapping or adjacent ranges are merged so we do
    one contiguous cut per region.
    """
    deleted_set = set(deleted_ids)
    to_remove = []
    for seg in segments:
        if seg["id"] in deleted_set:
            to_remove.append((seg["start"], seg["end"]))

    if not to_remove:
        return []

    to_remove.sort(key=lambda r: r[0])
    merged = [list(to_remove[0])]
    for start, end in to_remove[1:]:
        if start <= merged[-1][1] + 0.001:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return [tuple(r) for r in merged]


def ranges_to_keep(cut_ranges, duration):
    """
    Invert cut ranges into keep ranges: [(0, duration)] minus cut_ranges.
    """
    if not cut_ranges:
        return [(0.0, duration)]

    keep = []
    t = 0.0
    for start, end in sorted(cut_ranges, key=lambda r: r[0]):
        if start > t + 0.001:
            keep.append((t, start))
        t = max(t, end)
    if t < duration - 0.001:
        keep.append((t, duration))
    return keep


def render_video_with_cuts(video_path, output_path, cut_ranges):
    """
    Write a new video that has the given ranges removed (audio and video).
    Keep the source clip open until we finish writing, so subclips stay valid.
    """
    full = VideoFileClip(video_path)
    try:
        duration = float(full.duration)
        keep = ranges_to_keep(cut_ranges, duration)
        if not keep:
            raise ValueError("All video would be cut; nothing to keep")

        clips = [full.subclipped(start, end) for start, end in keep]
        concat = concatenate_videoclips(clips)
        try:
            concat.write_videofile(output_path, codec="libx264", audio_codec="aac")
        finally:
            concat.close()
            for c in clips:
                c.close()
    finally:
        full.close()
    return output_path
