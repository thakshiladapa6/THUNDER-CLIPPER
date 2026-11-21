@echo off
REM ===== THUNDER CLIPPER - builds THUNDER_CLIPPER.exe =====
REM 1) Install Python 3.10-3.12 (tick "Add to PATH")
REM 2) Put ffmpeg.exe and ffprobe.exe inside the "bin" folder (https://www.gyan.dev/ffmpeg/builds/ -> release essentials)
if not exist bin\ffmpeg.exe (echo Put ffmpeg.exe + ffprobe.exe in the bin folder first! & pause & exit /b 1)
py -m pip install -r requirements.txt
py make_logo.py
py -m PyInstaller --noconfirm --onefile --windowed --name THUNDER_CLIPPER --icon assets\icon.ico ^
  --add-data "assets;assets" --add-binary "bin\ffmpeg.exe;bin" --add-binary "bin\ffprobe.exe;bin" ^
  --collect-all customtkinter --collect-all yt_dlp --collect-all chat_downloader ^
  --collect-all faster_whisper --collect-all ctranslate2 --collect-all tokenizers --collect-all av app.py
echo.
echo DONE -> dist\THUNDER_CLIPPER.exe
pause
