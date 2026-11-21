"""THUNDER CLIPPER - GUI.  Contributors: THAKSHIL & JISSHU"""
import os, sys, queue, threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import engine
from captions import STYLES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
GOLD, CYAN, BG, CARD = "#FFD600", "#00E5FF", "#0B0720", "#161032"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("THUNDER CLIPPER")
        self.geometry("980x780")
        self.configure(fg_color=BG)
        assets = os.path.join(engine.BASE, "assets")
        try:
            self.iconbitmap(os.path.join(assets, "icon.ico"))
        except Exception:
            pass
        self.q = queue.Queue()
        self.video = None
        self.face = self.game = None

        head = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        head.pack(fill="x", padx=16, pady=(16, 8))
        try:
            logo = ctk.CTkImage(Image.open(os.path.join(assets, "logo.png")), size=(84, 84))
            ctk.CTkLabel(head, image=logo, text="").pack(side="left", padx=14, pady=10)
        except Exception:
            pass
        box = ctk.CTkFrame(head, fg_color="transparent")
        box.pack(side="left")
        ctk.CTkLabel(box, text="⚡ THUNDER CLIPPER", font=("Segoe UI Black", 34), text_color=GOLD).pack(anchor="w")
        ctk.CTkLabel(box, text="Turn any stream or video into viral portrait clips   •   by THAKSHIL & JISSHU",
                     font=("Segoe UI", 13), text_color=CYAN).pack(anchor="w")

        body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        body.pack(fill="x", padx=16, pady=8)
        body.columnconfigure(1, weight=1)
        self.url = self.row(body, 0, "Stream / video link", "https://twitch.tv/videos/…  or  YouTube link")
        self.ref = self.row(body, 1, "Reference video (optional)", "Instagram Reel / YouTube Short link")

        self.mode = self.combo(body, 2, "Moment to find", engine.MODES)
        self.src = self.combo(body, 3, "Detect from", engine.SOURCES)
        self.layout = self.combo(body, 4, "Portrait layout", engine.LAYOUTS)
        self.cap = self.combo(body, 5, "Caption style", list(STYLES))
        self.cap.set(list(STYLES)[0])

        ctk.CTkLabel(body, text="Clips / length (sec)").grid(row=6, column=0, padx=14, pady=6, sticky="w")
        nf = ctk.CTkFrame(body, fg_color="transparent")
        nf.grid(row=6, column=1, sticky="w", padx=8)
        self.n = ctk.CTkEntry(nf, width=60); self.n.insert(0, "5"); self.n.pack(side="left")
        self.len = ctk.CTkEntry(nf, width=60); self.len.insert(0, "45"); self.len.pack(side="left", padx=8)
        ctk.CTkLabel(nf, text="max minutes to grab (0=all):").pack(side="left", padx=(16, 4))
        self.maxm = ctk.CTkEntry(nf, width=60); self.maxm.insert(0, "0"); self.maxm.pack(side="left")
        self.deep = ctk.CTkCheckBox(nf, text="Deep analysis (transcribe all, slower)")
        self.deep.pack(side="left", padx=16)

        ctk.CTkLabel(body, text="Save clips to").grid(row=7, column=0, padx=14, pady=6, sticky="w")
        of = ctk.CTkFrame(body, fg_color="transparent")
        of.grid(row=7, column=1, sticky="ew", padx=8)
        self.out = ctk.CTkEntry(of); self.out.pack(side="left", fill="x", expand=True)
        self.out.insert(0, os.path.join(os.path.expanduser("~"), "Videos", "ThunderClips"))
        ctk.CTkButton(of, text="Browse", width=80, command=lambda: self.browse()).pack(side="left", padx=6)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=16)
        self.b1 = ctk.CTkButton(bf, text="1 ▸ Fetch video & select Face cam + Game", height=44, fg_color="#5B2BE0",
                                font=("Segoe UI", 14, "bold"), command=self.fetch)
        self.b1.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.b2 = ctk.CTkButton(bf, text="2 ▸ ⚡ START CLIPPING", height=44, fg_color=GOLD, text_color="black",
                                hover_color="#FFEA70", font=("Segoe UI", 14, "bold"), command=self.start, state="disabled")
        self.b2.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.status = ctk.CTkLabel(self, text="Regions: not selected", text_color=CYAN)
        self.status.pack(pady=(8, 0))
        self.bar = ctk.CTkProgressBar(self, progress_color=GOLD)
        self.bar.set(0)
        self.bar.pack(fill="x", padx=16, pady=6)
        self.logbox = ctk.CTkTextbox(self, fg_color=CARD, height=200)
        self.logbox.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log("Welcome to THUNDER CLIPPER ⚡  Paste a link, then press step 1.")
        self.after(100, self.poll)

    # ---- widgets helpers
    def row(self, p, r, label, ph):
        ctk.CTkLabel(p, text=label).grid(row=r, column=0, padx=14, pady=6, sticky="w")
        e = ctk.CTkEntry(p, placeholder_text=ph)
        e.grid(row=r, column=1, sticky="ew", padx=8, pady=6)
        return e

    def combo(self, p, r, label, vals):
        ctk.CTkLabel(p, text=label).grid(row=r, column=0, padx=14, pady=6, sticky="w")
        c = ctk.CTkOptionMenu(p, values=vals, fg_color="#2A1F5C", button_color="#5B2BE0", width=320)
        c.grid(row=r, column=1, sticky="w", padx=8, pady=6)
        return c

    def browse(self):
        d = filedialog.askdirectory()
        if d:
            self.out.delete(0, "end"); self.out.insert(0, d)

    def log(self, m):
        self.q.put(("log", m))

    def poll(self):
        try:
            while True:
                k, v = self.q.get_nowait()
                if k == "log":
                    self.logbox.insert("end", v + "\n"); self.logbox.see("end")
                elif k == "prog":
                    self.bar.set(v)
                elif k == "fetched":
                    self.b1.configure(state="normal"); self.pick_regions()
                elif k == "done":
                    self.b1.configure(state="normal"); self.b2.configure(state="normal")
                    if v: os.startfile(v) if os.name == "nt" else None
        except queue.Empty:
            pass
        self.after(100, self.poll)

    # ---- step 1
    def fetch(self):
        url = self.url.get().strip()
        if not url:
            return messagebox.showwarning("THUNDER CLIPPER", "Paste a stream/video link first.")
        self.b1.configure(state="disabled")
        folder = os.path.join(self.out.get(), "_work")

        def work():
            try:
                self.log("Downloading source (live streams are recorded up to the minute limit)...")
                self.video = engine.download(url, folder, int(self.maxm.get() or 0), self.log)
                self.log("Source ready ✔")
                self.q.put(("fetched", None))
            except Exception as e:
                self.log(f"ERROR: {e}"); self.q.put(("done", None))
        threading.Thread(target=work, daemon=True).start()

    def pick_regions(self):
        import cv2
        cap = cv2.VideoCapture(self.video)
        cap.set(1, int(cap.get(7) * 0.3))
        ok, f = cap.read(); cap.release()
        if not ok:
            return self.log("Could not read a frame.")
        sc = min(1.0, 1280 / f.shape[1])
        d = cv2.resize(f, None, fx=sc, fy=sc)
        back = lambda r: None if r[2] < 8 else tuple(int(v / sc) for v in r)
        self.face = back(cv2.selectROI("Drag a box around the STREAMER FACE CAM - ENTER to confirm (C = skip)", d, False))
        cv2.destroyAllWindows()
        self.game = back(cv2.selectROI("Drag a box around the GAME screen - ENTER to confirm (C = full frame)", d, False))
        cv2.destroyAllWindows()
        self.status.configure(text=f"Face cam: {'✔' if self.face else 'skipped'}    Game: {'✔' if self.game else 'full frame'}")
        self.b2.configure(state="normal")

    # ---- step 2
    def start(self):
        try:
            cfg = dict(video=self.video, url=self.url.get().strip(), ref=self.ref.get().strip(), mode=self.mode.get(),
                       src=self.src.get(), layout=self.layout.get(), caption=self.cap.get(), n=int(self.n.get()),
                       clip_len=int(self.len.get()), out=self.out.get(), face_roi=self.face, game_roi=self.game,
                       deep=bool(self.deep.get()))
        except ValueError:
            return messagebox.showwarning("THUNDER CLIPPER", "Clips and length must be numbers.")
        self.b2.configure(state="disabled"); self.b1.configure(state="disabled"); self.bar.set(0.02)

        def work():
            try:
                engine.run(cfg, self.log, lambda v: self.q.put(("prog", v)))
                self.q.put(("done", cfg["out"]))
            except Exception as e:
                self.log(f"ERROR: {e}"); self.q.put(("done", None))
        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
