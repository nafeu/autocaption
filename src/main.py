import argparse
from generate_captions import generate_captions
from overlay_captions import overlay_captions


def main():
    parser = argparse.ArgumentParser(
        description="Short Video Auto-Caption Script | github.com/nafeu/autocaption"
    )
    parser.add_argument("video", help="Path to the input video file")
    parser.add_argument(
        "--output-video", default="output_video.mp4", help="Output video with captions"
    )
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Transcribe the video and generate captions",
    )
    parser.add_argument(
        "--overlay", action="store_true", help="Overlay captions onto the video"
    )
    parser.add_argument("--title", default="", help="Title header text")

    args = parser.parse_args()

    if not args.transcribe and not args.overlay:
        generate_captions(args.video)
        overlay_captions(args.video, args.output_video, args.title)
    else:
        if args.transcribe:
            print("Running transcription...")
            generate_captions(args.video)
        if args.overlay:
            print("Overlaying captions...")
            overlay_captions(args.video, args.output_video, args.title)


if __name__ == "__main__":
    main()
