"""Generates the THUNDER CLIPPER logo (assets/logo.png + assets/icon.ico)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 512
os.makedirs("assets", exist_ok=True)
yy, xx = np.mgrid[0:S, 0:S]
t = (xx + yy) / (2 * S)
bg = np.zeros((S, S, 4), np.uint8)
for i, (a, b) in enumerate(zip((12, 8, 48), (96, 24, 190))):
    bg[..., i] = a + (b - a) * t
bg[..., 3] = 255
img = Image.fromarray(bg)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), 110, fill=255)
img.putalpha(mask)

# neon ring
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(ring).ellipse((46, 46, S - 46, S - 46), outline=(0, 229, 255, 255), width=14)
img = Image.alpha_composite(img, ring.filter(ImageFilter.GaussianBlur(14)))
img = Image.alpha_composite(img, ring)

# lightning bolt
bolt = [(300, 36), (120, 288), (228, 288), (188, 476), (392, 202), (280, 202), (344, 36)]
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(glow).polygon(bolt, fill=(255, 214, 0, 255))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(26)))
d = ImageDraw.Draw(img)
d.polygon(bolt, fill=(255, 221, 0, 255), outline=(255, 255, 255, 255))
d.line(bolt + [bolt[0]], fill=(255, 255, 255, 255), width=5)

# clip "scissor" slash
d.line((70, 420, 440, 120), fill=(255, 255, 255, 140), width=3)

img.save("assets/logo.png")
img.save("assets/icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("logo done")
