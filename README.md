# autocaption

A text-based video editor that generates captions from speech and lets you edit the video by editing the transcript. Trim your clip, then caption it with word-level timestamps—remove words or filler (um, uh, hmm) and re-render so those segments are cut from the final video.

![autocaption — Trim stage](docs/screenshots/trim-stage.png)
<!-- TODO: Add screenshot of the Trim stage -->

![autocaption — Caption stage](docs/screenshots/caption-stage.png)
<!-- TODO: Add screenshot of the Caption stage -->

## Features

- **Trim stage**: Upload any video, optionally trim with a visual timeline (draggable in/out handles and thumbnail previews). Playback stays in sync with the trim range.
- **Caption stage**: [OpenAI Whisper](https://github.com/openai/whisper) transcribes the video with word-level timestamps. A word-level transcript is built (words plus silence segments as “…”) and saved for editing.
- **Text-based editing**: Click any word or silence in the transcript to mark it for removal. Use “Select filler words” to auto-mark common fillers (um, uh, ah, hmm, etc.). Re-render to produce a new video with those segments cut out.
- **Captions on output**: Captions (with per-word highlight) are overlaid using the original VTT; trimming is applied last so the final video has correct captions and no removed content.
- **Download**: Save the current captioned/edited video to a chosen location (Save As dialog where supported, otherwise browser download).

## How it works

1. **Trim** (optional): Upload a video → optional trim via timeline handles → continue to Caption.
2. **Caption**: The app runs Whisper on the (possibly trimmed) video, generates a VTT and a word-level JSON transcript. Captions are overlaid with MoviePy and shown in the UI.
3. **Edit**: You see the transcript as clickable chips. Click to mark segments for removal; “Select filler words” marks common fillers. “Re-render video” cuts those segments from the captioned video (captions are applied first, then cuts) and updates the preview.
4. **Download**: Use “Download Video” to save the current result (with Save As where the browser supports it).

Backend: Flask. Trimming and cutting: MoviePy. Transcription: OpenAI Whisper. Caption overlay: MoviePy TextClips.

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) on your PATH (used by MoviePy and Whisper)
- Enough disk space and RAM for Whisper (model and inference)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/nafeu/autocaption.git
cd autocaption
```

### 2. Create and activate a virtual environment

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, MoviePy, and [OpenAI Whisper](https://github.com/openai/whisper) (`openai-whisper` on PyPI). Whisper depends on PyTorch; the first run may download a small language model (e.g. `base`).

**If `import whisper` fails** (e.g. missing PyTorch or CUDA):

- Ensure you have a supported Python version and enough memory.
- On GPU systems you can install a CUDA-enabled PyTorch first, then `pip install -r requirements.txt`. See [Whisper’s README](https://github.com/openai/whisper#setup) and [PyTorch Get Started](https://pytorch.org/get-started/locally/) for details.

### 4. Run the app

**Option A — Launch script (activates venv, starts server, opens browser):**

**macOS / Linux:**

```bash
./run.sh
```

(If needed: `chmod +x run.sh`)

**Windows:** Run the server and open the URL yourself (see Option B), or use WSL and run `./run.sh` there.

**Option B — Manual:**

```bash
source venv/bin/activate   # or venv\Scripts\activate on Windows
cd src
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser. Use [http://127.0.0.1:5000](http://127.0.0.1:5000) if your browser blocks `localhost`.

## Usage

1. **Trim**: Drop a video on the Trim stage (or click to browse). Use the timeline under the video to set start/end; drag the handles and use “Apply trim” if you want to clip. Click “Continue to Caption” (or the Caption tab).
2. **Caption**: The app transcribes and overlays captions. When done, you’ll see the video and the word-level transcript.
3. **Edit**: Click words or “…” (silence) to mark them for removal (they’ll appear struck through). Use “Select filler words” to mark common fillers, then “Re-render video” to apply cuts. You can clear marks and re-render again.
4. **Download**: Use “Download Video” in the Caption stage to save the current video (Save As where supported).

## Project structure

```
autocaption/
├── README.md
├── requirements.txt
├── run.sh              # Launch script (venv + server + browser)
├── src/
│   ├── app.py          # Flask app and routes
│   ├── generate_captions.py  # Whisper transcription + VTT + word-level transcript
│   ├── overlay_captions.py   # VTT parsing + caption overlay (MoviePy)
│   ├── transcript_edit.py   # Cut-range logic + video cutting
│   ├── trim_video.py        # Trim to start/end (MoviePy)
│   └── templates/
│       └── index.html  # Single-page UI (Trim + Caption stages)
├── docs/
│   └── screenshots/    # Place screenshots here (see README placeholders)
└── ...
```

## Screenshots

Add your screenshots under `docs/screenshots/` and reference them in this section, for example:

| Trim stage | Caption stage |
|------------|---------------|
| ![Trim](docs/screenshots/trim-stage.png) | ![Caption](docs/screenshots/caption-stage.png) |

<!-- TODO: Add your screenshots to docs/screenshots/ and update the paths above if needed -->

## License

See [LICENSE](LICENSE).

## Links

- **Community**: [Discord](https://discord.gg/d9M9CQhhmS)
