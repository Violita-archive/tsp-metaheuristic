"""
app/main.py
TSP Metaheuristic Optimizer - Desktop Application
CustomTkinter + Matplotlib   |   Tema terang "peta kertas"
"""

import sys
import os
import math
import threading
import types

sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from components.theme import P, init_fonts, fh, fb, fm, apply_mpl_style
apply_mpl_style()

# ── Algoritma milik kita ----------------------------------------------------------
from algorithms.sa import simulated_annealing
from algorithms.tabu import tabu_search

# ── Import dari file teman (graceful fallback kalau belum di-merge) ---------------
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
    from components.map_plot import plot_route as _ext_plot
    from components.map_plot import plot_convergence as _ext_conv
    from components.map_plot import rotate_to_depot
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


# ── Fallback distance matrix (kalau utils/distance.py belum ada) -----------------
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


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")


# ══════════════════════════════════════════════════════════════════════════════════
class TSPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        init_fonts()                      # pilih font yang terpasang (setelah Tk ada)
        self.title("TSP Metaheuristic Optimizer")
        self.geometry("1320x780")
        self.minsize(1060, 660)
        self.configure(fg_color=P["bg"])

        # State
        self.cities       = None
        self.dist_matrix  = None
        self.last_route   = None
        self.last_dist    = None
        self.last_history = []
        self.init_dist    = None
        self.init_route   = None

        self._build_ui()

    # ── UI Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=310, fg_color=P["surface"], corner_radius=0,
                          border_width=1, border_color=P["line"])
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(1, weight=1)

        # ── Brand ---------------------------------------------------------------
        brand = ctk.CTkFrame(sb, fg_color=P["surface"], corner_radius=0)
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 2))

        logo = ctk.CTkCanvas(brand, width=46, height=46, bg=P["surface"], highlightthickness=0)
        logo.pack(side="left")
        pts = [(6, 36), (16, 14), (30, 26), (40, 8)]
        logo.create_line(*[c for p in pts for c in p], fill=P["coral"], width=3,
                         capstyle="round", joinstyle="round")
        for k, (x, y) in enumerate(pts):
            col = P["sun"] if k == 0 else P["teal"]
            logo.create_oval(x - 5, y - 5, x + 5, y + 5, fill=col, outline=P["ink"], width=2)

        title_box = ctk.CTkFrame(brand, fg_color="transparent")
        title_box.pack(side="left", padx=(10, 0))
        line1 = ctk.CTkFrame(title_box, fg_color="transparent")
        line1.pack(anchor="w")
        ctk.CTkLabel(line1, text="TSP", font=fh(24), text_color=P["coral"]
                     ).pack(side="left")
        ctk.CTkLabel(line1, text=" Optimizer", font=fh(24), text_color=P["ink"]
                     ).pack(side="left")
        ctk.CTkLabel(title_box, text="Metaheuristik  ·  Sains Data 24 | ITS",
                     font=fb(10), text_color=P["muted"]).pack(anchor="w")

        # ── Area parameter (bisa di-scroll di layar kecil) ------------------------
        body = ctk.CTkScrollableFrame(sb, fg_color=P["surface"], corner_radius=0,
                                      scrollbar_button_color=P["line"],
                                      scrollbar_button_hover_color=P["muted"])
        body.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        body.grid_columnconfigure(0, weight=1)
        row = 0

        # 1. Data
        self._section(body, 1, "Data Kota", row); row += 1
        self.file_label = ctk.CTkLabel(
            body, text="Belum ada file dipilih", font=fb(11), text_color=P["muted"],
            fg_color=P["surface2"], corner_radius=10, height=40, anchor="w",
            justify="left", wraplength=220)
        self.file_label.grid(row=row, column=0, padx=18, pady=(2, 6), sticky="ew"); row += 1
        ctk.CTkButton(body, text="Pilih File CSV / Excel", height=36, corner_radius=10,
                      fg_color="transparent", text_color=P["teal_dk"],
                      border_width=1.5, border_color=P["teal"], hover_color=P["teal_lt"],
                      font=fb(12, "bold"), command=self._load_file
                      ).grid(row=row, column=0, padx=18, pady=(0, 6), sticky="ew"); row += 1

        # 2. Inisialisasi
        self._section(body, 2, "Inisialisasi Rute", row); row += 1
        self.var_constructive = ctk.StringVar(value="Nearest Neighbor")
        self._option(body, ["Nearest Neighbor", "Farthest Insertion", "Random"],
                     self.var_constructive).grid(row=row, column=0, padx=18, pady=(2, 6),
                                                 sticky="ew"); row += 1

        # 3. Metaheuristik
        self._section(body, 3, "Metaheuristik", row); row += 1
        self.var_meta = ctk.StringVar(value="Simulated Annealing")
        self._option(body, ["Simulated Annealing", "Tabu Search"], self.var_meta,
                     command=self._toggle_params
                     ).grid(row=row, column=0, padx=18, pady=(2, 8), sticky="ew"); row += 1

        self.var_two_opt = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(body, text="Terapkan 2-Opt setelah metaheuristik",
                        variable=self.var_two_opt, text_color=P["ink"],
                        fg_color=P["coral"], hover_color=P["coral_dk"],
                        border_color=P["muted"], checkmark_color="white",
                        font=fb(11)
                        ).grid(row=row, column=0, padx=20, pady=(0, 6), sticky="w"); row += 1

        # 4. Parameter
        self._section(body, 4, "Parameter", row); row += 1

        self.sa_frame = self._param_card(body, "Simulated Annealing")
        self.sa_frame.grid(row=row, column=0, padx=18, pady=(2, 6), sticky="ew")
        self.e_t_start = self._param_row(self.sa_frame, "Suhu awal (T)",  "1000",  1)
        self.e_t_min   = self._param_row(self.sa_frame, "Suhu minimum",   "0.001", 2)
        self.e_cooling = self._param_row(self.sa_frame, "Cooling rate",   "0.995", 3)

        self.tabu_frame = self._param_card(body, "Tabu Search")
        self.tabu_frame.grid(row=row, column=0, padx=18, pady=(2, 6), sticky="ew")
        self.e_tabu_iter   = self._param_row(self.tabu_frame, "Max iterasi",  "500",  1)
        self.e_tabu_tenure = self._param_row(self.tabu_frame, "Tabu tenure",  "auto", 2)
        self.tabu_frame.grid_remove()    # default SA dulu
        row += 1

        # ── Footer: tombol Run & Export (selalu terlihat) -------------------------
        foot = ctk.CTkFrame(sb, fg_color=P["surface"], corner_radius=0)
        foot.grid(row=2, column=0, sticky="ew", padx=18, pady=(6, 10))
        foot.grid_columnconfigure(0, weight=1)

        self.btn_run = ctk.CTkButton(
            foot, text="▶  JALANKAN", height=50, corner_radius=14,
            fg_color=P["coral"], hover_color=P["coral_dk"], text_color="white",
            font=fh(15), command=self._run)
        self.btn_run.grid(row=0, column=0, sticky="ew")

        self.btn_export = ctk.CTkButton(
            foot, text="⬇  Export Hasil", height=38, corner_radius=12,
            fg_color="transparent", text_color=P["ink"],
            border_width=1.5, border_color=P["line"], hover_color=P["surface2"],
            font=fb(12, "bold"), state="disabled", command=self._export)
        self.btn_export.grid(row=1, column=0, pady=(8, 0), sticky="ew")

        self.lbl_status = ctk.CTkLabel(foot, text="Pilih file kota untuk memulai",
                                       font=fb(10), text_color=P["muted"],
                                       wraplength=250, justify="left", anchor="w")
        self.lbl_status.grid(row=2, column=0, pady=(8, 0), sticky="w")

    def _build_main_panel(self):
        panel = ctk.CTkFrame(self, fg_color=P["bg"], corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew", padx=18, pady=16)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # ── Kartu statistik -------------------------------------------------------
        stats = ctk.CTkFrame(panel, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        self.s_init = self._stat_card(stats, "Jarak awal",            0, P["sky"])
        self.s_meta = self._stat_card(stats, "Setelah metaheuristik", 1, P["teal"])
        self.s_2opt = self._stat_card(stats, "Setelah 2-Opt",         2, P["sun"])
        self.s_gain = self._stat_card(stats, "Total perbaikan",       3, P["coral"])

        # ── Tabs ----------------------------------------------------------------
        self.tabs = ctk.CTkTabview(
            panel, fg_color=P["surface"], corner_radius=18,
            border_width=1, border_color=P["line"],
            segmented_button_fg_color=P["surface2"],
            segmented_button_selected_color=P["sun"],
            segmented_button_selected_hover_color="#F2B02C",
            segmented_button_unselected_color=P["surface2"],
            segmented_button_unselected_hover_color=P["coral_lt"],
            text_color=P["ink"],
        )
        self.tabs.grid(row=1, column=0, sticky="nsew")
        self.tabs._segmented_button.configure(font=fb(12, "bold"))

        t_map  = self.tabs.add("  Peta Rute  ")
        t_conv = self.tabs.add("  Konvergensi  ")
        t_info = self.tabs.add("  Detail Rute  ")

        for t in [t_map, t_conv, t_info]:
            t.grid_rowconfigure(0, weight=1)
            t.grid_columnconfigure(0, weight=1)

        self._build_map_tab(t_map)
        self._build_conv_tab(t_conv)
        self._build_info_tab(t_info)

    # ── Tab builders ──────────────────────────────────────────────────────────────

    def _make_canvas(self, parent, figsize, empty_msg):
        fig, ax = plt.subplots(figsize=figsize, facecolor=P["surface"],
                               layout="constrained")
        fig.get_layout_engine().set(w_pad=0.22, h_pad=0.14)   # sisakan tepi
        self._empty_state(ax, empty_msg)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        widget = canvas.get_tk_widget()
        widget.configure(bg=P["surface"], highlightthickness=0)
        widget.grid(row=0, column=0, sticky="nsew")

        # Pastikan ukuran figure = ukuran kanvas, apa pun skala DPI layarnya.
        # (Pada display scaling 125%/150%, matplotlib mengubah DPI saat widget tampil
        #  tanpa memicu resize -> grafik terpotong di kanan/bawah.)
        def _refit(canvas=canvas, widget=widget):
            w, h = widget.winfo_width(), widget.winfo_height()
            if w > 20 and h > 20:
                canvas.resize(types.SimpleNamespace(width=w, height=h))
        widget.bind("<Map>", lambda e: widget.after(60, _refit), add="+")
        return fig, ax, canvas

    def _empty_state(self, ax, msg):
        ax.clear()
        ax.set_facecolor(P["surface"])
        ax.set_axis_off()
        ax.text(0.5, 0.56, "◌  ─ ─ ◌ ─ ─ ◌", transform=ax.transAxes, ha="center",
                va="center", fontsize=22, color=P["line"])
        ax.text(0.5, 0.44, msg, transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color=P["muted"])

    def _build_map_tab(self, parent):
        self.map_fig, self.map_ax, self.map_canvas = self._make_canvas(
            parent, (7, 5), "Pilih file kota, lalu klik JALANKAN\nuntuk melihat peta rute")

    def _build_conv_tab(self, parent):
        self.conv_fig, self.conv_ax, self.conv_canvas = self._make_canvas(
            parent, (7, 4), "Grafik konvergensi akan muncul\nsetelah algoritma dijalankan")

    def _build_info_tab(self, parent):
        self.info_wrap = ctk.CTkFrame(parent, fg_color="transparent")
        self.info_wrap.grid(row=0, column=0, sticky="nsew")
        self.info_wrap.grid_columnconfigure(0, weight=1)
        self.info_wrap.grid_rowconfigure(1, weight=1)
        self.info_empty = ctk.CTkLabel(
            self.info_wrap, text="Belum ada hasil.\nJalankan algoritma terlebih dahulu.",
            font=fb(12), text_color=P["muted"], justify="center")
        self.info_empty.grid(row=0, column=0, rowspan=2, sticky="nsew")

    # ── Event handlers ────────────────────────────────────────────────────────────

    def _toggle_params(self, choice):
        if choice == "Simulated Annealing":
            self.tabu_frame.grid_remove()
            self.sa_frame.grid()
        else:
            self.sa_frame.grid_remove()
            self.tabu_frame.grid()

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
                text=f"✓ {fname}\n{len(self.cities)} kota dimuat", text_color=P["teal_dk"]
            )
            self._status(f"{len(self.cities)} kota siap diproses")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca file:\n{e}")

    def _run(self):
        if self.cities is None:
            messagebox.showwarning("Perhatian", "Pilih file kota terlebih dahulu!")
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
            coords = get_coords(self.cities)
            names  = get_names(self.cities)
            dm     = self.dist_matrix

            # 1. Constructive
            c = self.var_constructive.get()
            if c == "Nearest Neighbor":
                init_route, init_dist = nearest_neighbor(dm)
            elif c == "Farthest Insertion":
                init_route, init_dist = farthest_insertion(dm)
            else:
                init_route, init_dist = random_route(dm)

            # 2. Metaheuristik
            m = self.var_meta.get()
            if m == "Simulated Annealing":
                T_start  = float(self.e_t_start.get())
                T_min    = float(self.e_t_min.get())
                cooling  = float(self.e_cooling.get())
                meta_route, meta_dist, history = simulated_annealing(
                    dm, init_route, T_start=T_start, T_min=T_min, cooling_rate=cooling
                )
            else:
                max_iter = int(self.e_tabu_iter.get())
                tenure_s = self.e_tabu_tenure.get().strip()
                tenure   = None if tenure_s == "auto" else int(tenure_s)
                meta_route, meta_dist, history = tabu_search(
                    dm, init_route, tabu_tenure=tenure, max_iter=max_iter
                )

            # 3. 2-Opt (opsional)
            if self.var_two_opt.get() and _has_two_opt:
                final_route, final_dist, _ = two_opt(meta_route, dm)
            else:
                final_route, final_dist = meta_route, meta_dist

            # Simpan state
            self.init_dist    = init_dist
            self.init_route   = init_route
            self.last_route   = final_route
            self.last_dist    = final_dist
            self.last_history = history

            # Update UI di main thread
            self.after(0, lambda: self._show_results(
                coords, names, init_dist, meta_dist, final_dist, history, final_route, m
            ))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Terjadi kesalahan:\n{e}"))
            self.after(0, lambda: self.btn_run.configure(state="normal", text="▶  JALANKAN"))

    def _show_results(self, coords, names, init_dist, meta_dist, final_dist, history, route, meta_name):
        # Stats
        self.s_init.configure(text=f"{init_dist:.2f}")
        self.s_meta.configure(text=f"{meta_dist:.2f}")
        self.s_2opt.configure(text=f"{final_dist:.2f}" if self.var_two_opt.get() else "—")
        gain = init_dist - final_dist
        pct  = gain / init_dist * 100 if init_dist else 0
        arrow = "▼" if gain > 0 else "•"
        self.s_gain.configure(text=f"{arrow} {gain:.2f}  ({pct:.1f}%)",
                              text_color=P["grass"] if gain > 0 else P["ink"])

        # Peta rute
        self._draw_map(coords, names, route)

        # Konvergensi
        self._draw_conv(history, meta_name)

        # Detail rute
        self._write_info(coords, names, route, init_dist, meta_dist, final_dist)

        # Re-enable
        self.btn_run.configure(state="normal", text="▶  JALANKAN")
        self.btn_export.configure(state="normal")
        self._status(f"Selesai! Jarak optimal: {final_dist:.4f}")

    def _draw_map(self, coords, names, route):
        _ext_plot(coords, names, route, self.init_route,
                  subtitle=f"Total jarak {self.last_dist:.2f}  ·  {len(coords)} kota  ·  "
                           f"garis putus-putus = rute awal",
                  ax=self.map_ax)
        self.map_canvas.draw()

    def _draw_conv(self, history, meta_name):
        _ext_conv(history, self.init_dist, title=f"Konvergensi — {meta_name}",
                  subtitle="Jarak terbaik di setiap iterasi", ax=self.conv_ax)
        self.conv_canvas.draw()

    def _write_info(self, coords, names, route, init_dist, meta_dist, final_dist):
        """Tab Detail Rute: ringkasan + kartu per kota (bukan teks polos)."""
        for w in self.info_wrap.winfo_children():
            w.destroy()

        r = rotate_to_depot(route)           # selalu mulai dari depot
        n = len(r)
        legs = [math.dist(coords[r[k]], coords[r[(k + 1) % n]]) for k in range(n)]
        max_leg = max(legs) if legs else 1
        gain = init_dist - final_dist
        pct = gain / init_dist * 100 if init_dist else 0

        # Ringkasan
        head = ctk.CTkFrame(self.info_wrap, fg_color=P["coral_lt"], corner_radius=14)
        head.grid(row=0, column=0, sticky="ew", pady=(4, 10))
        head.grid_columnconfigure(1, weight=1)
        left = ctk.CTkFrame(head, fg_color="transparent")
        left.grid(row=0, column=0, padx=18, pady=12, sticky="w")
        ctk.CTkLabel(left, text="TOTAL JARAK RUTE TERBAIK", font=fb(9, "bold"),
                     text_color=P["coral_dk"]).pack(anchor="w")
        ctk.CTkLabel(left, text=f"{final_dist:.4f}", font=fh(30),
                     text_color=P["ink"]).pack(anchor="w")
        right = ctk.CTkFrame(head, fg_color="transparent")
        right.grid(row=0, column=1, padx=18, pady=12, sticky="e")
        for k, (lab, val) in enumerate([("Awal", f"{init_dist:.2f}"),
                                        ("Metaheuristik", f"{meta_dist:.2f}"),
                                        ("Perbaikan", f"{gain:.2f} ({pct:.1f}%)")]):
            box = ctk.CTkFrame(right, fg_color=P["surface"], corner_radius=10)
            box.grid(row=0, column=k, padx=(8, 0))
            ctk.CTkLabel(box, text=lab.upper(), font=fb(8, "bold"),
                         text_color=P["muted"]).pack(anchor="w", padx=12, pady=(7, 0))
            ctk.CTkLabel(box, text=val, font=fh(14),
                         text_color=P["ink"]).pack(anchor="w", padx=12, pady=(0, 7))

        # Daftar kota
        lst = ctk.CTkScrollableFrame(self.info_wrap, fg_color="transparent",
                                     scrollbar_button_color=P["line"],
                                     scrollbar_button_hover_color=P["muted"])
        lst.grid(row=1, column=0, sticky="nsew")
        lst.grid_columnconfigure(0, weight=1)

        for k, idx in enumerate(r):
            depot = idx == 0
            nxt = r[(k + 1) % n]
            card = ctk.CTkFrame(lst, fg_color=P["surface2"], corner_radius=12,
                                border_width=1, border_color=P["line"])
            card.grid(row=k, column=0, sticky="ew", pady=3, padx=(0, 6))
            card.grid_columnconfigure(1, weight=1)

            self._badge(card, "★" if depot else str(k + 1), 36,
                        P["sun"] if depot else P["teal"],
                        P["ink"] if depot else "white", fh(13), P["surface2"]
                        ).grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)

            ctk.CTkLabel(card, text=names[idx] + ("   DEPOT" if depot else ""),
                         font=fh(13), text_color=P["ink"], anchor="w"
                         ).grid(row=0, column=1, sticky="sw", pady=(8, 0))
            ctk.CTkLabel(card, text=f"({coords[idx][0]:g}, {coords[idx][1]:g})",
                         font=fm(10), text_color=P["muted"], anchor="w"
                         ).grid(row=1, column=1, sticky="nw", pady=(0, 8))

            ctk.CTkLabel(card, text=f"→ {names[nxt]}", font=fb(11),
                         text_color=P["muted"], anchor="e"
                         ).grid(row=0, column=2, sticky="se", padx=(8, 16), pady=(8, 0))
            side = ctk.CTkFrame(card, fg_color="transparent")
            side.grid(row=1, column=2, sticky="ne", padx=(8, 16), pady=(0, 8))
            bar = ctk.CTkProgressBar(side, width=110, height=7, corner_radius=4,
                                     fg_color=P["line"], progress_color=P["coral"])
            bar.set(legs[k] / max_leg if max_leg else 0)
            bar.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(side, text=f"{legs[k]:.2f}", font=fh(12),
                         text_color=P["ink"]).pack(side="left")

        ctk.CTkLabel(lst, text=f"Urutan indeks: {r}", font=fm(10),
                     text_color=P["muted"], anchor="w"
                     ).grid(row=n, column=0, sticky="w", pady=(8, 4), padx=4)

    def _export(self):
        if not _has_export:
            messagebox.showinfo("Belum tersedia",
                                "components/export.py belum ada.\nTunggu teman push file-nya.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )
        if not path:
            return
        try:
            export_results(path, self.cities, self.last_route,
                           self.last_dist, self.last_history, self.var_meta.get())
            messagebox.showinfo("Sukses", f"Hasil disimpan:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal export:\n{e}")

    # ── Helper UI ─────────────────────────────────────────────────────────────────

    def _badge(self, parent, text, size, bg, fg, font, canvas_bg):
        """Lencana bulat sempurna (digambar di canvas)."""
        c = ctk.CTkCanvas(parent, width=size, height=size, bg=canvas_bg,
                          highlightthickness=0)
        c.create_oval(1, 1, size - 1, size - 1, fill=bg, outline=bg)
        c.create_text(size / 2, size / 2, text=text, fill=fg, font=font)
        return c

    def _section(self, parent, num, title, row):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=18, pady=(10, 0))
        self._badge(f, str(num), 24, P["coral"], "white", fh(11),
                    P["surface"]).pack(side="left")
        ctk.CTkLabel(f, text=title, font=fh(13), text_color=P["ink"]
                     ).pack(side="left", padx=(8, 0))

    def _option(self, parent, values, variable, command=None):
        return ctk.CTkOptionMenu(
            parent, values=values, variable=variable, command=command, height=36,
            corner_radius=10, fg_color=P["surface2"], text_color=P["ink"],
            button_color=P["teal"], button_hover_color=P["teal_dk"],
            dropdown_fg_color=P["surface"], dropdown_text_color=P["ink"],
            dropdown_hover_color=P["coral_lt"], font=fb(12), dropdown_font=fb(12))

    def _param_card(self, parent, caption):
        card = ctk.CTkFrame(parent, fg_color=P["surface2"], corner_radius=12,
                            border_width=1, border_color=P["line"])
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=caption.upper(), font=fb(9, "bold"),
                     text_color=P["teal_dk"]
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 2))
        return card

    def _param_row(self, parent, label, default, row):
        ctk.CTkLabel(parent, text=label, text_color=P["muted"], font=fb(11)
                     ).grid(row=row, column=0, sticky="w", padx=(14, 4), pady=3)
        entry = ctk.CTkEntry(parent, width=92, height=30, corner_radius=8,
                             fg_color=P["surface"], border_color=P["line"],
                             border_width=1.5, text_color=P["ink"], font=fm(11),
                             justify="center")
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="e", padx=(4, 14), pady=3)
        if row == 3 or (parent is getattr(self, "tabu_frame", None) and row == 2):
            entry.grid_configure(pady=(3, 10))
        return entry

    def _stat_card(self, parent, label, col, accent):
        card = ctk.CTkFrame(parent, fg_color=P["surface"], corner_radius=14,
                            border_width=1, border_color=P["line"], height=86)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
        card.pack_propagate(False)
        ctk.CTkFrame(card, width=5, corner_radius=3, fg_color=accent
                     ).pack(side="left", fill="y", padx=(12, 0), pady=14)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(inner, text=label.upper(), font=fb(9, "bold"),
                     text_color=P["muted"]).pack(anchor="w")
        val = ctk.CTkLabel(inner, text="—", font=fh(24), text_color=P["ink"])
        val.pack(anchor="w")
        return val

    def _status(self, msg: str):
        self.lbl_status.configure(text=msg)


# ══════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()
