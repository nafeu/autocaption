import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import webvtt


def create_title_header(
    text,
    video_width,
    top=300,
    background_color="black",
    font="/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    font_size=64,
    text_color="#F8EFBA",
    padding=20,
):
    text_clip = TextClip(
        bg_color=background_color,
        color=text_color,
        font=font,
        font_size=font_size,
        interline=int(video_width * 0.00740),
        text_align="center",
        method="caption",
        size=(video_width - int(video_width * 0.2), None),
        text=text
    )

    text_width, text_height = text_clip.size
    box_width = text_width + 2 * padding
    box_height = text_height + 3 * padding

    background_clip = TextClip(
        font=font,
        text=" ",
        size=(box_width, box_height),
        bg_color=background_color,
    )

    title_clip = CompositeVideoClip(
        [background_clip, text_clip.with_position(("center", "center"))],
        size=(box_width, box_height),
    )

    return title_clip.with_position(("center", top))


def overlay_captions(
    video_path="input_video.mp4", output_video="output_video.mp4", title_text=""
):
    video = VideoFileClip(video_path)
    video_width, video_height = video.size

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    vtt_file_path = f"./{video_name}.vtt"

    captions = []
    text_clips = []

    text_clip_defaults = {
        "method": "label",
    }

    text_clip_caption_params = {
        "color": "white",
        "font": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "font_size": int(video_width * 0.07777),
        "stroke_color": "black",
        "stroke_width": int(video_width * 0.00462),
        "size": (video_width, int(video_height * 0.26)),
    }

    text_clip_caption_additional_configs = {"top": int(video_height * 0.365)}

    text_clip_title_header_params = {
        "font_size": int(video_width * 0.05925),
        "text": title_text,
        "top": int(video_height * 0.156),
        "video_width": video_width,
        "padding": int(video_width * 0.01851)
    }

    text_clip_title_header_additional_configs = {"duration": 5}

    for caption in webvtt.read(vtt_file_path):
        captions.append(
            {
                "start": time_to_seconds(caption.start),
                "end": time_to_seconds(caption.end),
                "text": caption.text.strip(),
            }
        )

    for caption in captions:
        text_clip = (
            TextClip(
                **text_clip_defaults, **text_clip_caption_params, text=caption["text"]
            )
            .with_duration(caption["end"] - caption["start"])
            .with_position(("center", text_clip_caption_additional_configs["top"]))
            .with_start(caption["start"])
        )
        text_clips.append(text_clip)

    final_video = None

    if len(title_text) > 0:
        title_header = create_title_header(**text_clip_title_header_params).with_duration(
            text_clip_title_header_additional_configs["duration"]
        )
        final_video = CompositeVideoClip([video, *text_clips, title_header])
    else:
        final_video = CompositeVideoClip([video, *text_clips])

    final_video.write_videofile(output_video, codec="libx264", audio_codec="aac")

    print(f"Video with captions saved to {output_video}")


def time_to_seconds(timestamp):
    parts = timestamp.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + float(f"0.{ms}")
