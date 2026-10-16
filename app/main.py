"""
app/main.py
Antarmuka utama aplikasi TSP Metaheuristic Optimizer.
Dibangun menggunakan CustomTkinter dan Matplotlib.
"""

import sys
import os
import threading
import subprocess

# paket-paket yang wajib ada
_required = ["customtkinter", "matplotlib", "numpy", "pandas", "openpyxl"]
# instalasi otomatis hanya dijalankan saat tidak dalam bentuk installer (.exe/.app)
if not getattr(sys, "frozen", False):
    for _pkg in _required:
        try:
            __import__(_pkg)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"])

sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# algoritma utama
from algorithms.sa import simulated_annealing
from algorithms.tabu import tabu_search

# modul pendukung — dibuat opsional agar app tetap jalan meski belum semua file ada
try:
    from utils.loader import load_cities, get_coords, get_names, route_to_names
    _has_loader = True
except ImportError:
    _has_loader = False

try:
    from algorithms.constructive import nearest_neighbor, farthest_insertion, random_route
    _has_constructive = True
except ImportError:
    _has_constructive = False

try:
    from algorithms.two_opt import two_opt
    _has_two_opt = True
except ImportError:
    _has_two_opt = False

try:
    from components.map_plot import plot_route
    _has_map_plot = True
except ImportError:
    _has_map_plot = False

try:
    from components.export import export_results
    _has_export = True
except ImportError:
    _has_export = False

try:
    from utils.distance import distance_matrix as _ext_dm
    _has_dm = True
except ImportError:
    _has_dm = False


# matriks jarak dihitung manual jika utils/distance belum tersedia
def _build_distance_matrix(coords):
    if _has_dm:
        return _ext_dm(coords)
    n = len(coords)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            mat[i][j] = np.sqrt(dx * dx + dy * dy)
    return mat


# ── Palet warna: Mono + Signal Orange (Design 6) ─────────────────────────────
BG         = "#FFFFFF"
SURFACE    = "#FFFFFF"
SIDEBAR_BG = "#0A0A0A"   # sidebar hitam
ACCENT     = "#FF5A1F"   # oranye aksen
FG         = "#0A0A0A"   # teks gelap
GRAY       = "#737373"
GOLD       = "#F59E0B"   # untuk highlight compare
GREEN_PCT  = "#22AA66"   # persentase improvement
BORDER     = "#E8E8E8"
DARK_BRD   = "#2A2A2A"   # border dalam sidebar gelap
SB_FG      = "#CCCCCC"   # teks dalam sidebar
SB_MUTED   = "#555555"   # teks muted dalam sidebar
CARD_GAIN  = "#FFF4EF"   # latar card Total Gain

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# nilai default SA dan Tabu
SA_T_START    = 1000.0
SA_T_MIN      = 1e-3
SA_COOLING    = 0.995
TABU_MAX_ITER = 500
TABU_TENURE   = None


# ══════════════════════════════════════════════════════════════════════════════════
class TSPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TSP Metaheuristic Optimizer")
        self.geometry("1280x740")
        self.minsize(1000, 640)
        self.configure(fg_color=BG)

        # state
        self.cities       = None
        self.dist_matrix  = None
        self.last_route   = None
        self.last_dist    = None
        self.last_history = []
        self.init_dist    = None
        self.runs         = []

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_panel()

    # ── sidebar gelap ──────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=265, fg_color=SIDEBAR_BG, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        row = 0

        # judul
        title_f = ctk.CTkFrame(sb, fg_color="transparent")
        title_f.grid(row=row, column=0, padx=18, pady=(22, 16), sticky="w"); row += 1
        ctk.CTkLabel(title_f,
                     text="  TSP Optimizer",
                     font=("Segoe UI", 16, "bold"),
                     text_color=SURFACE,
                     image=self._dot_icon(), compound="left"
                     ).pack(side="left")

        self._dark_divider(sb, row); row += 1

        # data kota
        ctk.CTkLabel(sb, text="DATA KOTA",
                     font=("Segoe UI", 9, "bold"), text_color=SB_MUTED,
                     ).grid(row=row, column=0, padx=18, pady=(10, 5), sticky="w"); row += 1

        self.file_label = ctk.CTkLabel(sb, text="Belum ada data",
                                        font=("Segoe UI", 10), text_color=SB_MUTED,
                                        wraplength=220)
        self.file_label.grid(row=row, column=0, padx=18, sticky="w"); row += 1

        ctk.CTkButton(sb, text="▲  Upload CSV / Excel",
                      fg_color=ACCENT, text_color=SURFACE, hover_color="#D94A10",
                      font=("Segoe UI", 11, "bold"), corner_radius=7,
                      command=self._load_file
                      ).grid(row=row, column=0, padx=14, pady=(6, 4), sticky="ew"); row += 1

        ctk.CTkButton(sb, text="✏️  Input Manual",
                      fg_color="transparent", text_color=SB_FG,
                      border_color=DARK_BRD, border_width=1,
                      hover_color="#1A1A1A", font=("Segoe UI", 11), corner_radius=7,
                      command=self._input_manual
                      ).grid(row=row, column=0, padx=14, pady=(0, 4), sticky="ew"); row += 1

        ctk.CTkLabel(sb,
                     text="Format CSV: kolom no, name, x, y",
                     font=("Segoe UI", 9), text_color=SB_MUTED, wraplength=220, justify="left"
                     ).grid(row=row, column=0, padx=18, pady=(0, 10), sticky="w"); row += 1

        self._dark_divider(sb, row); row += 1

        # inisialisasi rute
        ctk.CTkLabel(sb, text="INISIALISASI RUTE",
                     font=("Segoe UI", 9, "bold"), text_color=SB_MUTED,
                     ).grid(row=row, column=0, padx=18, pady=(10, 5), sticky="w"); row += 1

        self.var_constructive = ctk.StringVar(value="Nearest Neighbor")
        ctk.CTkOptionMenu(sb, values=["Nearest Neighbor", "Farthest Insertion", "Random"],
                          variable=self.var_constructive,
                          fg_color="#1A1A1A", button_color=ACCENT,
                          button_hover_color="#D94A10",
                          text_color=SB_FG,
                          dropdown_fg_color="#1A1A1A",
                          dropdown_text_color=SB_FG,
                          dropdown_hover_color="#2A2A2A",
                          corner_radius=7,
                          ).grid(row=row, column=0, padx=14, pady=(0, 10), sticky="ew"); row += 1

        self._dark_divider(sb, row); row += 1

        # metaheuristik
        ctk.CTkLabel(sb, text="METAHEURISTIK",
                     font=("Segoe UI", 9, "bold"), text_color=SB_MUTED,
                     ).grid(row=row, column=0, padx=18, pady=(10, 6), sticky="w"); row += 1

        self.var_use_meta = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sb, text="Gunakan metaheuristik",
                        variable=self.var_use_meta,
                        text_color=SB_FG, fg_color=ACCENT, hover_color="#D94A10",
                        checkmark_color=SURFACE, font=("Segoe UI", 10),
                        border_color=DARK_BRD, bg_color=SIDEBAR_BG,
                        command=self._toggle_meta_section
                        ).grid(row=row, column=0, padx=18, pady=(0, 6), sticky="w"); row += 1

        self.var_meta = ctk.StringVar(value="Simulated Annealing")
        self.meta_option_menu = ctk.CTkOptionMenu(
            sb, values=["Simulated Annealing", "Tabu Search"],
            variable=self.var_meta,
            fg_color="#1A1A1A", button_color=ACCENT,
            button_hover_color="#D94A10",
            text_color=SB_FG,
            dropdown_fg_color="#1A1A1A",
            dropdown_text_color=SB_FG,
            dropdown_hover_color="#2A2A2A",
            corner_radius=7,
        )
        self.meta_option_menu.grid(row=row, column=0, padx=14, pady=(0, 8), sticky="ew"); row += 1

        self.var_two_opt = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sb, text="Terapkan 2-Opt setelahnya",
                        variable=self.var_two_opt,
                        text_color=SB_FG, fg_color=ACCENT, hover_color="#D94A10",
                        checkmark_color=SURFACE, font=("Segoe UI", 10),
                        border_color=DARK_BRD, bg_color=SIDEBAR_BG,
                        ).grid(row=row, column=0, padx=18, pady=(0, 14), sticky="w"); row += 1

        self._dark_divider(sb, row); row += 1

        # tombol aksi
        self.btn_run = ctk.CTkButton(
            sb, text="▶  JALANKAN",
            fg_color=ACCENT, text_color=SURFACE, hover_color="#D94A10",
            font=("Segoe UI", 14, "bold"), height=46, corner_radius=8,
            command=self._run
        )
        self.btn_run.grid(row=row, column=0, padx=14, pady=(16, 6), sticky="ew"); row += 1

        self.btn_export = ctk.CTkButton(
            sb, text="⬇  Export Hasil",
            fg_color="transparent", text_color=SB_FG,
            border_color=DARK_BRD, border_width=1,
            hover_color="#1A1A1A", font=("Segoe UI", 11), corner_radius=7,
            state="disabled", command=self._export
        )
        self.btn_export.grid(row=row, column=0, padx=14, pady=(0, 6), sticky="ew"); row += 1

        self.btn_compare = ctk.CTkButton(
            sb, text="⇄  Bandingkan Run",
            fg_color="transparent", text_color=GOLD,
            border_color="#3A3000", border_width=1,
            hover_color="#1A1A1A", font=("Segoe UI", 11), corner_radius=7,
            state="disabled", command=self._compare
        )
        self.btn_compare.grid(row=row, column=0, padx=14, pady=(0, 6), sticky="ew"); row += 1

        ctk.CTkButton(sb, text="↺  Reset",
                      fg_color="transparent", text_color=SB_MUTED,
                      border_color=DARK_BRD, border_width=1,
                      hover_color="#1A1A1A", font=("Segoe UI", 10), corner_radius=7,
                      command=self._reset
                      ).grid(row=row, column=0, padx=14, pady=(0, 8), sticky="ew"); row += 1

        self.lbl_run_count = ctk.CTkLabel(sb, text="", font=("Segoe UI", 9),
                                           text_color=SB_MUTED, wraplength=230)
        self.lbl_run_count.grid(row=row, column=0, padx=18, pady=(0, 4), sticky="w"); row += 1

        self.lbl_status = ctk.CTkLabel(sb, text="", font=("Segoe UI", 10),
                                        text_color=SB_MUTED, wraplength=230)
        self.lbl_status.grid(row=row, column=0, padx=18, pady=(0, 20), sticky="w")

    def _dot_icon(self):
        """Buat icon kotak oranye kecil untuk judul."""
        import tkinter as tk
        img = tk.PhotoImage(width=14, height=14)
        for x in range(14):
            for y in range(14):
                img.put("#FF5A1F", (x, y))
        self._icon_ref = img
        return img

    # ── main panel: split layout ───────────────────────────────────────────────

    def _build_main_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BG)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(panel, fg_color=BG)
        content.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)   # map expands
        content.grid_columnconfigure(1, minsize=258) # right panel fixed

        # peta rute
        map_frame = ctk.CTkFrame(content, fg_color=SURFACE,
                                  border_width=1, border_color=BORDER, corner_radius=10)
        map_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        map_frame.grid_rowconfigure(1, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(map_frame, text="Peta Rute",
                     font=("Segoe UI", 12, "bold"), text_color=FG,
                     ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")

        fig, ax = plt.subplots(figsize=(6.5, 4.8), facecolor=SURFACE)
        ax.set_facecolor("#F8F8F8")
        ax.set_title("Pilih file dan jalankan algoritma", color=GRAY, fontsize=10)
        self.map_fig, self.map_ax = fig, ax
        self.map_canvas = FigureCanvasTkAgg(fig, master=map_frame)
        self.map_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        # right panel
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self._build_right_panel(right)

    def _build_right_panel(self, parent):
        # ── mini stats cards (2×2) ─────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(parent, fg_color=SURFACE,
                                    border_width=1, border_color=BORDER, corner_radius=10)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        stats_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(stats_frame, text="HASIL OPTIMASI",
                     font=("Segoe UI", 9, "bold"), text_color=GRAY,
                     ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 8), sticky="w")

        # card helper: returns (val_label, sub_label)
        def card(parent, row, col, title, val_default="—", sub_default="",
                 val_color=FG, sub_color=GREEN_PCT, is_accent=False):
            bg = CARD_GAIN if is_accent else SURFACE
            bd = "#FFD5C0" if is_accent else BORDER
            f = ctk.CTkFrame(parent, fg_color=bg,
                              border_width=1, border_color=bd, corner_radius=8)
            f.grid(row=row, column=col, padx=(8 if col == 0 else 4, 4 if col == 0 else 8),
                   pady=(0, 8), sticky="nsew")
            ctk.CTkLabel(f, text=title, font=("Segoe UI", 9), text_color=GRAY,
                         ).pack(anchor="w", padx=9, pady=(8, 2))
            v = ctk.CTkLabel(f, text=val_default,
                              font=("Segoe UI", 14, "bold"), text_color=val_color)
            v.pack(anchor="w", padx=9)
            s = ctk.CTkLabel(f, text=sub_default, font=("Segoe UI", 9),
                              text_color=sub_color)
            s.pack(anchor="w", padx=9, pady=(0, 8))
            return v, s

        self.c_awal_val, self.c_awal_sub   = card(stats_frame, 1, 0, "Jarak Awal",
                                                    sub_default="km", sub_color=GRAY)
        self.c_meta_val, self.c_meta_pct   = card(stats_frame, 1, 1, "Hasil Optimasi",
                                                    sub_default="—", sub_color=GREEN_PCT)
        self.c_2opt_val, self.c_2opt_pct   = card(stats_frame, 2, 0, "Setelah 2-Opt",
                                                    sub_default="—", sub_color=GREEN_PCT)
        self.c_gain_val, self.c_gain_pct   = card(stats_frame, 2, 1, "Total Gain",
                                                    val_default="—", val_color=ACCENT,
                                                    sub_default="—", sub_color=ACCENT,
                                                    is_accent=True)

        # ── konvergensi chart ──────────────────────────────────────────────────
        conv_frame = ctk.CTkFrame(parent, fg_color=SURFACE,
                                   border_width=1, border_color=BORDER, corner_radius=10)
        conv_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        conv_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(conv_frame, text="KONVERGENSI",
                     font=("Segoe UI", 9, "bold"), text_color=GRAY,
                     ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        fig2, ax2 = plt.subplots(figsize=(3.2, 1.8), facecolor=SURFACE)
        ax2.set_facecolor("#FAFAFA")
        ax2.set_title("Jalankan algoritma dulu", color=GRAY, fontsize=8)
        self.conv_fig, self.conv_ax = fig2, ax2
        self.conv_canvas = FigureCanvasTkAgg(fig2, master=conv_frame)
        self.conv_canvas.get_tk_widget().grid(row=1, column=0, sticky="ew",
                                               padx=8, pady=(0, 8))

        # ── urutan rute ────────────────────────────────────────────────────────
        route_frame = ctk.CTkFrame(parent, fg_color=SURFACE,
                                    border_width=1, border_color=BORDER, corner_radius=10)
        route_frame.grid(row=2, column=0, sticky="nsew")
        route_frame.grid_rowconfigure(1, weight=1)
        route_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(route_frame, text="URUTAN RUTE",
                     font=("Segoe UI", 9, "bold"), text_color=GRAY,
                     ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.route_scroll = ctk.CTkScrollableFrame(
            route_frame, fg_color="transparent", corner_radius=0
        )
        self.route_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.route_scroll.grid_columnconfigure(0, weight=1)

        # placeholder
        ctk.CTkLabel(self.route_scroll, text="Belum ada rute.",
                     font=("Segoe UI", 10), text_color=GRAY,
                     ).grid(row=0, column=0, padx=4, pady=8, sticky="w")

    # ── event handlers ─────────────────────────────────────────────────────────

    def _toggle_meta_section(self):
        if self.var_use_meta.get():
            self.meta_option_menu.grid()
        else:
            self.meta_option_menu.grid_remove()

    def _load_file(self):
        if not _has_loader:
            messagebox.showerror("Belum tersedia",
                                 "utils/loader.py belum ada.\nTunggu teman push file-nya dulu.")
            return
        path = filedialog.askopenfilename(
            title="Pilih file kota",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"), ("Semua", "*.*")]
        )
        if not path:
            return
        try:
            self.cities      = load_cities(path)
            coords           = get_coords(self.cities)
            self.dist_matrix = _build_distance_matrix(coords)
            fname = os.path.basename(path)
            self.file_label.configure(
                text=f"✓ {fname}\n{len(self.cities)} kota dimuat", text_color=ACCENT
            )
            self._status(f"{len(self.cities)} kota siap diproses")
            self.runs = []
            self._update_run_counter()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca file:\n{e}")

    def _input_manual(self):
        win = ctk.CTkToplevel(self)
        win.title("Input Data Kota Manual")
        win.geometry("560x560")
        win.configure(fg_color=BG)
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text="✏️  Input Data Kota Manual",
                     font=("Segoe UI", 15, "bold"), text_color=ACCENT
                     ).grid(row=0, column=0, pady=(18, 2), padx=20, sticky="w")
        ctk.CTkLabel(win,
                     text="Isi nama kota beserta koordinat X dan Y.\n"
                          "Koordinat bisa berupa km, derajat, atau angka relatif apa saja.",
                     font=("Segoe UI", 10), text_color=GRAY, justify="left"
                     ).grid(row=1, column=0, pady=(0, 10), padx=20, sticky="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color=SURFACE,
                                         border_width=1, border_color=BORDER)
        scroll.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="nsew")
        scroll.grid_columnconfigure((1, 2, 3), weight=1)

        for col, (txt, w) in enumerate([("No", 40), ("Nama Kota", 180), ("X", 90), ("Y", 90)]):
            ctk.CTkLabel(scroll, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color=GRAY, width=w
                         ).grid(row=0, column=col, padx=4, pady=(4, 6))

        entries = []

        def _add_row(no=None, name="", x="", y=""):
            r = len(entries) + 1
            ctk.CTkLabel(scroll, text=str(r), font=("Segoe UI", 10),
                         text_color=GRAY, width=40
                         ).grid(row=r, column=0, padx=4, pady=2)
            e_name = ctk.CTkEntry(scroll, placeholder_text="Nama kota",
                                   fg_color=SURFACE, border_color=BORDER, text_color=FG,
                                   font=("Segoe UI", 10), width=180)
            e_name.grid(row=r, column=1, padx=4, pady=2)
            e_x = ctk.CTkEntry(scroll, placeholder_text="X",
                                fg_color=SURFACE, border_color=BORDER, text_color=FG,
                                font=("Segoe UI", 10), width=90)
            e_x.grid(row=r, column=2, padx=4, pady=2)
            e_y = ctk.CTkEntry(scroll, placeholder_text="Y",
                                fg_color=SURFACE, border_color=BORDER, text_color=FG,
                                font=("Segoe UI", 10), width=90)
            e_y.grid(row=r, column=3, padx=4, pady=2)
            if name: e_name.insert(0, name)
            if x:    e_x.insert(0, str(x))
            if y:    e_y.insert(0, str(y))
            entries.append((e_name, e_x, e_y))

        _add_row(name="Surabaya", x=112.7, y=-7.2)
        _add_row(name="Sidoarjo", x=112.7, y=-7.4)
        _add_row(name="Malang",   x=112.6, y=-7.9)
        for _ in range(5):
            _add_row()

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_frame, text="+ Tambah Baris",
                      fg_color=SURFACE, text_color=ACCENT,
                      border_color=ACCENT, border_width=1,
                      hover_color="#FFF4EF", font=("Segoe UI", 10),
                      command=_add_row
                      ).grid(row=0, column=0, padx=(0, 4), sticky="ew")

        def _use_data():
            cities = []
            for i, (e_name, e_x, e_y) in enumerate(entries):
                name = e_name.get().strip()
                x_s  = e_x.get().strip()
                y_s  = e_y.get().strip()
                if not name and not x_s and not y_s:
                    continue
                if not name or not x_s or not y_s:
                    messagebox.showwarning("Data tidak lengkap",
                        f"Baris {i+1}: isi semua kolom (nama, X, Y).")
                    return
                try:
                    cities.append({"no": i+1, "name": name,
                                   "x": float(x_s), "y": float(y_s)})
                except ValueError:
                    messagebox.showwarning("Format salah",
                        f"Baris {i+1}: X dan Y harus angka.")
                    return
            if len(cities) < 3:
                messagebox.showwarning("Kurang kota",
                    "Minimal 3 kota untuk menjalankan TSP.")
                return
            coords = [(c["x"], c["y"]) for c in cities]
            self.cities      = cities
            self.dist_matrix = _build_distance_matrix(coords)
            self.file_label.configure(
                text=f"✓ Input manual\n{len(cities)} kota dimuat", text_color=ACCENT
            )
            self._status(f"{len(cities)} kota siap (manual)")
            self.runs = []
            self._update_run_counter()
            win.destroy()

        ctk.CTkButton(btn_frame, text="✓  Gunakan Data Ini",
                      fg_color=ACCENT, text_color=SURFACE,
                      hover_color="#D94A10", font=("Segoe UI", 11, "bold"),
                      command=_use_data
                      ).grid(row=0, column=1, padx=(4, 0), sticky="ew")

    def _run(self):
        if self.cities is None:
            messagebox.showwarning("Perhatian", "Pilih file atau input data kota terlebih dahulu!")
            return
        if not _has_constructive:
            messagebox.showerror("Belum tersedia",
                                 "algorithms/constructive.py belum ada.\nTunggu teman push file-nya.")
            return
        self.btn_run.configure(state="disabled", text="⏳  Memproses...")
        self._status("Menghitung rute optimal...")
        threading.Thread(target=self._pipeline, daemon=True).start()

    def _pipeline(self):
        try:
            coords = [(c["x"], c["y"]) for c in self.cities]
            names  = [c["name"] for c in self.cities]
            dm     = self.dist_matrix

            # 1. Constructive
            c = self.var_constructive.get()
            if c == "Nearest Neighbor":
                init_route, init_dist = nearest_neighbor(dm)
            elif c == "Farthest Insertion":
                init_route, init_dist = farthest_insertion(dm)
            else:
                init_route, init_dist = random_route(dm)

            # 2. Metaheuristik (opsional)
            use_meta = self.var_use_meta.get()
            m = self.var_meta.get() if use_meta else "—"
            if use_meta:
                if m == "Simulated Annealing":
                    meta_route, meta_dist, history = simulated_annealing(
                        dm, init_route,
                        T_start=SA_T_START, T_min=SA_T_MIN, cooling_rate=SA_COOLING
                    )
                else:
                    meta_route, meta_dist, history = tabu_search(
                        dm, init_route, tabu_tenure=TABU_TENURE, max_iter=TABU_MAX_ITER
                    )
            else:
                meta_route, meta_dist, history = init_route, init_dist, []

            # 3. 2-Opt
            if self.var_two_opt.get() and _has_two_opt:
                final_route, final_dist, _ = two_opt(meta_route, dm)
            else:
                final_route, final_dist = meta_route, meta_dist

            self.init_dist    = init_dist
            self.last_route   = final_route
            self.last_dist    = final_dist
            self.last_history = history

            self.after(0, lambda: self._show_results(
                coords, names, init_dist, meta_dist, final_dist, history, final_route, m, c
            ))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Terjadi kesalahan:\n{e}"))
            self.after(0, lambda: self.btn_run.configure(state="normal", text="▶  JALANKAN"))

    def _show_results(self, coords, names, init_dist, meta_dist, final_dist,
                      history, route, meta_name, constructive_name):
        gain = init_dist - final_dist
        pct  = gain / init_dist * 100 if init_dist else 0

        # update mini cards
        self.c_awal_val.configure(text=f"{init_dist:.1f}")
        self.c_awal_sub.configure(text="km")

        if self.var_use_meta.get():
            mpct = (init_dist - meta_dist) / init_dist * 100 if init_dist else 0
            self.c_meta_val.configure(text=f"{meta_dist:.1f}")
            self.c_meta_pct.configure(text=f"−{mpct:.1f}%")
        else:
            self.c_meta_val.configure(text="—")
            self.c_meta_pct.configure(text="tidak dipakai")

        if self.var_two_opt.get() and _has_two_opt:
            opct = (meta_dist - final_dist) / meta_dist * 100 if meta_dist else 0
            self.c_2opt_val.configure(text=f"{final_dist:.1f}")
            self.c_2opt_pct.configure(text=f"−{opct:.1f}%")
        else:
            self.c_2opt_val.configure(text="—")
            self.c_2opt_pct.configure(text="tidak dipakai")

        self.c_gain_val.configure(text=f"−{pct:.1f}%")
        self.c_gain_pct.configure(text=f"−{gain:.1f} km")

        self._draw_map(coords, names, route)
        self._draw_conv(history, meta_name)
        self._update_route_list(names, route)

        two_opt_used = self.var_two_opt.get() and _has_two_opt
        run_data = {
            "label":       f"Run {len(self.runs) + 1}",
            "init_method": constructive_name,
            "meta_method": meta_name,
            "two_opt":     two_opt_used,
            "init_dist":   init_dist,
            "meta_dist":   meta_dist,
            "final_dist":  final_dist,
            "gain":        gain,
            "pct":         pct,
            "route":       route,
            "names":       names,
            "history":     history,
        }
        if len(self.runs) >= 2:
            self.runs = [self.runs[-1], run_data]
        else:
            self.runs.append(run_data)

        self._update_run_counter()
        self.btn_run.configure(state="normal", text="▶  JALANKAN")
        self.btn_export.configure(state="normal")
        self._status(f"Selesai! Jarak optimal: {final_dist:.4f}")

    def _update_route_list(self, names, route):
        # bersihkan isi lama
        for widget in self.route_scroll.winfo_children():
            widget.destroy()

        dm = self.dist_matrix
        for idx, city_idx in enumerate(route):
            next_idx = route[(idx + 1) % len(route)]
            step_dist = dm[city_idx][next_idx] if dm is not None else 0

            row_f = ctk.CTkFrame(self.route_scroll, fg_color="transparent")
            row_f.grid(row=idx, column=0, sticky="ew", padx=2, pady=1)
            row_f.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row_f, text=f"{idx+1}.",
                         font=("Segoe UI", 10), text_color=GRAY, width=26
                         ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row_f, text=names[city_idx],
                         font=("Segoe UI", 10), text_color=FG, anchor="w"
                         ).grid(row=0, column=1, sticky="ew", padx=(2, 4))
            dist_text = "—" if idx == 0 else f"{step_dist:.1f}"
            ctk.CTkLabel(row_f, text=dist_text,
                         font=("Segoe UI", 10, "bold"),
                         text_color=ACCENT if idx > 0 else GRAY
                         ).grid(row=0, column=2, sticky="e")

            if idx < len(route) - 1:
                ctk.CTkFrame(self.route_scroll, height=1, fg_color=BORDER
                             ).grid(row=idx * 2 + 1, column=0, sticky="ew", padx=2)

    def _update_run_counter(self):
        n = len(self.runs)
        if n == 0:
            self.lbl_run_count.configure(text="")
            self.btn_compare.configure(state="disabled")
        elif n == 1:
            m = self.runs[0]['meta_method']
            m_label = m[:2].upper() if m != "—" else "Konstruktif"
            self.lbl_run_count.configure(
                text=f"Run 1 tersimpan ({m_label}). Jalankan lagi untuk bandingkan.",
                text_color=SB_MUTED
            )
            self.btn_compare.configure(state="disabled")
        else:
            self.lbl_run_count.configure(
                text="Run 1 & Run 2 tersimpan. Klik Bandingkan!",
                text_color=GOLD
            )
            self.btn_compare.configure(state="normal")

    def _draw_map(self, coords, names, route):
        if _has_map_plot:
            plot_route(coords, names, route, ax=self.map_ax)
        else:
            ax = self.map_ax
            ax.clear()
            ax.set_facecolor("#F8F8F8")
            self.map_fig.patch.set_facecolor(SURFACE)
            xs = [coords[i][0] for i in route] + [coords[route[0]][0]]
            ys = [coords[i][1] for i in route] + [coords[route[0]][1]]
            ax.plot(xs, ys, color=ACCENT, linewidth=2, zorder=1, alpha=0.85)
            ax.scatter([c[0] for c in coords], [c[1] for c in coords],
                       color=SURFACE, s=60, zorder=3,
                       edgecolors=ACCENT, linewidths=1.5)
            for name, coord in zip(names, coords):
                ax.annotate(name, coord, fontsize=7.5, color=FG,
                            xytext=(5, 4), textcoords="offset points")
            # titik start
            ax.scatter([coords[route[0]][0]], [coords[route[0]][1]],
                       color=ACCENT, s=110, zorder=4)
            ax.set_title("Rute Optimal TSP", color=FG, fontsize=10, pad=8)
            self._style_ax(ax)
        self.map_canvas.draw()

    def _draw_conv(self, history, meta_name):
        ax = self.conv_ax
        ax.clear()
        ax.set_facecolor("#FAFAFA")
        self.conv_fig.patch.set_facecolor(SURFACE)

        if not history:
            ax.set_title("Tidak ada data konvergensi", color=GRAY, fontsize=8)
            self.conv_canvas.draw()
            return

        iters      = [h["iter"] for h in history]
        best_dists = [h["best_dist"] for h in history]

        ax.plot(iters, best_dists, color=ACCENT, linewidth=2, zorder=3)
        ax.scatter([iters[0]],  [best_dists[0]],  color=GRAY,  s=30, zorder=5)
        ax.scatter([iters[-1]], [best_dists[-1]], color=ACCENT, s=40, zorder=5)

        if best_dists[0] > 0:
            impv = (best_dists[0] - best_dists[-1]) / best_dists[0] * 100
            ax.text(0.97, 0.92, f"−{impv:.1f}%",
                    transform=ax.transAxes, ha="right", va="top",
                    color=ACCENT, fontsize=8, fontweight="bold")

        ax.set_title(f"Konvergensi — {meta_name}", color=FG, fontsize=8, pad=6)
        ax.set_xlabel("Iterasi", color=GRAY, fontsize=7)
        ax.set_ylabel("Jarak", color=GRAY, fontsize=7)
        self._style_ax(ax)
        self.conv_canvas.draw()

    def _write_info(self, names, route, init_dist, meta_dist, final_dist,
                    meta_name, constructive_name):
        """Tidak digunakan di layout baru (digantikan route list + cards),
        tetap ada untuk kompatibilitas _compare window."""
        rn   = [names[i] for i in route]
        gain = init_dist - final_dist
        pct  = gain / init_dist * 100 if init_dist else 0
        two_opt_used = self.var_two_opt.get() and _has_two_opt

        lines = [
            "  RUTE OPTIMAL TSP",
            "",
            f"  Inisialisasi  : {constructive_name}",
            f"  Metaheuristik : {meta_name}",
            f"  2-Opt         : {'Ya' if two_opt_used else 'Tidak'}",
            "",
            "  Urutan Kota:",
            "  " + " → ".join(rn) + f" → {rn[0]}",
            "",
            "  " + "─" * 46,
            f"  Jarak Awal             : {init_dist:.4f}",
        ]
        if meta_name != "—":
            lines.append(f"  Setelah Metaheuristik  : {meta_dist:.4f}")
        if two_opt_used:
            lines.append(f"  Setelah 2-Opt          : {final_dist:.4f}")
        lines.append(f"  Total Improvement      : {gain:.4f}  ({pct:.2f}%)")
        return "\n".join(lines)

    def _compare(self):
        if len(self.runs) < 2:
            return
        r1, r2 = self.runs[0], self.runs[1]

        win = ctk.CTkToplevel(self)
        win.title("Perbandingan Run")
        win.geometry("860x600")
        win.configure(fg_color=BG)
        win.grab_set()

        win.grid_columnconfigure((0, 1), weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text="⇄  Perbandingan Hasil",
                     font=("Segoe UI", 16, "bold"), text_color=ACCENT
                     ).grid(row=0, column=0, columnspan=2, pady=(20, 4))
        ctk.CTkLabel(win, text="Run 1 vs Run 2 — pilih yang terbaik untuk laporan",
                     font=("Segoe UI", 10), text_color=GRAY
                     ).grid(row=1, column=0, columnspan=2, pady=(0, 14))

        def _col(run, col, highlight=False):
            frame = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=10,
                                  border_width=1, border_color=BORDER)
            frame.grid(row=2, column=col, padx=12, pady=(0, 16), sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)

            label_color = GOLD if highlight else ACCENT
            header_f = ctk.CTkFrame(frame, fg_color="transparent")
            header_f.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
            ctk.CTkLabel(header_f, text=run["label"],
                         font=("Segoe UI", 18, "bold"), text_color=label_color
                         ).pack(side="left")
            if highlight:
                ctk.CTkLabel(header_f, text="★ LEBIH BAIK",
                             font=("Segoe UI", 10, "bold"), text_color=GOLD
                             ).pack(side="right")

            rows_data = [
                ("Inisialisasi",          run["init_method"]),
                ("Metaheuristik",         run["meta_method"]),
                ("2-Opt",                 "Ya" if run["two_opt"] else "Tidak"),
                ("", ""),
                ("Jarak Awal",            f"{run['init_dist']:.4f}"),
                ("Setelah Metaheuristik", f"{run['meta_dist']:.4f}" if run["meta_method"] != "—" else "—"),
                ("Jarak Final",           f"{run['final_dist']:.4f}"),
                ("Improvement",           f"{run['gain']:.4f}  ({run['pct']:.2f}%)"),
            ]
            for i, (lbl, val) in enumerate(rows_data):
                if lbl == "" and val == "":
                    ctk.CTkFrame(frame, height=1, fg_color=BORDER
                                 ).grid(row=i+1, column=0, padx=16, sticky="ew", pady=2)
                    continue
                row_f = ctk.CTkFrame(frame, fg_color="transparent")
                row_f.grid(row=i+1, column=0, padx=16, pady=2, sticky="ew")
                row_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(row_f, text=lbl + ":", font=("Segoe UI", 10),
                             text_color=GRAY, width=160, anchor="w"
                             ).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(row_f, text=val, font=("Segoe UI", 10, "bold"),
                             text_color=FG, anchor="w"
                             ).grid(row=0, column=1, sticky="w")

            route_str  = " → ".join(run["names"][i] for i in run["route"])
            route_str += f" → {run['names'][run['route'][0]]}"
            txt = ctk.CTkTextbox(frame, height=65, fg_color="#F8F8F8",
                                  text_color=FG, font=("Segoe UI", 9), wrap="word")
            txt.grid(row=len(rows_data)+1, column=0, padx=16, pady=(4, 16), sticky="ew")
            txt.insert("1.0", route_str)
            txt.configure(state="disabled")

        r1_better = r1["final_dist"] < r2["final_dist"]
        _col(r1, 0, highlight=r1_better)
        _col(r2, 1, highlight=(not r1_better))

        winner = r1 if r1_better else r2
        diff   = abs(r1["final_dist"] - r2["final_dist"])
        pct_d  = diff / max(r1["final_dist"], r2["final_dist"]) * 100
        ctk.CTkLabel(win,
                     text=f"🏆  {winner['label']} lebih unggul — selisih {diff:.4f} ({pct_d:.1f}%)",
                     font=("Segoe UI", 12, "bold"), text_color=GOLD
                     ).grid(row=3, column=0, columnspan=2, pady=(0, 20))

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )
        if not path:
            return
        try:
            if _has_export:
                export_results(path, self.cities, self.last_route,
                               self.last_dist, self.last_history, self.var_meta.get())
            else:
                raise ModuleNotFoundError("export tidak tersedia")
            messagebox.showinfo("Sukses", f"Hasil disimpan:\n{path}")
        except (ModuleNotFoundError, ImportError):
            csv_path = path.replace(".xlsx", ".csv") if path.endswith(".xlsx") else path
            self._export_csv(csv_path)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal export:\n{e}")

    def _export_csv(self, path: str):
        import csv
        names       = [c["name"] for c in self.cities]
        route_names = [names[i] for i in self.last_route]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Urutan", "Kota"])
            for idx, kota in enumerate(route_names, 1):
                w.writerow([idx, kota])
            w.writerow([])
            w.writerow(["Jarak Optimal", self.last_dist])
            w.writerow(["Metaheuristik", self.var_meta.get()])
        messagebox.showinfo("Sukses",
            f"Disimpan sebagai CSV (openpyxl belum ter-install):\n{path}")

    def _reset(self):
        self.cities       = None
        self.dist_matrix  = None
        self.last_route   = None
        self.last_dist    = None
        self.last_history = []
        self.init_dist    = None
        self.runs         = []

        self.file_label.configure(text="Belum ada data", text_color=SB_MUTED)

        # reset cards
        self.c_awal_val.configure(text="—"); self.c_awal_sub.configure(text="km")
        self.c_meta_val.configure(text="—"); self.c_meta_pct.configure(text="—")
        self.c_2opt_val.configure(text="—"); self.c_2opt_pct.configure(text="—")
        self.c_gain_val.configure(text="—"); self.c_gain_pct.configure(text="—")

        self.btn_export.configure(state="disabled")
        self.btn_compare.configure(state="disabled")
        self.lbl_run_count.configure(text="")
        self._status("")

        # reset route list
        for widget in self.route_scroll.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.route_scroll, text="Belum ada rute.",
                     font=("Segoe UI", 10), text_color=GRAY,
                     ).grid(row=0, column=0, padx=4, pady=8, sticky="w")

        # reset charts
        self.conv_ax.cla()
        self.conv_ax.set_facecolor("#FAFAFA")
        self.conv_fig.patch.set_facecolor(SURFACE)
        self.conv_ax.set_title("Jalankan algoritma dulu", color=GRAY, fontsize=8)
        self.conv_canvas.draw_idle()

        self.map_ax.cla()
        self.map_ax.set_facecolor("#F8F8F8")
        self.map_fig.patch.set_facecolor(SURFACE)
        self.map_ax.set_title("Pilih file dan jalankan algoritma", color=GRAY, fontsize=10)
        self.map_canvas.draw_idle()

    # ── helpers UI ─────────────────────────────────────────────────────────────

    def _dark_divider(self, parent, row):
        ctk.CTkFrame(parent, height=1, fg_color=DARK_BRD
                     ).grid(row=row, column=0, padx=14, sticky="ew", pady=(0, 8))

    def _style_ax(self, ax):
        ax.tick_params(colors=GRAY, labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

    def _status(self, msg: str):
        self.lbl_status.configure(text=msg)


if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()