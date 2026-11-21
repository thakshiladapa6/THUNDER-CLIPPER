"""THUNDER CLIPPER engine: download -> analyse (chat + voice) -> pick moments -> render portrait clips."""
import os, re, sys, glob, json, shutil, subprocess
import numpy as np
from captions import build_ass

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
NOWIN = 0x08000000 if os.name == "nt" else 0

HYPE = r"(pog+|poggers|pogchamp|omg|wtf|insane|crazy|clutch|let'?s go+|\bgg\b|\bez\b|\bw+\b|holy|no way|hype|nuts|cracked|goat|🔥|🤯)"
FUNNY = r"(lo+l|lmao|lmfao|kekw|\blul\b|omegalul|ha(ha)+|😂|🤣|i can'?t|im dead|bruh|clown|\bfunny)"
SERIOUS = r"(serious|story|honestly|\bsad\b|sorry|real talk|important|truth|\brip\b|respect|\bo7\b|💔|😢|damn)"
MODES = ["Auto (best moments)", "Hyped", "Funny", "Serious"]
SOURCES = ["Chat + streamer voice", "Streamer voice only", "Chat only"]
LAYOUTS = ["Face cam on top + Game below", "Game only (blurred background)"]


def tool(name):
    exe = name + (".exe" if os.name == "nt" else "")
    for d in (os.path.join(BASE, "bin"), os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "bin")):
        if os.path.exists(os.path.join(d, exe)):
            return os.path.join(d, exe)
    return shutil.which(name) or name


def sh(cmd, **kw):
    return subprocess.run(cmd, creationflags=NOWIN, capture_output=True, **kw)


def probe(path):
    r = sh([tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=width,height:format=duration", "-of", "json", path])
    j = json.loads(r.stdout or b"{}")
    s = j["streams"][0]
    return int(s["width"]), int(s["height"]), float(j["format"]["duration"])


# ---------------------------------------------------------------- download
def download(url, folder, max_min, log, tag="source"):
    import yt_dlp
    from yt_dlp.utils import download_range_func
    os.makedirs(folder, exist_ok=True)
    for old in glob.glob(os.path.join(folder, tag + ".*")):
        os.remove(old)
    last = [-10]

    def hook(d):
        if d.get("status") == "downloading":
            try:
                p = float((d.get("_percent_str") or "0").strip().replace("%", ""))
            except ValueError:
                return
            if p - last[0] >= 10:
                last[0] = p
                log(f"   downloading... {p:.0f}%")

    o = {"format": "bv*[height<=1080]+ba/b[height<=1080]/b", "outtmpl": os.path.join(folder, tag + ".%(ext)s"),
         "merge_output_format": "mp4", "noplaylist": True, "quiet": True, "no_warnings": True,
         "progress_hooks": [hook], "live_from_start": True}
    ff = tool("ffmpeg")
    if os.path.isabs(ff):
        o["ffmpeg_location"] = os.path.dirname(ff)
    if max_min:
        o["download_ranges"] = download_range_func(None, [(0, max_min * 60)])
    with yt_dlp.YoutubeDL(o) as y:
        info = y.extract_info(url, download=True)
    try:
        return info["requested_downloads"][0]["filepath"]
    except Exception:
        return glob.glob(os.path.join(folder, tag + ".*"))[0]


def ref_info(url):
    import yt_dlp
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as y:
        return y.extract_info(url, download=False)


def get_chat(url, limit_s, log):
    try:
        from chat_downloader import ChatDownloader
        ev = []
        for m in ChatDownloader().get_chat(url, message_types=["text_message"]):
            t = m.get("time_in_seconds")
            if t is None:
                continue
            ev.append((t, m.get("message") or ""))
            if limit_s and t > limit_s:
                break
        log(f"   chat messages: {len(ev)}")
        return ev
    except Exception as e:
        log(f"   (no chat available: {str(e)[:80]}) -> using voice analysis")
        return []


# ---------------------------------------------------------------- analysis
def z(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / s if s > 1e-9 else x * 0


def audio_features(video):
    p = sh([tool("ffmpeg"), "-v", "quiet", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
    a = np.frombuffer(p.stdout, np.int16).astype(np.float32) / 32768
    n = len(a) // 16000
    a = a[:n * 16000].reshape(n, 10, 1600)
    sub = np.sqrt((a ** 2).mean(2) + 1e-9)
    rms = sub.mean(1)
    return dict(rms=rms, burst=sub.std(1) / (rms + 1e-6), voiced=(sub > 0.015).mean(1))


def kw_series(ev, N, rx=None):
    s = np.zeros(N)
    for t, m in ev:
        if 0 <= int(t) < N and (rx is None or re.search(rx, m, re.I)):
            s[int(t)] += 1
    return np.convolve(s, np.ones(3) / 3, "same")


def build_score(mode, src, N, a, chat, speech):
    lag = lambda x: np.concatenate([x[6:], np.zeros(6)]) if len(x) > 6 else x  # chat reacts ~6s late
    has_chat = len(chat) > 20 and src != "Streamer voice only"
    wc = (0.9 if src == "Chat only" else 0.45) if has_chat else 0.0
    c_all, c_h, c_f, c_s = (lag(kw_series(chat, N, r)) for r in (None, HYPE, FUNNY, SERIOUS))
    s_h, s_f, s_s = (kw_series(speech, N, r) for r in (HYPE, FUNNY, SERIOUS))
    m = min(N, len(a["rms"]))
    pad = lambda x: np.pad(x[:m], (0, N - m))
    loud, burst, voiced = z(pad(a["rms"])), z(pad(a["burst"])), z(pad(a["voiced"]))
    hyped = wc * (0.6 * z(c_all) + 0.4 * z(c_h)) + (1 - wc) * (0.6 * loud + 0.4 * burst) + 0.25 * z(s_h)
    funny = wc * (0.6 * z(c_f) + 0.4 * z(c_all)) + (1 - wc) * (0.5 * burst + 0.3 * loud) + 0.3 * z(s_f)
    serious = 0.5 * voiced - 0.5 * burst - 0.2 * loud + (0.4 * z(c_s) if has_chat else 0) + 0.3 * z(s_s)
    return {"Hyped": hyped, "Funny": funny, "Serious": serious}.get(mode, np.maximum.reduce([hyped, funny, serious]))


def pick_windows(score, L, n):
    if len(score) <= L:
        return [0]
    w = np.convolve(score, np.ones(L) / L, "valid")
    chosen = []
    for i in np.argsort(-w):
        if all(abs(int(i) - j) >= L for j in chosen):
            chosen.append(int(i))
        if len(chosen) >= n:
            break
    return sorted(chosen)


_model = None
def whisper():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("base", compute_type="int8")
    return _model


def speech_events(video, log):
    try:
        segs, _ = whisper().transcribe(video, vad_filter=True)
        return [(s.start, s.text) for s in segs]
    except Exception as e:
        log(f"   (deep transcription skipped: {str(e)[:80]})")
        return []


def clip_words(video, start, L, tmp):
    wav = os.path.join(tmp, "c.wav")
    sh([tool("ffmpeg"), "-y", "-v", "quiet", "-ss", str(start), "-t", str(L), "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav])
    segs, _ = whisper().transcribe(wav, word_timestamps=True, vad_filter=True)
    return [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or []) if w.word.strip()]


# ---------------------------------------------------------------- render
def crop_s(r, W, H):
    x, y, w, h = [int(v) for v in r]
    x, y = max(0, min(x, W - 2)), max(0, min(y, H - 2))
    w, h = max(2, min(w, W - x)) & ~1, max(2, min(h, H - y)) & ~1
    return f"crop={w}:{h}:{x}:{y}"


def render(video, start, L, c, W, H, idx, log):
    out = c["out"]
    name = f"THUNDER_clip_{idx:02d}.mp4"
    game = c.get("game_roi") or (0, 0, W, H)
    face = c.get("face_roi")
    g = crop_s(game, W, H)
    if face and c["layout"] == LAYOUTS[0]:
        f = crop_s(face, W, H)
        fc = (f"[0:v]{f},scale=1080:640:force_original_aspect_ratio=increase,crop=1080:640[f];"
              f"[0:v]{g},scale=1080:1280:force_original_aspect_ratio=increase,crop=1080:1280[g];[f][g]vstack[v]")
    else:
        fc = (f"[0:v]{g},split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30[bg];"
              f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v]")
    cap = False
    if c["caption"] and not c["caption"].startswith("None"):
        try:
            words = clip_words(video, start, L, out)
            cap = build_ass(words, c["caption"], os.path.join(out, "_cap.ass"))
        except Exception as e:
            log(f"   (captions skipped: {str(e)[:80]})")
    fc += ";[v]ass=_cap.ass[o]" if cap else ";[v]null[o]"
    cmd = [tool("ffmpeg"), "-y", "-v", "error", "-ss", str(start), "-t", str(L), "-i", video, "-filter_complex", fc,
           "-map", "[o]", "-map", "0:a?", "-r", str(c.get("fps") or 30), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", name]
    r = subprocess.run(cmd, cwd=out, creationflags=NOWIN, capture_output=True)
    if r.returncode:
        log("   ffmpeg error: " + r.stderr.decode(errors="ignore")[-300:])
    return os.path.join(out, name)


# ---------------------------------------------------------------- main pipeline
def run(c, log, prog):
    out = c["out"]
    os.makedirs(out, exist_ok=True)
    video = c["video"]
    W, H, dur = probe(video)
    N, L = int(dur), int(c["clip_len"])
    if c.get("ref"):
        log("Reading reference video style...")
        try:
            i = ref_info(c["ref"])
            if i.get("duration"):
                L = int(min(90, max(15, i["duration"])))
            c["fps"] = int(i.get("fps") or 30)
            log(f"   reference '{(i.get('title') or '')[:40]}' -> clip length {L}s @ {c['fps']}fps")
        except Exception as e:
            log(f"   (reference failed: {str(e)[:80]})")
    prog(0.1)
    log("Analysing streamer voice...")
    a = audio_features(video)
    chat = get_chat(c["url"], dur, log) if c["src"] != SOURCES[1] and c.get("url") else []
    prog(0.25)
    speech = []
    if c.get("deep"):
        log("Deep analysis: transcribing whole video (slow)...")
        speech = speech_events(video, log)
    log(f"Finding the best '{c['mode']}' moments...")
    score = build_score(c["mode"], c["src"], N, a, chat, speech)
    starts = pick_windows(score, L, c["n"])
    prog(0.35)
    files = []
    for k, s in enumerate(starts, 1):
        log(f"Rendering clip {k}/{len(starts)}  [{s // 60}:{s % 60:02d} - {(s + L) // 60}:{(s + L) % 60:02d}]")
        files.append(render(video, s, L, c, W, H, k, log))
        prog(0.35 + 0.65 * k / len(starts))
    for t in ("_cap.ass", "c.wav"):
        try: os.remove(os.path.join(out, t))
        except OSError: pass
    log(f"DONE! {len(files)} clips saved in: {out}")
    return files
