THUNDER CLIPPER  -  by THAKSHIL & JISSHU

RUN FROM SOURCE:  py -m pip install -r requirements.txt  &  py app.py   (ffmpeg must be in bin\ or PATH)
BUILD THE .EXE :  double-click build_exe.bat  ->  dist\THUNDER_CLIPPER.exe

HOW TO USE
1. Paste stream/VOD link (Twitch, YouTube, Kick, etc.). Optional: paste an Instagram/YouTube reference link.
2. Pick Moment (Hyped / Funny / Serious / Auto), Detect-from, Layout, Caption style.
3. Step 1: fetch video, then drag boxes on the FACE CAM and the GAME (Enter to confirm).
4. Step 2: START CLIPPING -> 1080x1920 clips with captions in the output folder.

NOTES
- Chat is read from VODs / replays (Twitch, YouTube). If chat can't be read, it falls back to voice analysis.
- Reference video sets clip length and FPS. Captions use Whisper (model downloads on first use, needs internet).
- Live streams: set "max minutes to grab" so the recording stops.
