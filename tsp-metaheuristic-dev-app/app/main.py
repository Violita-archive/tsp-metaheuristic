"""
app/main.py
Antarmuka utama aplikasi TSP Metaheuristic Optimizer.
Dibangun menggunakan CustomTkinter dan Matplotlib.
"""

import sys
import os
import random
import threading
import queue
import subprocess
import time

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

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from algorithms.sa import simulated_annealing, estimate_T0, iterations_to_Tmin
from algorithms.tabu import tabu_search
from algorithms.moves import MOVE_LABELS, MOVE_KEYS, all_moves, rotate_to_start
from algorithms.constructive import nearest_neighbor, farthest_insertion, random_route
from algorithms.two_opt import two_opt
from utils.loader import load_cities, get_coords, get_names
from utils.distance import distance_matrix
from utils.generator import (PATTERNS, generate_cities, circle_optimum,
                             write_template, save_cities)
from components.map_plot import plot_route, plot_points, rotate_to_depot
from components import report


# ── Palet warna: Mono + Signal Orange ────────────────────────────────────────
BG         = "#FFFFFF"
SURFACE    = "#FFFFFF"
SIDEBAR_BG = "#0A0A0A"
SB_FIELD   = "#1A1A1A"
ACCENT     = "#FF5A1F"
ACCENT_HV  = "#D94A10"
FG         = "#0A0A0A"
GRAY       = "#737373"
GOLD       = "#F59E0B"
GREEN_PCT  = "#22AA66"
BORDER     = "#E8E8E8"
DARK_BRD   = "#2A2A2A"
SB_FG      = "#CCCCCC"
SB_MUTED   = "#8A8A8A"
CARD_GAIN  = "#FFF4EF"
RUN_COLORS = ["#FF5A1F", "#2563EB", "#14A3A0", "#7C3AED", "#F59E0B",
              "#DB2777", "#0EA5E9", "#65A30D", "#78716C", "#DC2626"]

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# nilai default parameter (dapat diubah pengguna di sidebar)
SA_DEFAULT = {"T_start": "1000", "cooling_rate": "0.995", "T_min": "0.001",
              "max_iter": "10000", "iter_per_temp": "1", "stall_limit": "0"}
TS_DEFAULT = {"tabu_tenure": "", "max_iter": "500", "stall_limit": "0",
              "n_candidates": "0"}
MAX_RUNS = 20


# ══════════════════════════════════════════════════════════════════════════════
class TSPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TSP Metaheuristic Optimizer")
        self.geometry("1360x800")
        self.minsize(1100, 680)
        self.configure(fg_color=BG)

        self.cities = None
        self.dist_matrix = None     # list of list (lebih cepat untuk loop Python)
        self.data_source = ""
        self.runs = []
        self.run_counter = 0
        self.current_run = None
        self.map_mode = "Akhir"

        self._init_ttk_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # hasil dari thread pekerja diteruskan lewat antrian, lalu dieksekusi di thread utama
        self._ui_queue = queue.Queue()
        self._poll_queue()

    def _post(self, fn):
        self._ui_queue.put(fn)

    def _poll_queue(self):
        try:
            while True:
                self._ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.after(40, self._poll_queue)

    # ── layout dasar ─────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_panel()

    def _init_ttk_style(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TSP.Treeview", font=("Segoe UI", 9), rowheight=22,
                     background=SURFACE, fieldbackground=SURFACE, foreground=FG,
                     bordercolor=BORDER)
        st.configure("TSP.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                     background="#F3F3F3", foreground=FG, relief="flat")
        st.map("TSP.Treeview", background=[("selected", "#FFE3D6")],
               foreground=[("selected", FG)])
        st.configure("TSP.Horizontal.TProgressbar", troughcolor="#F0F0F0",
                     background=ACCENT, bordercolor=BORDER)

    # ── sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=310, fg_color=SIDEBAR_BG, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(1, weight=1)

        title_f = ctk.CTkFrame(sb, fg_color="transparent")
        title_f.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="w")
        ctk.CTkLabel(title_f, text="  TSP Optimizer", font=("Segoe UI", 16, "bold"),
                     text_color=SURFACE, image=self._dot_icon(), compound="left"
                     ).pack(side="left")

        body = ctk.CTkScrollableFrame(sb, fg_color=SIDEBAR_BG, corner_radius=0,
                                      scrollbar_button_color=DARK_BRD,
                                      scrollbar_button_hover_color="#3A3A3A")
        body.grid(row=1, column=0, sticky="nsew", padx=(4, 0))
        body.grid_columnconfigure(0, weight=1)
        self.sb_body = body

        self._build_data_section(body)
        self._build_algo_section(body)
        self._build_footer(sb)

    def _section(self, parent, text):
        ctk.CTkFrame(parent, height=1, fg_color=DARK_BRD).pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 9, "bold"),
                     text_color=SB_MUTED).pack(anchor="w", padx=14, pady=(8, 4))

    def _sb_entry(self, parent, default="", width=110, placeholder=""):
        e = ctk.CTkEntry(parent, width=width, height=28, fg_color=SB_FIELD,
                         border_color=DARK_BRD, text_color=SB_FG,
                         placeholder_text=placeholder, placeholder_text_color="#5A5A5A",
                         font=("Segoe UI", 10))
        if default != "":
            e.insert(0, str(default))
        return e

    def _sb_option(self, parent, values, variable, command=None, width=None):
        kw = dict(values=values, variable=variable, fg_color=SB_FIELD,
                  button_color=ACCENT, button_hover_color=ACCENT_HV,
                  text_color=SB_FG, dropdown_fg_color=SB_FIELD,
                  dropdown_text_color=SB_FG, dropdown_hover_color=DARK_BRD,
                  corner_radius=7, height=28, font=("Segoe UI", 10),
                  dynamic_resizing=False)
        if command:
            kw["command"] = command
        if width:
            kw["width"] = width
        return ctk.CTkOptionMenu(parent, **kw)

    def _sb_button(self, parent, text, command, primary=False, **kw):
        if primary:
            return ctk.CTkButton(parent, text=text, command=command, fg_color=ACCENT,
                                 text_color=SURFACE, hover_color=ACCENT_HV,
                                 font=("Segoe UI", 10, "bold"), corner_radius=7,
                                 height=30, **kw)
        return ctk.CTkButton(parent, text=text, command=command, fg_color="transparent",
                             text_color=SB_FG, border_color=DARK_BRD, border_width=1,
                             hover_color=SB_FIELD, font=("Segoe UI", 10),
                             corner_radius=7, height=28, **kw)

    def _sb_label(self, parent, text, muted=True, size=9):
        return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size),
                            text_color=SB_MUTED if muted else SB_FG,
                            justify="left", anchor="w")

    # ── bagian data ──────────────────────────────────────────────────────────
    def _build_data_section(self, body):
        ctk.CTkLabel(body, text="DATA KOTA", font=("Segoe UI", 9, "bold"),
                     text_color=SB_MUTED).pack(anchor="w", padx=14, pady=(2, 4))

        self.data_tab = ctk.CTkSegmentedButton(
            body, values=["Import", "Generate", "Manual"], command=self._switch_data_tab,
            fg_color=SB_FIELD, selected_color=ACCENT, selected_hover_color=ACCENT_HV,
            unselected_color=SB_FIELD, unselected_hover_color=DARK_BRD,
            text_color=SURFACE, font=("Segoe UI", 10), height=28)
        self.data_tab.pack(fill="x", padx=12, pady=(0, 6))
        self.data_tab.set("Import")

        holder = ctk.CTkFrame(body, fg_color="transparent")
        holder.pack(fill="x", padx=12)
        holder.grid_columnconfigure(0, weight=1)
        self.data_frames = {}

        # tab import
        f = ctk.CTkFrame(holder, fg_color="transparent")
        f.grid_columnconfigure((0, 1), weight=1)
        self._sb_button(f, "▲  Upload CSV / Excel", self._load_file, primary=True
                        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self._sb_button(f, "⬇ Template CSV", lambda: self._save_template(".csv")
                        ).grid(row=1, column=0, sticky="ew", padx=(0, 2))
        self._sb_button(f, "⬇ Template Excel", lambda: self._save_template(".xlsx")
                        ).grid(row=1, column=1, sticky="ew", padx=(2, 0))
        self._sb_label(f, "Kolom wajib: name, x, y (no opsional).\nBaris pertama = depot."
                       ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.data_frames["Import"] = f

        # tab generate
        f = ctk.CTkFrame(holder, fg_color="transparent")
        f.grid_columnconfigure((0, 1), weight=1)
        self.gen_n = self._sb_entry(f, "20")
        self.gen_seed = self._sb_entry(f, "", placeholder="kosong = acak")
        self.gen_x = self._sb_entry(f, "100")
        self.gen_y = self._sb_entry(f, "100")
        self.var_gen_pattern = ctk.StringVar(value="Uniform")
        for r, (lbl, w) in enumerate([("Jumlah titik", self.gen_n), ("Seed", self.gen_seed),
                                      ("X maks", self.gen_x), ("Y maks", self.gen_y)]):
            rr, cc = divmod(r, 2)
            self._sb_label(f, lbl).grid(row=rr * 2, column=cc, sticky="w", padx=2)
            w.grid(row=rr * 2 + 1, column=cc, sticky="ew", padx=2, pady=(0, 4))
        self._sb_label(f, "Pola sebaran").grid(row=4, column=0, sticky="w", padx=2)
        self._sb_option(f, PATTERNS, self.var_gen_pattern
                        ).grid(row=5, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 6))
        self._sb_button(f, "🎲  Generate", self._generate, primary=True
                        ).grid(row=6, column=0, sticky="ew", padx=(2, 2))
        self._sb_button(f, "💾 Simpan Data", self._save_data
                        ).grid(row=6, column=1, sticky="ew", padx=(2, 2))
        self._sb_label(f, "Pola Lingkaran punya jarak optimal yang diketahui\n"
                          "(keliling poligon) untuk validasi algoritma."
                       ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.data_frames["Generate"] = f

        # tab manual
        f = ctk.CTkFrame(holder, fg_color="transparent")
        f.grid_columnconfigure(0, weight=1)
        self._sb_button(f, "✏️  Buka Tabel Input Manual", self._input_manual, primary=True
                        ).grid(row=0, column=0, sticky="ew")
        self._sb_label(f, "Data yang sudah dimuat ikut ditampilkan\nsehingga bisa diedit."
                       ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.data_frames["Manual"] = f

        self._switch_data_tab("Import")

        self.file_label = ctk.CTkLabel(body, text="Belum ada data", font=("Segoe UI", 10),
                                       text_color=SB_MUTED, justify="left", anchor="w",
                                       wraplength=270)
        self.file_label.pack(anchor="w", fill="x", padx=14, pady=(8, 0))
        self.preview_label = ctk.CTkLabel(body, text="", font=("Consolas", 9),
                                          text_color=SB_MUTED, justify="left", anchor="w")
        self.preview_label.pack(anchor="w", fill="x", padx=14)

    def _switch_data_tab(self, name):
        for k, fr in self.data_frames.items():
            if k == name:
                fr.grid(row=0, column=0, sticky="ew")
            else:
                fr.grid_forget()

    # ── bagian algoritma ─────────────────────────────────────────────────────
    def _build_algo_section(self, body):
        self._section(body, "INISIALISASI RUTE")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", padx=12)
        row.grid_columnconfigure(0, weight=1)
        self.var_constructive = ctk.StringVar(value="Nearest Neighbor")
        self._sb_option(row, ["Nearest Neighbor", "Farthest Insertion", "Random"],
                        self.var_constructive).grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.seed_entry = self._sb_entry(row, "", width=86, placeholder="acak")
        self.seed_entry.grid(row=1, column=1)
        self._sb_label(row, "Metode").grid(row=0, column=0, sticky="w")
        self._sb_label(row, "Seed").grid(row=0, column=1, sticky="w")
        self._sb_label(body, "Seed dipakai untuk Random, SA, dan sampling kandidat Tabu.\n"
                             "Kosong = acak (seed yang terpakai tetap dicatat)."
                       ).pack(anchor="w", padx=14, pady=(2, 0))

        self._section(body, "METAHEURISTIK")
        self.var_use_meta = ctk.BooleanVar(value=True)
        self.meta_check = ctk.CTkCheckBox(body, text="Gunakan metaheuristik", variable=self.var_use_meta,
                        text_color=SB_FG, fg_color=ACCENT, hover_color=ACCENT_HV,
                        checkmark_color=SURFACE, font=("Segoe UI", 10),
                        border_color=DARK_BRD, command=self._toggle_meta_section,
                        checkbox_width=18, checkbox_height=18)
        self.meta_check.pack(anchor="w", padx=14, pady=(0, 6))

        self.meta_box = ctk.CTkFrame(body, fg_color="transparent")
        self.meta_box.pack(fill="x", padx=12)
        self.meta_box.grid_columnconfigure(0, weight=1)
        self.var_meta = ctk.StringVar(value="Simulated Annealing")
        self._sb_option(self.meta_box, ["Simulated Annealing", "Tabu Search"],
                        self.var_meta, command=lambda _v: self._switch_param_frame()
                        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.param_holder = ctk.CTkFrame(self.meta_box, fg_color="#121212",
                                         border_color=DARK_BRD, border_width=1,
                                         corner_radius=8)
        self.param_holder.grid(row=1, column=0, sticky="ew")
        self.param_holder.grid_columnconfigure(0, weight=1)
        self._build_sa_params(self.param_holder)
        self._build_ts_params(self.param_holder)
        self._switch_param_frame()

        self._section(body, "LOCAL SEARCH")
        self.var_two_opt = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(body, text="Terapkan 2-Opt setelahnya", variable=self.var_two_opt,
                        text_color=SB_FG, fg_color=ACCENT, hover_color=ACCENT_HV,
                        checkmark_color=SURFACE, font=("Segoe UI", 10),
                        border_color=DARK_BRD, checkbox_width=18, checkbox_height=18
                        ).pack(anchor="w", padx=14, pady=(0, 12))

    def _param_grid(self, parent, spec, store):
        """spec: list (key, label, default). Entry disusun dua kolom."""
        g = ctk.CTkFrame(parent, fg_color="transparent")
        g.grid_columnconfigure((0, 1), weight=1)
        for k, (key, label, default, ph) in enumerate(spec):
            rr, cc = divmod(k, 2)
            self._sb_label(g, label).grid(row=rr * 2, column=cc, sticky="w", padx=3)
            e = self._sb_entry(g, default, placeholder=ph)
            e.grid(row=rr * 2 + 1, column=cc, sticky="ew", padx=3, pady=(0, 4))
            e.bind("<KeyRelease>", lambda _e: self._update_param_hint())
            store[key] = e
        return g

    def _build_sa_params(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f, text="Parameter SA", font=("Segoe UI", 9, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))
        self.sa_entries = {}
        spec = [("T_start", "Suhu awal T₀", SA_DEFAULT["T_start"], ""),
                ("cooling_rate", "Cooling rate α", SA_DEFAULT["cooling_rate"], ""),
                ("T_min", "Suhu minimum", SA_DEFAULT["T_min"], ""),
                ("max_iter", "Iterasi maks", SA_DEFAULT["max_iter"], ""),
                ("iter_per_temp", "Iterasi per suhu (L)", SA_DEFAULT["iter_per_temp"], ""),
                ("stall_limit", "Stop jika stagnan", SA_DEFAULT["stall_limit"], "0 = off")]
        self._param_grid(f, spec, self.sa_entries).grid(row=1, column=0, sticky="ew", padx=5)

        self.var_sa_move = ctk.StringVar(value="Swap")
        mv = ctk.CTkFrame(f, fg_color="transparent")
        mv.grid(row=2, column=0, sticky="ew", padx=8)
        mv.grid_columnconfigure(1, weight=1)
        self._sb_label(mv, "Move operator").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._sb_option(mv, list(MOVE_LABELS.values()), self.var_sa_move,
                        command=lambda _v: self._update_param_hint()
                        ).grid(row=0, column=1, sticky="ew")

        bt = ctk.CTkFrame(f, fg_color="transparent")
        bt.grid(row=3, column=0, sticky="ew", padx=8, pady=(6, 2))
        bt.grid_columnconfigure((0, 1), weight=1)
        self._sb_button(bt, "T₀ otomatis", self._auto_T0).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self._sb_button(bt, "↺ Default", lambda: self._reset_params("sa")
                        ).grid(row=0, column=1, sticky="ew", padx=(2, 0))
        self.sa_hint = self._sb_label(f, "")
        self.sa_hint.configure(wraplength=240)
        self.sa_hint.grid(row=4, column=0, sticky="w", padx=8, pady=(2, 8))
        self.sa_frame = f

    def _build_ts_params(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f, text="Parameter Tabu Search", font=("Segoe UI", 9, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))
        self.ts_entries = {}
        spec = [("tabu_tenure", "Tabu tenure", TS_DEFAULT["tabu_tenure"], "auto"),
                ("max_iter", "Iterasi maks", TS_DEFAULT["max_iter"], ""),
                ("stall_limit", "Stop jika stagnan", TS_DEFAULT["stall_limit"], "0 = off"),
                ("n_candidates", "Jumlah kandidat", TS_DEFAULT["n_candidates"], "0 = semua")]
        self._param_grid(f, spec, self.ts_entries).grid(row=1, column=0, sticky="ew", padx=5)

        self.var_ts_move = ctk.StringVar(value="Swap")
        mv = ctk.CTkFrame(f, fg_color="transparent")
        mv.grid(row=2, column=0, sticky="ew", padx=8)
        mv.grid_columnconfigure(1, weight=1)
        self._sb_label(mv, "Move operator").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._sb_option(mv, list(MOVE_LABELS.values()), self.var_ts_move,
                        command=lambda _v: self._update_param_hint()
                        ).grid(row=0, column=1, sticky="ew")

        self.var_aspiration = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(f, text="Aspiration criterion", variable=self.var_aspiration,
                        text_color=SB_FG, fg_color=ACCENT, hover_color=ACCENT_HV,
                        checkmark_color=SURFACE, font=("Segoe UI", 10),
                        border_color=DARK_BRD, checkbox_width=16, checkbox_height=16
                        ).grid(row=3, column=0, sticky="w", padx=8, pady=(6, 0))
        self._sb_button(f, "↺ Default", lambda: self._reset_params("ts")
                        ).grid(row=4, column=0, sticky="ew", padx=8, pady=(6, 2))
        self.ts_hint = self._sb_label(f, "")
        self.ts_hint.configure(wraplength=240)
        self.ts_hint.grid(row=5, column=0, sticky="w", padx=8, pady=(2, 8))
        self.ts_frame = f

    def _build_footer(self, sb):
        foot = ctk.CTkFrame(sb, fg_color=SIDEBAR_BG, corner_radius=0)
        foot.grid(row=2, column=0, sticky="ew")
        foot.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkFrame(foot, height=1, fg_color=DARK_BRD).grid(row=0, column=0, columnspan=3,
                                                            sticky="ew", pady=(0, 8))
        self.pipe_label = ctk.CTkLabel(foot, text="", font=("Segoe UI", 9),
                                       text_color=SB_FG, wraplength=280)
        self.pipe_label.grid(row=1, column=0, columnspan=3, padx=14, sticky="w")

        self.btn_run = ctk.CTkButton(foot, text="▶  JALANKAN", fg_color=ACCENT,
                                     text_color=SURFACE, hover_color=ACCENT_HV,
                                     font=("Segoe UI", 14, "bold"), height=44,
                                     corner_radius=8, command=self._run)
        self.btn_run.grid(row=2, column=0, columnspan=3, padx=12, pady=(4, 6), sticky="ew")

        self.btn_export = self._sb_button(foot, "⬇ Export", self._export_menu, state="disabled")
        self.btn_export.grid(row=3, column=0, padx=(12, 2), sticky="ew")
        self.btn_compare = self._sb_button(foot, "⇄ Bandingkan", self._compare, state="disabled")
        self.btn_compare.configure(text_color=GOLD)
        self.btn_compare.grid(row=3, column=1, padx=2, sticky="ew")
        self.btn_log = self._sb_button(foot, "☰ Log", self._show_log, state="disabled")
        self.btn_log.grid(row=3, column=2, padx=(2, 12), sticky="ew")

        self._sb_button(foot, "📊 Analisis Parameter", self._param_analysis
                        ).grid(row=4, column=0, columnspan=2, padx=(12, 2), pady=(4, 0), sticky="ew")
        self._sb_button(foot, "↺ Reset", self._reset
                        ).grid(row=4, column=2, padx=(2, 12), pady=(4, 0), sticky="ew")

        self.lbl_run_count = ctk.CTkLabel(foot, text="", font=("Segoe UI", 9),
                                          text_color=SB_MUTED, wraplength=280, justify="left")
        self.lbl_run_count.grid(row=5, column=0, columnspan=3, padx=14, pady=(4, 0), sticky="w")
        self.lbl_status = ctk.CTkLabel(foot, text="", font=("Segoe UI", 10),
                                       text_color=SB_FG, wraplength=280, justify="left")
        self.lbl_status.grid(row=6, column=0, columnspan=3, padx=14, pady=(0, 10), sticky="w")
        for v in (self.var_constructive, self.var_two_opt, self.var_use_meta, self.var_meta,
                  self.var_sa_move, self.var_ts_move):
            v.trace_add("write", lambda *_: self._update_param_hint())
        self._update_param_hint()

    def _dot_icon(self):
        img = tk.PhotoImage(width=14, height=14)
        img.put(ACCENT, to=(0, 0, 14, 14))
        self._icon_ref = img
        return img

    # ── panel utama ──────────────────────────────────────────────────────────
    def _build_main_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BG)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(panel, fg_color=BG)
        content.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, minsize=280)

        map_frame = ctk.CTkFrame(content, fg_color=SURFACE, border_width=1,
                                 border_color=BORDER, corner_radius=10)
        map_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        map_frame.grid_rowconfigure(1, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(map_frame, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text="Peta Rute", font=("Segoe UI", 12, "bold"),
                     text_color=FG).grid(row=0, column=0, sticky="w")
        self.map_toggle = ctk.CTkSegmentedButton(
            head, values=["Akhir", "Awal", "Keduanya"], command=self._set_map_mode,
            selected_color=ACCENT, selected_hover_color=ACCENT_HV,
            unselected_color="#F1F1F1", unselected_hover_color="#E5E5E5",
            text_color=FG, font=("Segoe UI", 10), height=26)
        self.map_toggle.set("Akhir")
        self.map_toggle.grid(row=0, column=2, sticky="e", padx=(0, 6))
        ctk.CTkButton(head, text="📷", width=32, height=26, fg_color="#F1F1F1",
                      text_color=FG, hover_color="#E5E5E5", command=self._export_png
                      ).grid(row=0, column=3, sticky="e")

        fig, ax = plt.subplots(figsize=(6.5, 4.8), facecolor=SURFACE)
        ax.set_facecolor("#F8F8F8")
        ax.set_title("Muat / generate data lalu jalankan algoritma", color=GRAY, fontsize=10)
        self.map_fig, self.map_ax = fig, ax
        self.map_canvas = FigureCanvasTkAgg(fig, master=map_frame)
        self.map_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self._build_right_panel(right)

    def _build_right_panel(self, parent):
        stats = ctk.CTkFrame(parent, fg_color=SURFACE, border_width=1,
                             border_color=BORDER, corner_radius=10)
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        stats.grid_columnconfigure((0, 1), weight=1)
        self.lbl_run_title = ctk.CTkLabel(stats, text="HASIL OPTIMASI",
                                          font=("Segoe UI", 9, "bold"), text_color=GRAY)
        self.lbl_run_title.grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        def card(row, col, title, val_color=FG, sub_color=GREEN_PCT, accent=False):
            f = ctk.CTkFrame(stats, fg_color=CARD_GAIN if accent else SURFACE,
                             border_width=1, border_color="#FFD5C0" if accent else BORDER,
                             corner_radius=8)
            f.grid(row=row, column=col, padx=(8 if col == 0 else 4, 4 if col == 0 else 8),
                   pady=(0, 8), sticky="nsew")
            ctk.CTkLabel(f, text=title, font=("Segoe UI", 9), text_color=GRAY
                         ).pack(anchor="w", padx=9, pady=(7, 1))
            v = ctk.CTkLabel(f, text="—", font=("Segoe UI", 14, "bold"), text_color=val_color)
            v.pack(anchor="w", padx=9)
            s = ctk.CTkLabel(f, text="", font=("Segoe UI", 9), text_color=sub_color)
            s.pack(anchor="w", padx=9, pady=(0, 7))
            return v, s

        self.c_awal_val, self.c_awal_sub = card(1, 0, "Jarak Awal", sub_color=GRAY)
        self.c_meta_val, self.c_meta_pct = card(1, 1, "Hasil Metaheuristik")
        self.c_2opt_val, self.c_2opt_pct = card(2, 0, "Setelah 2-Opt")
        self.c_gain_val, self.c_gain_pct = card(2, 1, "Total Gain", val_color=ACCENT,
                                                sub_color=ACCENT, accent=True)
        self.lbl_run_info = ctk.CTkLabel(stats, text="", font=("Segoe UI", 9),
                                         text_color=GRAY, justify="left", anchor="w",
                                         wraplength=260)
        self.lbl_run_info.grid(row=3, column=0, columnspan=2, padx=12, pady=(0, 10), sticky="w")

        conv = ctk.CTkFrame(parent, fg_color=SURFACE, border_width=1,
                            border_color=BORDER, corner_radius=10)
        conv.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        conv.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(conv, text="KONVERGENSI", font=("Segoe UI", 9, "bold"),
                     text_color=GRAY).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")
        fig2, ax2 = plt.subplots(figsize=(3.4, 1.9), facecolor=SURFACE)
        ax2.set_facecolor("#FAFAFA")
        ax2.set_title("Jalankan algoritma dulu", color=GRAY, fontsize=8)
        ax2.set_axis_off()
        self.conv_fig, self.conv_ax = fig2, ax2
        self.conv_canvas = FigureCanvasTkAgg(fig2, master=conv)
        self.conv_canvas.get_tk_widget().grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        route_frame = ctk.CTkFrame(parent, fg_color=SURFACE, border_width=1,
                                   border_color=BORDER, corner_radius=10)
        route_frame.grid(row=2, column=0, sticky="nsew")
        route_frame.grid_rowconfigure(1, weight=1)
        route_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(route_frame, text="URUTAN RUTE", font=("Segoe UI", 9, "bold"),
                     text_color=GRAY).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")
        self.route_box = ctk.CTkTextbox(route_frame, fg_color=SURFACE, text_color=FG,
                                        font=("Consolas", 10), wrap="none",
                                        activate_scrollbars=True)
        self.route_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._set_route_text("Belum ada rute.")

    # ── handler: data ────────────────────────────────────────────────────────
    def _set_cities(self, cities, source):
        coords = get_coords(cities)
        self.cities = cities
        self.dist_matrix = np.asarray(distance_matrix(coords)).tolist()
        self.data_source = source
        self.runs = []
        self.run_counter = 0
        self.current_run = None
        self.file_label.configure(text=f"✓ {source}\n{len(cities)} kota dimuat · depot: "
                                       f"{cities[0]['name']}", text_color=ACCENT)
        lines = [f"{'#':>3} {'name':<12}{'x':>8}{'y':>8}"]
        for c in cities[:5]:
            lines.append(f"{c['no']:>3} {c['name'][:12]:<12}{c['x']:>8.2f}{c['y']:>8.2f}")
        if len(cities) > 5:
            lines.append(f"    + {len(cities) - 5} kota lainnya")
        self.preview_label.configure(text="\n".join(lines))
        self._clear_results()
        self._draw_points()
        self._update_run_counter()
        self._update_param_hint()
        self._status(f"{len(cities)} kota siap diproses")

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Pilih file kota",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Semua", "*.*")])
        if not path:
            return
        try:
            self._set_cities(load_cities(path), os.path.basename(path))
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca file:\n{e}")

    def _save_template(self, ext):
        path = filedialog.asksaveasfilename(defaultextension=ext,
                                            initialfile=f"template_tsp{ext}",
                                            filetypes=[("Template", f"*{ext}")])
        if path:
            try:
                write_template(path)
                self._status(f"Template disimpan: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan template:\n{e}")

    def _generate(self):
        try:
            n = int(self.gen_n.get())
            if not 3 <= n <= 1000:
                raise ValueError("Jumlah titik harus 3 - 1000.")
            s = self.gen_seed.get().strip()
            seed = int(s) if s else random.randint(0, 99999)
            xm, ym = float(self.gen_x.get()), float(self.gen_y.get())
            if xm <= 0 or ym <= 0:
                raise ValueError("X maks dan Y maks harus > 0.")
        except ValueError as e:
            messagebox.showwarning("Input tidak valid", str(e) if "harus" in str(e)
                                   else "Isi jumlah titik, seed, X maks, Y maks dengan angka.")
            return
        pat = self.var_gen_pattern.get()
        cities = generate_cities(n, seed, pat, xm, ym)
        self.gen_meta = {"pattern": pat, "seed": seed, "x_max": xm, "y_max": ym}
        self._set_cities(cities, f"Generate {pat} (seed {seed})")
        if pat == "Lingkaran":
            self._status(f"Jarak optimal teoretis: {circle_optimum(n, xm, ym):.4f}")

    def _save_data(self):
        if self.cities is None:
            messagebox.showinfo("Info", "Belum ada data untuk disimpan.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile="data_kota.csv",
                                            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")])
        if path:
            save_cities(path, self.cities)
            self._status(f"Data disimpan: {os.path.basename(path)}")

    def _input_manual(self):
        win = ctk.CTkToplevel(self)
        win.title("Input Data Kota Manual")
        win.geometry("560x580")
        win.configure(fg_color=BG)
        win.transient(self)
        win.after(100, win.grab_set)
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text="✏️  Input Data Kota Manual", font=("Segoe UI", 15, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, pady=(18, 2), padx=20, sticky="w")
        ctk.CTkLabel(win, text="Isi nama kota beserta koordinat X dan Y. Baris pertama = depot.\n"
                               "Baris kosong diabaikan.",
                     font=("Segoe UI", 10), text_color=GRAY, justify="left"
                     ).grid(row=1, column=0, pady=(0, 10), padx=20, sticky="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color=SURFACE, border_width=1, border_color=BORDER)
        scroll.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="nsew")
        for col, (txt, w) in enumerate([("No", 40), ("Nama Kota", 180), ("X", 90), ("Y", 90)]):
            ctk.CTkLabel(scroll, text=txt, font=("Segoe UI", 10, "bold"), text_color=GRAY,
                         width=w).grid(row=0, column=col, padx=4, pady=(4, 6))
        entries = []

        def _add_row(name="", x="", y=""):
            r = len(entries) + 1
            ctk.CTkLabel(scroll, text=str(r), font=("Segoe UI", 10), text_color=GRAY,
                         width=40).grid(row=r, column=0, padx=4, pady=2)
            es = []
            for col, (ph, w, val) in enumerate([("Nama kota", 180, name), ("X", 90, x),
                                                ("Y", 90, y)], start=1):
                e = ctk.CTkEntry(scroll, placeholder_text=ph, fg_color=SURFACE,
                                 border_color=BORDER, text_color=FG,
                                 font=("Segoe UI", 10), width=w)
                e.grid(row=r, column=col, padx=4, pady=2)
                if val != "":
                    e.insert(0, str(val))
                es.append(e)
            entries.append(tuple(es))

        if self.cities:
            for c in self.cities:
                _add_row(c["name"], c["x"], c["y"])
        else:
            _add_row("Surabaya", 0, 0)
            _add_row("Sidoarjo", 20, 15)
            _add_row("Malang", 90, 45)
        for _ in range(3):
            _add_row()

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btn_frame, text="+ Tambah Baris", fg_color=SURFACE, text_color=ACCENT,
                      border_color=ACCENT, border_width=1, hover_color=CARD_GAIN,
                      font=("Segoe UI", 10), command=_add_row
                      ).grid(row=0, column=0, padx=(0, 4), sticky="ew")

        def _use_data():
            cities = []
            for i, (e_name, e_x, e_y) in enumerate(entries):
                name, xs, ys = e_name.get().strip(), e_x.get().strip(), e_y.get().strip()
                if not name and not xs and not ys:
                    continue
                if not name or not xs or not ys:
                    messagebox.showwarning("Data tidak lengkap",
                                           f"Baris {i+1}: isi semua kolom (nama, X, Y).", parent=win)
                    return
                try:
                    cities.append({"no": len(cities) + 1, "name": name,
                                   "x": float(xs), "y": float(ys)})
                except ValueError:
                    messagebox.showwarning("Format salah", f"Baris {i+1}: X dan Y harus angka.",
                                           parent=win)
                    return
            if len(cities) < 3:
                messagebox.showwarning("Kurang kota", "Minimal 3 kota untuk TSP.", parent=win)
                return
            win.destroy()
            self._set_cities(cities, "Input manual")

        ctk.CTkButton(btn_frame, text="✓  Gunakan Data Ini", fg_color=ACCENT, text_color=SURFACE,
                      hover_color=ACCENT_HV, font=("Segoe UI", 11, "bold"), command=_use_data
                      ).grid(row=0, column=1, padx=(4, 0), sticky="ew")

    # ── handler: parameter ───────────────────────────────────────────────────
    def _toggle_meta_section(self):
        if self.var_use_meta.get():
            self.meta_box.pack(fill="x", padx=12, after=self.meta_check)
        else:
            self.meta_box.pack_forget()
        self._update_param_hint()

    def _switch_param_frame(self):
        if self.var_meta.get() == "Simulated Annealing":
            self.ts_frame.grid_forget()
            self.sa_frame.grid(row=0, column=0, sticky="ew")
        else:
            self.sa_frame.grid_forget()
            self.ts_frame.grid(row=0, column=0, sticky="ew")
        self._update_param_hint()

    def _reset_params(self, which):
        entries, defaults = ((self.sa_entries, SA_DEFAULT) if which == "sa"
                             else (self.ts_entries, TS_DEFAULT))
        for k, e in entries.items():
            e.delete(0, "end")
            if defaults[k] != "":
                e.insert(0, defaults[k])
        if which == "sa":
            self.var_sa_move.set("Swap")
        else:
            self.var_ts_move.set("Swap")
            self.var_aspiration.set(True)
        self._update_param_hint()

    def _auto_T0(self):
        if self.cities is None:
            messagebox.showinfo("Info", "Muat data kota terlebih dahulu.")
            return
        move = MOVE_KEYS[self.var_sa_move.get()]
        route = list(range(len(self.cities)))
        T0 = estimate_T0(self.dist_matrix, route, move, p0=0.8, seed=0)
        e = self.sa_entries["T_start"]
        e.delete(0, "end")
        e.insert(0, f"{T0:.4g}")
        self._update_param_hint()
        self._status(f"T₀ = {T0:.4g}: peluang awal menerima solusi lebih buruk ≈ 0.8 "
                     f"(dari rata-rata Δ positif {MOVE_LABELS[move]}).")

    def _update_param_hint(self):
        try:
            p = {k: float(e.get()) for k, e in self.sa_entries.items()}
            k = iterations_to_Tmin(p["T_start"], p["T_min"], p["cooling_rate"],
                                   p["iter_per_temp"])
            if p["T_min"] == 0 and 0 < p["cooling_rate"] < 1:
                txt = (f"T_min = 0: berhenti oleh iterasi maks ({int(p['max_iter']):,}) "
                       f"atau kriteria stagnan.")
            elif k is None:
                txt = "Cek nilai: 0 < α < 1 dan T₀ > T_min > 0."
            else:
                mx = int(p["max_iter"])
                stop = "T_min" if k <= mx else "iterasi maks"
                txt = (f"T mencapai T_min setelah ±{k:,} iterasi → berhenti karena {stop} "
                       f"(±{min(k, mx):,} iterasi). Suhu akhir ≈ "
                       f"{p['T_start'] * p['cooling_rate'] ** (min(k, mx) / max(1, p['iter_per_temp'])):.3g}.")
        except (ValueError, ZeroDivisionError, OverflowError):
            txt = "Isi semua parameter dengan angka."
        self.sa_hint.configure(text=txt)

        n = len(self.cities) if self.cities else None
        move = MOVE_KEYS[self.var_ts_move.get()]
        if n:
            auto = max(5, n // 2)
            nb = len(all_moves(n, move))
            t = self.ts_entries["tabu_tenure"].get().strip()
            self.ts_hint.configure(text=f"N = {n} kota → tenure auto = max(5, N/2) = {auto}"
                                        f"{'' if not t else f' (dipakai: {t})'}. "
                                        f"Neighbor {MOVE_LABELS[move]} per iterasi: {nb:,}.")
        else:
            self.ts_hint.configure(text="Tenure kosong = auto, max(5, N/2).")
        self._update_pipe_label()

    def _update_pipe_label(self, *_):
        if not hasattr(self, "pipe_label"):
            return
        parts = [{"Nearest Neighbor": "NN", "Farthest Insertion": "FI"}.get(
            self.var_constructive.get(), "Random")]
        if self.var_use_meta.get():
            sa = self.var_meta.get() == "Simulated Annealing"
            parts.append(f"{'SA' if sa else 'Tabu'} ({(self.var_sa_move if sa else self.var_ts_move).get()})")
        if self.var_two_opt.get():
            parts.append("2-Opt")
        self.pipe_label.configure(text="Pipeline: " + " → ".join(parts))

    def _parse_seed(self):
        s = self.seed_entry.get().strip()
        if not s:
            return random.randint(0, 99999)
        return int(s)

    def _read_config(self):
        """Membaca seluruh pengaturan sidebar. ValueError jika tidak valid."""
        cfg = {"init": self.var_constructive.get(), "use_meta": self.var_use_meta.get(),
               "meta": self.var_meta.get() if self.var_use_meta.get() else "—",
               "two_opt": self.var_two_opt.get()}
        try:
            cfg["seed"] = self._parse_seed()
        except ValueError:
            raise ValueError("Seed harus bilangan bulat.")
        if cfg["meta"] == "Simulated Annealing":
            try:
                p = {k: float(e.get()) for k, e in self.sa_entries.items()}
            except ValueError:
                raise ValueError("Semua parameter SA harus berupa angka.")
            if not 0 < p["cooling_rate"] < 1:
                raise ValueError("Cooling rate α harus di antara 0 dan 1.")
            if p["T_start"] <= 0 or p["T_min"] < 0:
                raise ValueError("Suhu awal harus > 0 dan suhu minimum ≥ 0.")
            if p["max_iter"] < 1 or p["iter_per_temp"] < 1 or p["stall_limit"] < 0:
                raise ValueError("Iterasi maks dan L minimal 1, stagnan ≥ 0.")
            cfg["move"] = self.var_sa_move.get()
            cfg["sa"] = dict(T_start=p["T_start"], cooling_rate=p["cooling_rate"],
                             T_min=p["T_min"], max_iter=int(p["max_iter"]),
                             iter_per_temp=int(p["iter_per_temp"]),
                             stall_limit=int(p["stall_limit"]))
        elif cfg["meta"] == "Tabu Search":
            try:
                t = self.ts_entries["tabu_tenure"].get().strip()
                tenure = int(t) if t else None
                mx = int(self.ts_entries["max_iter"].get())
                stall = int(self.ts_entries["stall_limit"].get() or 0)
                cand = int(self.ts_entries["n_candidates"].get() or 0)
            except ValueError:
                raise ValueError("Parameter Tabu harus bilangan bulat (tenure boleh kosong).")
            if (tenure is not None and tenure < 1) or mx < 1 or stall < 0 or cand < 0:
                raise ValueError("Tenure & iterasi maks minimal 1; stagnan & kandidat ≥ 0.")
            cfg["move"] = self.var_ts_move.get()
            cfg["ts"] = dict(tabu_tenure=tenure, max_iter=mx, stall_limit=stall,
                             n_candidates=cand, aspiration=self.var_aspiration.get())
        else:
            cfg["move"] = "-"
        return cfg

    # ── eksekusi ─────────────────────────────────────────────────────────────
    def _run(self):
        if self.cities is None:
            messagebox.showwarning("Perhatian", "Muat, generate, atau input data kota dulu!")
            return
        try:
            cfg = self._read_config()
        except ValueError as e:
            messagebox.showwarning("Parameter tidak valid", str(e))
            return
        self.btn_run.configure(state="disabled", text="⏳  Memproses...")
        self._status("Menghitung rute...")
        threading.Thread(target=self._pipeline_thread, args=(cfg,), daemon=True).start()

    def _pipeline_thread(self, cfg):
        try:
            run = run_pipeline(self.dist_matrix, get_names(self.cities), cfg)
            self._post(lambda: self._on_run_done(run))
        except Exception as e:
            msg = str(e)
            self._post(lambda: messagebox.showerror("Error", f"Terjadi kesalahan:\n{msg}"))
            self._post(lambda: self.btn_run.configure(state="normal", text="▶  JALANKAN"))

    def _on_run_done(self, run):
        self.run_counter += 1
        run["label"] = f"Run {self.run_counter}"
        run["color"] = RUN_COLORS[(self.run_counter - 1) % len(RUN_COLORS)]
        self.runs.append(run)
        if len(self.runs) > MAX_RUNS:
            self.runs.pop(0)
        self._display_run(run)
        self._update_run_counter()
        self.btn_run.configure(state="normal", text="▶  JALANKAN")
        for b in (self.btn_export, self.btn_log):
            b.configure(state="normal")
        self._status(f"Selesai: jarak final {run['final_dist']:.4f} "
                     f"({run['time']:.3f} s)")

    def _display_run(self, run):
        self.current_run = run
        init, meta, final = run["init_dist"], run["meta_dist"], run["final_dist"]
        self.lbl_run_title.configure(text=f"HASIL OPTIMASI · {run['label'].upper()}")
        self.c_awal_val.configure(text=f"{init:,.2f}")
        self.c_awal_sub.configure(text=run["init_method"])
        if run["meta_method"] != "—":
            mp = (init - meta) / init * 100 if init else 0
            self.c_meta_val.configure(text=f"{meta:,.2f}")
            short = "SA" if run["meta_method"] == "Simulated Annealing" else "Tabu"
            self.c_meta_pct.configure(text=f"−{mp:.2f}% · {short} ({run['move']})")
        else:
            self.c_meta_val.configure(text="—")
            self.c_meta_pct.configure(text="tidak dipakai")
        if run["two_opt"]:
            op = (meta - final) / meta * 100 if meta else 0
            self.c_2opt_val.configure(text=f"{final:,.2f}")
            self.c_2opt_pct.configure(text=f"−{op:.2f}%")
        else:
            self.c_2opt_val.configure(text="—")
            self.c_2opt_pct.configure(text="tidak dipakai")
        self.c_gain_val.configure(text=f"−{run['pct']:.2f}%")
        self.c_gain_pct.configure(text=f"−{run['gain']:,.2f}")
        self.lbl_run_info.configure(
            text=f"Iterasi: {run['iterations']:,} · Waktu: {run['time']:.3f} s\n"
                 f"Berhenti: {run['stop_reason']}\n"
                 f"Parameter: {report.params_text(run['params'])}")
        self._draw_map()
        self._draw_conv(run)
        self._update_route_list(run)

    def _update_route_list(self, run):
        d = self.dist_matrix
        r = rotate_to_depot(run["final_route"])
        closed = r + [r[0]]
        lines, total = [], 0.0
        for k, c in enumerate(closed):
            step = d[closed[k - 1]][c] if k else 0.0
            total += step
            lines.append(f"{k+1:>3}. {self.cities[c]['name'][:16]:<16} "
                         f"{('—' if k == 0 else f'{step:,.2f}'):>9}  {total:>10,.2f}")
        head = f"{'':>4} {'Kota':<16} {'Jarak':>9}  {'Kumulatif':>10}\n"
        self._set_route_text(head + "\n".join(lines))

    def _set_route_text(self, txt):
        self.route_box.configure(state="normal")
        self.route_box.delete("1.0", "end")
        self.route_box.insert("1.0", txt)
        self.route_box.configure(state="disabled")

    def _update_run_counter(self):
        n = len(self.runs)
        if n == 0:
            self.lbl_run_count.configure(text="")
        elif n == 1:
            self.lbl_run_count.configure(text="1 run tersimpan. Ganti metode/parameter lalu "
                                              "jalankan lagi untuk membandingkan.",
                                         text_color=SB_MUTED)
        else:
            self.lbl_run_count.configure(text=f"{n} run tersimpan · klik Bandingkan.",
                                         text_color=GOLD)
        self.btn_compare.configure(state="normal" if n >= 2 else "disabled")

    # ── gambar ───────────────────────────────────────────────────────────────
    def _set_map_mode(self, mode):
        self.map_mode = mode
        self._draw_map()

    def _draw_points(self):
        coords, names = get_coords(self.cities), get_names(self.cities)
        plot_points(coords, names, title="Data Kota",
                    subtitle=f"{len(coords)} kota · {self.data_source}", ax=self.map_ax)
        self.map_fig.tight_layout()
        self.map_canvas.draw_idle()

    def _draw_map(self):
        run = self.current_run
        if self.cities is None:
            return
        if run is None:
            self._draw_points()
            return
        coords, names = get_coords(self.cities), get_names(self.cities)
        sub = f"{report.pipeline_text(run)} · {run['label']}"
        if self.map_mode == "Awal":
            plot_route(coords, names, run["init_route"], ax=self.map_ax,
                       title=f"Rute Awal ({run['init_method']}) · {run['init_dist']:,.2f}",
                       subtitle=sub)
        else:
            plot_route(coords, names, run["final_route"], ax=self.map_ax,
                       initial_route=run["init_route"] if self.map_mode == "Keduanya" else None,
                       title=f"Rute Akhir · {run['final_dist']:,.2f}", subtitle=sub)
        self.map_fig.tight_layout()
        self.map_canvas.draw_idle()

    def _draw_conv(self, run):
        ax = self.conv_ax
        ax.clear()
        ax.set_facecolor("#FAFAFA")
        h = run["history"]
        if not h:
            ax.set_title("Tidak ada data konvergensi", color=GRAY, fontsize=8)
            self._style_ax(ax)
            self.conv_canvas.draw_idle()
            return
        h = _downsample(h, 2500)
        it = [x["iter"] for x in h]
        ax.plot(it, [x["current_dist"] for x in h], color="#B5B5B5", lw=0.8, label="current")
        ax.plot(it, [x["best_dist"] for x in h], color=ACCENT, lw=2, label="best")
        b0, b1 = h[0]["best_dist"], h[-1]["best_dist"]
        pct = f" · −{(b0 - b1) / b0 * 100:.1f}%" if b0 else ""
        ax.set_title(f"{run['meta_method']} · {run['move']}{pct}", color=FG, fontsize=8, pad=4)
        ax.set_xlabel("Iterasi", color=GRAY, fontsize=7)
        ax.legend(fontsize=6, loc="upper right", frameon=False, ncol=2)
        self._style_ax(ax)
        self.conv_fig.tight_layout()
        self.conv_canvas.draw_idle()

    def _style_ax(self, ax):
        ax.tick_params(colors=GRAY, labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

    # ── export ───────────────────────────────────────────────────────────────
    def _export_menu(self):
        if not self.current_run:
            return
        m = tk.Menu(self, tearoff=0, font=("Segoe UI", 10))
        m.add_command(label="Excel (.xlsx) — ringkasan, parameter, rute, log", command=self._export_xlsx)
        m.add_command(label="CSV (.csv) — tabel rute", command=self._export_csv)
        m.add_command(label="Gambar peta (.png)", command=self._export_png)
        m.add_command(label="Laporan teks (.txt)", command=self._export_txt)
        b = self.btn_export
        m.tk_popup(b.winfo_rootx(), b.winfo_rooty() - 90)

    def _ask_path(self, ext, name):
        types = {".xlsx": ("Excel", "*.xlsx"), ".csv": ("CSV", "*.csv"),
                 ".png": ("PNG", "*.png"), ".txt": ("Teks", "*.txt")}
        return filedialog.asksaveasfilename(defaultextension=ext, initialfile=name,
                                            filetypes=[types[ext]])

    def _export_do(self, ext, fn):
        run = self.current_run
        if not run:
            messagebox.showinfo("Info", "Jalankan optimasi dulu.")
            return
        path = self._ask_path(ext, f"hasil_tsp_{run['label'].replace(' ', '_').lower()}{ext}")
        if not path:
            return
        try:
            fn(path, run)
            self._status(f"Tersimpan: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal export:\n{e}")

    def _export_xlsx(self):
        self._export_do(".xlsx", lambda p, r: report.export_run(p, self.cities, r, self.runs))

    def _export_csv(self):
        self._export_do(".csv", lambda p, r: report.export_run(p, self.cities, r))

    def _export_png(self):
        self._export_do(".png", lambda p, r: report.export_png(
            p, self.cities, r, show_initial=self.map_mode != "Akhir"))

    def _export_txt(self):
        self._export_do(".txt", lambda p, r: report.export_txt(p, self.cities, r, self.runs))

    # ── jendela: perbandingan ────────────────────────────────────────────────
    def _compare(self):
        if len(self.runs) < 2:
            return
        win = self._toplevel("Perbandingan Run", "1180x720")
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(win, text="⇄  Perbandingan Run", font=("Segoe UI", 16, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, padx=18, pady=(16, 0), sticky="w")
        best = min(self.runs, key=lambda r: r["final_dist"])
        worst = max(self.runs, key=lambda r: r["final_dist"])
        diff = worst["final_dist"] - best["final_dist"]
        ctk.CTkLabel(win, text=f"🏆 Terbaik: {best['label']} — {report.pipeline_text(best)} — "
                               f"{best['final_dist']:,.4f}  (lebih pendek {diff:,.4f} / "
                               f"{diff / worst['final_dist'] * 100:.2f}% dari yang terburuk)",
                     font=("Segoe UI", 11, "bold"), text_color=GOLD
                     ).grid(row=1, column=0, padx=18, pady=(2, 8), sticky="w")

        cols = ["Run", "Inisialisasi", "Metaheuristik", "Move", "2-Opt", "Parameter",
                "Jarak Awal", "Jarak Final", "Gain (%)", "Iterasi", "Waktu (s)", "Kriteria Berhenti"]
        widths = [60, 115, 125, 70, 50, 260, 85, 90, 65, 65, 70, 220]
        tf = ctk.CTkFrame(win, fg_color=SURFACE, border_color=BORDER, border_width=1)
        tf.grid(row=2, column=0, sticky="ew", padx=16)
        tf.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(tf, columns=cols, show="headings", style="TSP.Treeview",
                            height=min(8, len(self.runs)))
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w" if c in ("Parameter", "Kriteria Berhenti",
                                                        "Inisialisasi", "Metaheuristik") else "center")
        tree.tag_configure("best", background="#E7F6EE")
        xs = ttk.Scrollbar(tf, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=xs.set)
        tree.grid(row=0, column=0, sticky="ew")
        xs.grid(row=1, column=0, sticky="ew")

        fig = Figure(figsize=(11, 3.6), facecolor=SURFACE)
        ax1, ax2 = fig.add_subplot(1, 2, 1), fig.add_subplot(1, 2, 2)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew", padx=16, pady=8)

        def refresh():
            tree.delete(*tree.get_children())
            bmin = min(r["final_dist"] for r in self.runs)
            for r in self.runs:
                row = report.run_row(r)
                tree.insert("", "end", iid=r["label"],
                            values=[row[c] if row[c] is not None else "—" for c in cols],
                            tags=("best",) if r["final_dist"] == bmin else ())
            ax1.clear(); ax2.clear()
            for r in self.runs:
                if r["history"]:
                    h = _downsample(r["history"], 2000)
                    ax1.plot([x["iter"] for x in h], [x["best_dist"] for x in h],
                             color=r["color"], lw=1.8, label=r["label"])
            ax1.set_title("Konvergensi (best per iterasi)", fontsize=9, color=FG)
            ax1.set_xlabel("Iterasi", fontsize=8, color=GRAY)
            ax1.set_ylabel("Jarak", fontsize=8, color=GRAY)
            if ax1.lines:
                ax1.legend(fontsize=7, frameon=False)
            labels = [r["label"] for r in self.runs]
            ax2.bar(labels, [r["init_dist"] for r in self.runs], color="#E5E5E5", label="Awal")
            bars = ax2.bar(labels, [r["final_dist"] for r in self.runs],
                           color=[r["color"] for r in self.runs], width=0.55, label="Final")
            for b, r in zip(bars, self.runs):
                ax2.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{r['final_dist']:,.1f}",
                         ha="center", va="bottom", fontsize=7, color=FG)
            ax2.set_title("Jarak awal vs final", fontsize=9, color=FG)
            ax2.tick_params(axis="x", labelsize=7, rotation=0)
            ax2.legend(fontsize=7, frameon=False)
            for a in (ax1, ax2):
                self._style_ax(a)
            fig.tight_layout()
            canvas.draw_idle()

        def selected():
            sel = tree.selection()
            return [r for r in self.runs if r["label"] in sel]

        def show_selected():
            s = selected()
            if s:
                self._display_run(s[0])

        def delete_selected():
            s = selected()
            if not s:
                return
            if len(self.runs) - len(s) < 1:
                messagebox.showinfo("Info", "Minimal satu run harus tersisa.", parent=win)
                return
            for r in s:
                self.runs.remove(r)
            if self.current_run in s:
                self._display_run(self.runs[-1])
            self._update_run_counter()
            refresh()

        def export():
            path = filedialog.asksaveasfilename(parent=win, defaultextension=".xlsx",
                                                initialfile="perbandingan_run.xlsx",
                                                filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
            if path:
                try:
                    report.export_compare(path, self.runs)
                    messagebox.showinfo("Sukses", f"Disimpan:\n{path}", parent=win)
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=win)

        tree.bind("<Double-1>", lambda _e: show_selected())
        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 14))
        for k, (txt, cmd, prim) in enumerate([
                ("Tampilkan di peta", show_selected, True),
                ("Hapus run terpilih", delete_selected, False),
                ("⬇ Export perbandingan", export, False),
                ("Tutup", win.destroy, False)]):
            ctk.CTkButton(bf, text=txt, command=cmd, width=170,
                          fg_color=ACCENT if prim else SURFACE,
                          text_color=SURFACE if prim else FG,
                          border_color=BORDER, border_width=0 if prim else 1,
                          hover_color=ACCENT_HV if prim else "#F3F3F3",
                          font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(bf, text="Tip: klik dua kali baris untuk menampilkan run di peta utama.",
                     font=("Segoe UI", 9), text_color=GRAY).pack(side="right")
        refresh()

    # ── jendela: log iterasi ─────────────────────────────────────────────────
    def _show_log(self):
        run = self.current_run
        if not run:
            return
        if not run["history"]:
            messagebox.showinfo("Log Iterasi", "Run ini tidak memakai metaheuristik, "
                                               "jadi tidak ada log iterasi.")
            return
        win = self._toplevel(f"Log Iterasi — {run['label']}", "1100x640")
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        sa = run["meta_method"] == "Simulated Annealing"
        ctk.CTkLabel(win, text=f"☰  Log Iterasi · {report.pipeline_text(run)}",
                     font=("Segoe UI", 15, "bold"), text_color=ACCENT
                     ).grid(row=0, column=0, padx=18, pady=(14, 2), sticky="w")

        ctrl = ctk.CTkFrame(win, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        var_imp = ctk.BooleanVar(value=False)
        var_acc = ctk.BooleanVar(value=False)
        info = ctk.CTkLabel(ctrl, text="", font=("Segoe UI", 9), text_color=GRAY)

        if sa:
            cols = ["Iter", "T", "Move", "Δ", "p = e^(−Δ/T)", "u", "Keputusan", "Current", "Best"]
            keys = ["iter", "temperature", "move", "delta", "prob", "u", "accepted",
                    "current_dist", "best_dist"]
            widths = [60, 90, 260, 80, 100, 60, 90, 100, 100]
        else:
            cols = ["Iter", "Move", "Δ", "Aspirasi", "Current", "Best", "Tabu list (sisa tenure)"]
            keys = ["iter", "move", "delta", "aspiration", "current_dist", "best_dist", "tabu_list"]
            widths = [60, 260, 80, 70, 100, 100, 420]

        tf = ctk.CTkFrame(win, fg_color=SURFACE, border_color=BORDER, border_width=1)
        tf.grid(row=2, column=0, sticky="nsew", padx=16)
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(tf, columns=cols, show="headings", style="TSP.Treeview")
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w" if c.startswith(("Move", "Tabu")) else "center")
        tree.tag_configure("imp", background="#E7F6EE")
        tree.tag_configure("rej", foreground="#9A9A9A")
        ys = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        xs = ttk.Scrollbar(tf, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        LIMIT = 3000

        def fmt(k, v):
            if v is None:
                return "—"
            if k == "accepted":
                return "Terima" if v else "Tolak"
            if k == "aspiration":
                return "Ya" if v else ""
            if isinstance(v, float):
                return f"{v:.4f}"
            return v

        def refresh():
            tree.delete(*tree.get_children())
            prev_best = None
            rows = []
            for h in run["history"]:
                improved = prev_best is not None and h["best_dist"] < prev_best
                prev_best = h["best_dist"]
                if var_imp.get() and not improved:
                    continue
                if sa and var_acc.get() and not h.get("accepted"):
                    continue
                rows.append((h, improved))
            for h, improved in rows[:LIMIT]:
                tag = "imp" if improved else ("rej" if sa and h.get("accepted") is False else "")
                tree.insert("", "end", values=[fmt(k, h.get(k)) for k in keys], tags=(tag,))
            note = (f"{len(rows):,} baris" + (f" (ditampilkan {LIMIT:,} pertama — export untuk "
                                              f"data lengkap)" if len(rows) > LIMIT else ""))
            info.configure(text=note + " · hijau = best membaik")

        ctk.CTkCheckBox(ctrl, text="Hanya saat best membaik", variable=var_imp,
                        command=refresh, font=("Segoe UI", 10), fg_color=ACCENT,
                        hover_color=ACCENT_HV, text_color=FG, checkbox_width=16,
                        checkbox_height=16).pack(side="left", padx=(0, 12))
        if sa:
            ctk.CTkCheckBox(ctrl, text="Hanya move diterima", variable=var_acc,
                            command=refresh, font=("Segoe UI", 10), fg_color=ACCENT,
                            hover_color=ACCENT_HV, text_color=FG, checkbox_width=16,
                            checkbox_height=16).pack(side="left", padx=(0, 12))
        info.pack(side="left")

        def export():
            path = filedialog.asksaveasfilename(parent=win, defaultextension=".xlsx",
                                                initialfile=f"log_{run['label'].replace(' ', '_').lower()}.xlsx",
                                                filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
            if not path:
                return
            import pandas as pd
            df = pd.DataFrame(run["history"])
            try:
                if path.lower().endswith(".csv"):
                    df.to_csv(path, index=False)
                else:
                    df.to_excel(path, index=False, sheet_name="Log Iterasi")
                messagebox.showinfo("Sukses", f"Disimpan:\n{path}", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        ctk.CTkButton(ctrl, text="⬇ Export log", command=export, width=120, fg_color=ACCENT,
                      hover_color=ACCENT_HV, font=("Segoe UI", 10)).pack(side="right")
        ctk.CTkLabel(win, text=f"Berhenti: {run['stop_reason']} · {run['iterations']:,} iterasi · "
                               f"parameter: {report.params_text(run['params'])}",
                     font=("Segoe UI", 9), text_color=GRAY
                     ).grid(row=3, column=0, padx=18, pady=(6, 12), sticky="w")
        refresh()

    # ── jendela: analisis parameter ──────────────────────────────────────────
    SWEEP_PARAMS = {
        "Simulated Annealing": {
            "Cooling rate (α)": ("cooling_rate", "0.9, 0.95, 0.99, 0.995, 0.999"),
            "Suhu awal (T₀)": ("T_start", "1, 10, 100, 1000, 10000"),
            "Suhu minimum": ("T_min", "1, 0.1, 0.01, 0.001"),
            "Iterasi maks": ("max_iter", "1000, 5000, 10000, 50000"),
            "Iterasi per suhu (L)": ("iter_per_temp", "1, 5, 10, 50"),
            "Move operator": ("move", "Swap, 2-Opt, Insertion"),
        },
        "Tabu Search": {
            "Tabu tenure": ("tabu_tenure", "3, 5, 10, 20, 50"),
            "Iterasi maks": ("max_iter", "50, 100, 250, 500, 1000"),
            "Jumlah kandidat": ("n_candidates", "0, 20, 50, 200"),
            "Move operator": ("move", "Swap, 2-Opt, Insertion"),
        },
    }

    def _param_analysis(self):
        if self.cities is None:
            messagebox.showwarning("Perhatian", "Muat atau generate data kota dulu.")
            return
        try:
            base = self._read_config()
        except ValueError as e:
            messagebox.showwarning("Parameter tidak valid", str(e))
            return

        win = self._toplevel("Analisis Parameter", "1120x760")
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(win, text="📊  Analisis Parameter", font=("Segoe UI", 16, "bold"),
                     text_color=ACCENT).grid(row=0, column=0, padx=18, pady=(14, 0), sticky="w")
        ctk.CTkLabel(win, text="Satu parameter divariasikan, parameter lain mengikuti sidebar. "
                               "Tiap nilai diulang dengan seed berbeda (seed dasar, +1, +2, …) "
                               "untuk melihat rata-rata dan sebaran hasil.",
                     font=("Segoe UI", 10), text_color=GRAY
                     ).grid(row=1, column=0, padx=18, pady=(0, 8), sticky="w")

        ctrl = ctk.CTkFrame(win, fg_color=SURFACE, border_color=BORDER, border_width=1,
                            corner_radius=10)
        ctrl.grid(row=2, column=0, sticky="ew", padx=16)
        var_algo = ctk.StringVar(value=base["meta"] if base["meta"] != "—"
                                 else "Simulated Annealing")
        var_param = ctk.StringVar()
        values_e = ctk.CTkEntry(ctrl, width=300, font=("Segoe UI", 10))
        reps_e = ctk.CTkEntry(ctrl, width=60, font=("Segoe UI", 10))
        reps_e.insert(0, "5")
        var_2opt = ctk.BooleanVar(value=False)

        def on_param(_v=None):
            _, sug = self.SWEEP_PARAMS[var_algo.get()][var_param.get()]
            values_e.delete(0, "end")
            values_e.insert(0, sug)

        param_menu = ctk.CTkOptionMenu(ctrl, variable=var_param, values=[], command=on_param,
                                       fg_color="#F1F1F1", text_color=FG, button_color=ACCENT,
                                       button_hover_color=ACCENT_HV, width=180,
                                       font=("Segoe UI", 10), dynamic_resizing=False)

        def on_algo(_v=None):
            names = list(self.SWEEP_PARAMS[var_algo.get()])
            param_menu.configure(values=names)
            var_param.set(names[0])
            on_param()

        algo_menu = ctk.CTkOptionMenu(ctrl, variable=var_algo,
                                      values=list(self.SWEEP_PARAMS), command=on_algo,
                                      fg_color="#F1F1F1", text_color=FG, button_color=ACCENT,
                                      button_hover_color=ACCENT_HV, width=170,
                                      font=("Segoe UI", 10), dynamic_resizing=False)
        for k, (lbl, w) in enumerate([("Algoritma", algo_menu), ("Parameter", param_menu),
                                      ("Nilai (pisah koma)", values_e), ("Ulangan", reps_e)]):
            ctk.CTkLabel(ctrl, text=lbl, font=("Segoe UI", 9, "bold"), text_color=GRAY
                         ).grid(row=0, column=k, padx=(12, 4), pady=(10, 0), sticky="w")
            w.grid(row=1, column=k, padx=(12, 4), pady=(2, 10), sticky="w")
        ctk.CTkCheckBox(ctrl, text="Sertakan 2-Opt", variable=var_2opt, font=("Segoe UI", 10),
                        fg_color=ACCENT, hover_color=ACCENT_HV, text_color=FG,
                        checkbox_width=16, checkbox_height=16
                        ).grid(row=1, column=4, padx=12, pady=(2, 10))
        btn_go = ctk.CTkButton(ctrl, text="▶ Jalankan", width=110, fg_color=ACCENT,
                               hover_color=ACCENT_HV, font=("Segoe UI", 11, "bold"))
        btn_go.grid(row=1, column=5, padx=(4, 6), pady=(2, 10))
        btn_exp = ctk.CTkButton(ctrl, text="⬇ Export", width=90, state="disabled",
                                fg_color=SURFACE, text_color=FG, border_color=BORDER,
                                border_width=1, hover_color="#F3F3F3", font=("Segoe UI", 10))
        btn_exp.grid(row=1, column=6, padx=(0, 12), pady=(2, 10))
        on_algo()

        prog_f = ctk.CTkFrame(win, fg_color="transparent")
        prog_f.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 4))
        prog_f.grid_columnconfigure(0, weight=1)
        prog = ttk.Progressbar(prog_f, style="TSP.Horizontal.TProgressbar", mode="determinate")
        prog.grid(row=0, column=0, sticky="ew")
        prog_lbl = ctk.CTkLabel(prog_f, text="", font=("Segoe UI", 9), text_color=GRAY)
        prog_lbl.grid(row=0, column=1, padx=(8, 0))

        out = ctk.CTkFrame(win, fg_color="transparent")
        out.grid(row=4, column=0, sticky="nsew", padx=16)
        out.grid_columnconfigure(0, weight=1)
        out.grid_rowconfigure(1, weight=1)
        cols = ["Nilai", "Best", "Rata-rata", "Worst", "Std", "Gain rata-rata (%)",
                "Iterasi rata-rata", "Waktu rata-rata (s)"]
        tree = ttk.Treeview(out, columns=cols, show="headings", style="TSP.Treeview", height=6)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=125, anchor="center")
        tree.tag_configure("best", background="#E7F6EE")
        tree.grid(row=0, column=0, sticky="ew")
        fig = Figure(figsize=(11, 3.4), facecolor=SURFACE)
        ax1, ax2 = fig.add_subplot(1, 2, 1), fig.add_subplot(1, 2, 2)
        canvas = FigureCanvasTkAgg(fig, master=out)
        canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        concl = ctk.CTkLabel(win, text="", font=("Segoe UI", 11, "bold"), text_color=FG,
                             justify="left", wraplength=1050, anchor="w")
        concl.grid(row=5, column=0, padx=18, pady=(6, 12), sticky="w")
        state = {"result": None, "cancel": False}

        def parse_values():
            key, _ = self.SWEEP_PARAMS[var_algo.get()][var_param.get()]
            raw = [v.strip() for v in values_e.get().split(",") if v.strip()]
            if not raw:
                raise ValueError("Isi minimal satu nilai.")
            if key == "move":
                bad = [v for v in raw if v not in MOVE_KEYS]
                if bad:
                    raise ValueError(f"Move tidak dikenal: {bad}. Pilihan: Swap, 2-Opt, Insertion.")
                return key, raw
            vals = []
            for v in raw:
                x = float(v)
                if key in ("max_iter", "iter_per_temp", "tabu_tenure", "n_candidates"):
                    x = int(x)
                if key == "cooling_rate" and not 0 < x < 1:
                    raise ValueError("α harus di antara 0 dan 1.")
                vals.append(x)
            return key, vals

        def go():
            if btn_go.cget("text") == "■ Batal":
                state["cancel"] = True
                return
            try:
                key, vals = parse_values()
                reps = int(reps_e.get())
                if not 1 <= reps <= 100:
                    raise ValueError("Ulangan 1 - 100.")
            except ValueError as e:
                messagebox.showwarning("Input tidak valid", str(e), parent=win)
                return
            algo = var_algo.get()
            cfg0 = dict(base)
            cfg0["use_meta"], cfg0["meta"], cfg0["two_opt"] = True, algo, var_2opt.get()
            if algo == "Simulated Annealing":
                cfg0["sa"] = self._sa_from_entries_safe()
                cfg0["move"] = self.var_sa_move.get()
            else:
                cfg0["ts"] = self._ts_from_entries_safe()
                cfg0["move"] = self.var_ts_move.get()
            state["cancel"] = False
            btn_go.configure(text="■ Batal")
            btn_exp.configure(state="disabled")
            prog.configure(maximum=len(vals) * reps, value=0)
            threading.Thread(target=worker, args=(cfg0, algo, key, vals, reps),
                             daemon=True).start()

        def worker(cfg0, algo, key, vals, reps):
            names = get_names(self.cities)
            seed0 = cfg0["seed"]
            raw, done = [], 0
            for v in vals:
                for r in range(reps):
                    if state["cancel"]:
                        self._post(lambda: finish(raw, algo, key, vals, cancelled=True))
                        return
                    cfg = dict(cfg0)
                    cfg["seed"] = seed0 + r
                    sub = "sa" if algo == "Simulated Annealing" else "ts"
                    cfg[sub] = dict(cfg0[sub])
                    if key == "move":
                        cfg["move"] = v
                    else:
                        cfg[sub][key] = v
                    res = run_pipeline(self.dist_matrix, names, cfg, keep_history=False)
                    raw.append({"Nilai": v, "Ulangan": r + 1, "Seed": cfg["seed"],
                                "Jarak Awal": round(res["init_dist"], 4),
                                "Jarak Final": round(res["final_dist"], 4),
                                "Gain (%)": round(res["pct"], 3),
                                "Iterasi": res["iterations"], "Waktu (s)": round(res["time"], 4),
                                "Kriteria Berhenti": res["stop_reason"]})
                    done += 1
                    self._post(lambda d=done, v=v: (prog.configure(value=d),
                                                       prog_lbl.configure(text=f"{d}/{len(vals) * reps} · nilai {v}")))
            self._post(lambda: finish(raw, algo, key, vals))

        def finish(raw, algo, key, vals, cancelled=False):
            btn_go.configure(text="▶ Jalankan")
            if not raw:
                prog_lbl.configure(text="Dibatalkan")
                return
            summary = []
            for v in vals:
                ds = [x["Jarak Final"] for x in raw if x["Nilai"] == v]
                if not ds:
                    continue
                sel = [x for x in raw if x["Nilai"] == v]
                summary.append({
                    "Nilai": v, "Best": round(min(ds), 4), "Rata-rata": round(float(np.mean(ds)), 4),
                    "Worst": round(max(ds), 4), "Std": round(float(np.std(ds, ddof=1)) if len(ds) > 1 else 0.0, 4),
                    "Gain rata-rata (%)": round(float(np.mean([x["Gain (%)"] for x in sel])), 3),
                    "Iterasi rata-rata": round(float(np.mean([x["Iterasi"] for x in sel])), 1),
                    "Waktu rata-rata (s)": round(float(np.mean([x["Waktu (s)"] for x in sel])), 4)})
            tree.delete(*tree.get_children())
            bmean = min(s["Rata-rata"] for s in summary)
            for s in summary:
                tree.insert("", "end", values=[s[c] for c in cols],
                            tags=("best",) if s["Rata-rata"] == bmean else ())
            ax1.clear(); ax2.clear()
            lbls = [str(s["Nilai"]) for s in summary]
            data = [[x["Jarak Final"] for x in raw if x["Nilai"] == s["Nilai"]] for s in summary]
            ax1.boxplot(data, patch_artist=True,
                        boxprops=dict(facecolor="#FFE3D6", edgecolor=ACCENT),
                        medianprops=dict(color=ACCENT, lw=2),
                        whiskerprops=dict(color=GRAY), capprops=dict(color=GRAY),
                        flierprops=dict(markeredgecolor=GRAY, markersize=4))
            ax1.set_xticks(range(1, len(lbls) + 1))
            ax1.set_xticklabels(lbls)
            ax1.plot(range(1, len(summary) + 1), [s["Rata-rata"] for s in summary],
                     "o--", color=FG, lw=1, ms=4, label="rata-rata")
            ax1.set_title(f"Jarak final vs {var_param.get()}", fontsize=9, color=FG)
            ax1.set_xlabel(var_param.get(), fontsize=8, color=GRAY)
            ax1.set_ylabel("Jarak final", fontsize=8, color=GRAY)
            ax1.legend(fontsize=7, frameon=False)
            ax2.bar(lbls, [s["Waktu rata-rata (s)"] for s in summary], color="#BFD3F6")
            ax2b = ax2.twinx()
            ax2b.plot(lbls, [s["Iterasi rata-rata"] for s in summary], "o-", color=ACCENT, lw=1.5)
            ax2.set_title("Waktu (batang) & iterasi (garis) rata-rata", fontsize=9, color=FG)
            ax2.set_ylabel("Waktu (s)", fontsize=8, color=GRAY)
            ax2b.set_ylabel("Iterasi", fontsize=8, color=ACCENT)
            for a in (ax1, ax2, ax2b):
                self._style_ax(a)
            fig.tight_layout()
            canvas.draw_idle()
            best = min(summary, key=lambda s: (s["Rata-rata"], s["Waktu rata-rata (s)"]))
            reps = max(x["Ulangan"] for x in raw)
            txt = (f"Rata-rata jarak terendah: {var_param.get()} = {best['Nilai']} "
                   f"(rata-rata {best['Rata-rata']:,.4f}, best {best['Best']:,.4f}, "
                   f"std {best['Std']:,.4f}, {reps} ulangan).")
            if algo == "Tabu Search" and all(s["Std"] == 0 for s in summary):
                txt += ("  Std = 0 karena Tabu Search deterministik bila inisialisasi bukan "
                        "Random dan kandidat = 0 (semua neighbor).")
            if cancelled:
                txt = "(Dibatalkan, hasil parsial) " + txt
            concl.configure(text=txt)
            state["result"] = (summary, raw, {
                "Algoritma": algo, "Parameter divariasikan": var_param.get(),
                "Nilai": ", ".join(map(str, vals)), "Ulangan": reps,
                "Inisialisasi": base["init"], "Seed dasar": base["seed"],
                "2-Opt": "Ya" if var_2opt.get() else "Tidak",
                "Parameter lain": report.params_text(
                    self._sa_from_entries_safe() if algo == "Simulated Annealing"
                    else self._ts_from_entries_safe()),
                "Move (sidebar)": (self.var_sa_move if algo == "Simulated Annealing"
                                   else self.var_ts_move).get(),
                "Jumlah kota": len(self.cities), "Data": self.data_source})
            btn_exp.configure(state="normal")

        def export():
            if not state["result"]:
                return
            path = filedialog.asksaveasfilename(parent=win, defaultextension=".xlsx",
                                                initialfile="analisis_parameter.xlsx",
                                                filetypes=[("Excel", "*.xlsx")])
            if path:
                try:
                    report.export_sweep(path, *state["result"])
                    png = os.path.splitext(path)[0] + ".png"
                    fig.savefig(png, dpi=180, facecolor=SURFACE)
                    messagebox.showinfo("Sukses", f"Disimpan:\n{path}\n{png}", parent=win)
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=win)

        btn_go.configure(command=go)
        btn_exp.configure(command=export)

    def _sa_from_entries_safe(self):
        try:
            p = {k: float(e.get()) for k, e in self.sa_entries.items()}
        except ValueError:
            p = {k: float(v) for k, v in SA_DEFAULT.items()}
        return dict(T_start=p["T_start"], cooling_rate=p["cooling_rate"], T_min=p["T_min"],
                    max_iter=int(p["max_iter"]), iter_per_temp=int(p["iter_per_temp"]),
                    stall_limit=int(p["stall_limit"]))

    def _ts_from_entries_safe(self):
        def gi(k, dflt):
            try:
                return int(self.ts_entries[k].get())
            except ValueError:
                return dflt
        t = self.ts_entries["tabu_tenure"].get().strip()
        return dict(tabu_tenure=int(t) if t.isdigit() else None, max_iter=gi("max_iter", 500),
                    stall_limit=gi("stall_limit", 0), n_candidates=gi("n_candidates", 0),
                    aspiration=self.var_aspiration.get())

    # ── reset ────────────────────────────────────────────────────────────────
    def _clear_results(self):
        self.current_run = None
        for v in (self.c_awal_val, self.c_meta_val, self.c_2opt_val, self.c_gain_val):
            v.configure(text="—")
        for s in (self.c_awal_sub, self.c_meta_pct, self.c_2opt_pct, self.c_gain_pct):
            s.configure(text="")
        self.lbl_run_title.configure(text="HASIL OPTIMASI")
        self.lbl_run_info.configure(text="")
        self._set_route_text("Belum ada rute.")
        for b in (self.btn_export, self.btn_log, self.btn_compare):
            b.configure(state="disabled")
        self.conv_ax.cla()
        self.conv_ax.set_facecolor("#FAFAFA")
        self.conv_ax.set_title("Jalankan algoritma dulu", color=GRAY, fontsize=8)
        self.conv_ax.set_axis_off()
        self.conv_canvas.draw_idle()

    def _reset(self):
        self.cities = None
        self.dist_matrix = None
        self.runs = []
        self.run_counter = 0
        self.file_label.configure(text="Belum ada data", text_color=SB_MUTED)
        self.preview_label.configure(text="")
        self._clear_results()
        self._update_run_counter()
        self._update_param_hint()
        self._status("")
        self.map_ax.cla()
        self.map_ax.set_facecolor("#F8F8F8")
        self.map_ax.set_title("Muat / generate data lalu jalankan algoritma", color=GRAY, fontsize=10)
        self.map_canvas.draw_idle()

    def _toplevel(self, title, geometry):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry(geometry)
        win.configure(fg_color=BG)
        win.transient(self)
        # jendela dimunculkan di depan (CTkToplevel kadang tertutup jendela utama di Windows)
        win.after(150, lambda: (win.lift(), win.focus_force()))
        return win

    def _status(self, msg):
        self.lbl_status.configure(text=msg)

    def _on_close(self):
        plt.close("all")
        self.quit()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
def _downsample(history, max_points):
    if len(history) <= max_points:
        return history
    step = len(history) / max_points
    idx = sorted({int(k * step) for k in range(max_points)} | {len(history) - 1})
    return [history[i] for i in idx]


def run_pipeline(dm, names, cfg, keep_history=True):
    """Konstruksi → metaheuristik (opsional) → 2-Opt (opsional). Return dict run."""
    t0 = time.perf_counter()
    seed = cfg["seed"]
    init_m = cfg["init"]
    if init_m == "Nearest Neighbor":
        init_route, init_dist = nearest_neighbor(dm)
    elif init_m == "Farthest Insertion":
        init_route, init_dist = farthest_insertion(dm)
    else:
        init_route, init_dist = random_route(dm, seed=seed)
    init_route = rotate_to_start(list(init_route), 0)

    meta = cfg["meta"] if cfg["use_meta"] else "—"
    move_lbl = cfg.get("move", "-")
    params, stop, iters = {}, "-", 0
    nm = names if keep_history else None
    if meta == "Simulated Annealing":
        p = cfg["sa"]
        log_every = max(1, p["max_iter"] // 50000)
        route, dist, hist, info = simulated_annealing(
            dm, init_route, move=MOVE_KEYS[move_lbl], seed=seed, names=nm,
            log_every=log_every if keep_history else max(1, p["max_iter"]),
            return_info=True, **p)
        params = {"T0": p["T_start"], "alpha": p["cooling_rate"], "T_min": p["T_min"],
                  "max_iter": p["max_iter"], "L": p["iter_per_temp"],
                  "stagnan": p["stall_limit"], "move": move_lbl, "seed": seed}
    elif meta == "Tabu Search":
        p = cfg["ts"]
        route, dist, hist, info = tabu_search(
            dm, init_route, move=MOVE_KEYS[move_lbl], seed=seed, names=nm,
            return_info=True, **p)
        params = {"tenure": info["tenure"] if p["tabu_tenure"] else f"auto({info['tenure']})",
                  "max_iter": p["max_iter"], "stagnan": p["stall_limit"],
                  "kandidat": p["n_candidates"] or "semua",
                  "aspirasi": "Ya" if p["aspiration"] else "Tidak", "move": move_lbl,
                  "seed": seed}
    else:
        route, dist, hist, info = init_route, init_dist, [], None
    if info:
        stop, iters = info["stop_reason"], info["iterations"]
    if init_m == "Random":
        params = {"seed_init": seed, **params}

    meta_route, meta_dist = route, dist
    if cfg["two_opt"]:
        final_route, final_dist, _ = two_opt(meta_route, dm)
    else:
        final_route, final_dist = meta_route, meta_dist

    gain = init_dist - final_dist
    return {
        "init_method": init_m, "meta_method": meta, "move": move_lbl,
        "two_opt": cfg["two_opt"], "params": params,
        "init_route": init_route, "init_dist": float(init_dist),
        "meta_route": meta_route, "meta_dist": float(meta_dist),
        "final_route": list(final_route), "final_dist": float(final_dist),
        "gain": float(gain), "pct": float(gain / init_dist * 100) if init_dist else 0.0,
        "history": hist if keep_history else [], "stop_reason": stop,
        "iterations": iters, "time": time.perf_counter() - t0,
    }


if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()
