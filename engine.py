"""Caption styles -> ASS subtitle files (burned in by ffmpeg)."""

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H0000FFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,{bs},{ol},{sh},2,60,60,{mv},1

[Events]
Format: Layer, Start, End, Style, MarginL, MarginR, MarginV, Effect, Text
"""

# colours are BGR: yellow=00FFFF, green=00FF00, pink=B400FF
STYLES = {
    "Hormozi (yellow word highlight)": dict(font="Impact", size=100, ol=7, sh=2, bs=1, mv=560, chunk=3, upper=True, hl="&H0000FFFF&", pop=False),
    "Pop (one word at a time)":        dict(font="Impact", size=140, ol=8, sh=3, bs=1, mv=600, chunk=1, upper=True, hl="&H00FFFFFF&", pop=True),
    "Karaoke (green)":                 dict(font="Arial Black", size=82, ol=6, sh=2, bs=1, mv=520, chunk=4, upper=False, hl="&H0000FF00&", pop=False),
    "Neon pink":                       dict(font="Arial Black", size=88, ol=6, sh=2, bs=1, mv=520, chunk=3, upper=True, hl="&H00B400FF&", pop=True),
    "Classic (white, bottom)":         dict(font="Arial", size=64, ol=4, sh=1, bs=1, mv=260, chunk=6, upper=False, hl=None, pop=False),
    "Minimal box":                     dict(font="Arial", size=58, ol=14, sh=0, bs=3, mv=260, chunk=5, upper=False, hl=None, pop=False),
    "None (no captions)":              None,
}


def ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_ass(words, style_name, path):
    """words = [(start, end, text)] relative to clip start. Returns True if written."""
    st = STYLES.get(style_name)
    if not st or not words:
        return False
    lines = [HEAD.format(**st)]
    n = st["chunk"]
    for c in range(0, len(words), n):
        chunk = words[c:c + n]
        txt = [(w[2].upper() if st["upper"] else w[2]).replace("{", "").replace("}", "") for w in chunk]
        for i, (s, e, _) in enumerate(chunk):
            end = chunk[i + 1][0] if i + 1 < len(chunk) else e + 0.15
            end = max(end, s + 0.06)
            parts = []
            for j, tx in enumerate(txt):
                if st["hl"] and j == i:
                    pop = r"\fscx115\fscy115" if st["pop"] else ""
                    parts.append("{\\1c%s%s}%s{\\1c&H00FFFFFF&\\fscx100\\fscy100}" % (st["hl"], pop, tx))
                else:
                    parts.append(tx)
            text = " ".join(parts)
            if st["pop"] and not st["hl"]:
                text = r"{\fscx70\fscy70\t(0,90,\fscx100\fscy100)}" + text
            lines.append(f"Dialogue: 0,{ts(s)},{ts(end)},Default,0,0,0,,{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True
