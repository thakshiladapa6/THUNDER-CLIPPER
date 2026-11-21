<p align="center"><img src="assets/logo.png" width="140"></p>

# ⚡ THUNDER CLIPPER
Turn any stream or video link into viral portrait clips (1080×1920) with captions.
**Contributors: THAKSHIL & JISSHU**

## Features
- Paste a Twitch / YouTube / Kick link (VOD or live recording)
- Select the streamer **face cam** and the **game** area, auto portrait layout
- Finds **Hyped / Funny / Serious** moments from **chat + streamer voice**
- Reference video link (Instagram / YouTube) sets clip length & FPS
- Caption styles: Hormozi, Pop, Karaoke, Neon, Classic, Minimal

## Download the .exe
Go to **Actions → Build THUNDER CLIPPER exe → latest run → Artifacts → THUNDER_CLIPPER_exe**.
Or push a tag (`git tag v1.0 && git push --tags`) to get it under **Releases**.

## Run from source
```
pip install -r requirements.txt
python app.py
```
(ffmpeg + ffprobe must be in `bin/` or on PATH.)
