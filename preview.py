"""Draws a phone-shaped example of the selected caption style (shown in the app)."""
from PIL import Image, ImageDraw, ImageFont
from captions import STYLES

FONTS = {"Impact": ["impact.ttf"], "Arial Black": ["ariblk.ttf"], "Arial": ["arial.ttf"]}


def font(name, size):
    for f in FONTS.get(name, []) + ["arialbd.ttf", "DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def rgb(h):                       # ASS "&H00BBGGRR&" -> (r,g,b)
    s = h[2:-1][-6:]
    return (int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16))


def caption_preview(name, W=540, H=960):
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    top = H // 3
    for y in range(H):
        if y < top:
            t = y / top; c = (int(70 - 30 * t), int(35 - 10 * t), int(150 - 50 * t))
        else:
            t = (y - top) / (H - top); c = (int(15 + 10 * t), int(25 + 30 * t), int(70 + 50 * t))
        d.line((0, y, W, y), fill=c)
    d.ellipse((W // 2 - 70, 70, W // 2 + 70, 210), fill=(255, 205, 160))
    d.pieslice((W // 2 - 140, 230, W // 2 + 140, 480), 180, 360, fill=(90, 70, 170))
    d.text((14, 12), "FACE CAM", font=font("Arial", 18), fill=(255, 255, 255))
    d.text((14, top + 12), "GAME", font=font("Arial", 18), fill=(0, 229, 255))
    d.line((W // 2 - 30, 560, W // 2 + 30, 560), fill=(0, 229, 255), width=3)
    d.line((W // 2, 530, W // 2, 590), fill=(0, 229, 255), width=3)
    st = STYLES.get(name)
    if not st:
        d.text((W // 2, H - 150), "No captions", font=font("Arial", 28), fill=(200, 200, 200), anchor="mm")
        return im.convert("RGB")

    words = ["insane"] if st["chunk"] == 1 else "this is insane bro wow lol".split()[:st["chunk"]]
    words = [w.upper() if st["upper"] else (w.capitalize() if i == 0 else w) for i, w in enumerate(words)]
    hi = (2 if len(words) >= 3 else len(words) - 1) if st["hl"] else -1
    fs = int(st["size"] * 0.5)
    f = font(st["font"], fs)
    ol = max(1, int(st["ol"] * 0.5)) if st["bs"] == 1 else 0
    sp = f.getlength(" ")
    lines, cur, w_cur = [], [], 0
    for i, w in enumerate(words):
        wl = f.getlength(w)
        if cur and w_cur + sp + wl > W - 60:
            lines.append(cur); cur, w_cur = [], 0
        cur.append((i, w, wl)); w_cur += wl + (sp if len(cur) > 1 else 0)
    lines.append(cur)
    lh = int(fs * 1.2)
    y = H - int(st["mv"] * 0.5) - lh * len(lines)
    if st["bs"] == 3:
        bw = max(sum(x[2] for x in l) + sp * (len(l) - 1) for l in lines)
        d.rounded_rectangle((W / 2 - bw / 2 - 14, y - 8, W / 2 + bw / 2 + 14, y + lh * len(lines) + 4), 10, fill=(0, 0, 0, 190))
    for l in lines:
        x = (W - (sum(t[2] for t in l) + sp * (len(l) - 1))) / 2
        for i, w, wl in l:
            col = rgb(st["hl"]) if i == hi else (255, 255, 255)
            d.text((x, y), w, font=f, fill=col, stroke_width=ol, stroke_fill=(0, 0, 0))
            x += wl + sp
        y += lh
    return im.convert("RGB")
