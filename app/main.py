"""
app/main.py
TSP Metaheuristic Optimizer - Desktop Application
CustomTkinter + Matplotlib
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

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


# ── Warna tema (Theme A: Dark Navy + Teal) ----------------------------------------
TEAL    = "#00C9A7"
NAVY    = "#0F1923"
CARD    = "#1B2B38"
FG      = "#E8F4F0"
GRAY    = "#8FA0AC"
GOLD    = "#FFD700"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ══════════════════════════════════════════════════════════════════════════════════
class TSPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TSP Metaheuristic Optimizer")
        self.geometry("1280x740")
        self.minsize(960, 620)
        self.configure(fg_color=NAVY)

        # State
        self.cities       = None
        self.dist_matrix  = None
        self.last_route   = None
        self.last_dist    = None
        self.last_history = []
        self.init_dist    = None

        self._build_ui()

    # ── UI Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=270, fg_color=CARD, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        row = 0

        # Judul
        ctk.CTkLabel(sb, text="TSP Optimizer",
                     font=("Segoe UI", 18, "bold"), text_color=TEAL
                     ).grid(row=row, column=0, padx=20, pady=(20, 2), sticky="w"); row += 1
        ctk.CTkLabel(sb, text="Metaheuristik · Stat24 ITS",
                     font=("Segoe UI", 10), text_color=GRAY
                     ).grid(row=row, column=0, padx=20, pady=(0, 14), sticky="w"); row += 1

        self._divider(sb, row); row += 1

        # File loader
        ctk.CTkLabel(sb, text="Data Kota", font=("Segoe UI", 12, "bold"),
                     text_color=FG).grid(row=row, column=0, padx=20, sticky="w"); row += 1

        self.file_label = ctk.CTkLabel(sb, text="Belum ada file",
                                        font=("Segoe UI", 10), text_color=GRAY, wraplength=210)
        self.file_label.grid(row=row, column=0, padx=20, sticky="w"); row += 1

        ctk.CTkButton(sb, text="Pilih File CSV / Excel",
                      fg_color=TEAL, text_color=NAVY, hover_color="#009E86",
                      font=("Segoe UI", 11, "bold"),
                      command=self._load_file
                      ).grid(row=row, column=0, padx=16, pady=(6, 14), sticky="ew"); row += 1

        self._divider(sb, row); row += 1

        # Metode inisialisasi
        ctk.CTkLabel(sb, text="Inisialisasi Rute", font=("Segoe UI", 12, "bold"),
                     text_color=FG).grid(row=row, column=0, padx=20, sticky="w"); row += 1

        self.var_constructive = ctk.StringVar(value="Nearest Neighbor")
        ctk.CTkOptionMenu(sb, values=["Nearest Neighbor", "Farthest Insertion", "Random"],
                          variable=self.var_constructive,
                          fg_color=NAVY, button_color=TEAL, button_hover_color="#009E86",
                          text_color=FG
                          ).grid(row=row, column=0, padx=16, pady=(4, 12), sticky="ew"); row += 1

        # Metaheuristik
        ctk.CTkLabel(sb, text="Metaheuristik", font=("Segoe UI", 12, "bold"),
                     text_color=FG).grid(row=row, column=0, padx=20, sticky="w"); row += 1

        self.var_meta = ctk.StringVar(value="Simulated Annealing")
        ctk.CTkOptionMenu(sb, values=["Simulated Annealing", "Tabu Search"],
                          variable=self.var_meta,
                          fg_color=NAVY, button_color=TEAL, button_hover_color="#009E86",
                          text_color=FG, command=self._toggle_params
                          ).grid(row=row, column=0, padx=16, pady=(4, 8), sticky="ew"); row += 1

        # Toggle 2-Opt
        self.var_two_opt = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sb, text="Terapkan 2-Opt setelah metaheuristik",
                        variable=self.var_two_opt,
                        text_color=FG, fg_color=TEAL, hover_color="#009E86",
                        checkmark_color=NAVY, font=("Segoe UI", 10)
                        ).grid(row=row, column=0, padx=20, pady=(0, 12), sticky="w"); row += 1

        self._divider(sb, row); row += 1

        # ── Parameter SA ----------------------------------------------------------
        self.sa_frame = ctk.CTkFrame(sb, fg_color="transparent")
        self.sa_frame.grid(row=row, column=0, padx=16, sticky="ew")
        self.sa_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.sa_frame, text="Parameter SA",
                     font=("Segoe UI", 11, "bold"), text_color=FG
                     ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.e_t_start  = self._param_row(self.sa_frame, "T Awal",   "1000",  1)
        self.e_t_min    = self._param_row(self.sa_frame, "T Min",    "0.001", 2)
        self.e_cooling  = self._param_row(self.sa_frame, "Cooling",  "0.995", 3)

        # ── Parameter Tabu --------------------------------------------------------
        self.tabu_frame = ctk.CTkFrame(sb, fg_color="transparent")
        self.tabu_frame.grid(row=row, column=0, padx=16, sticky="ew")
        self.tabu_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.tabu_frame, text="Parameter Tabu",
                     font=("Segoe UI", 11, "bold"), text_color=FG
                     ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.e_tabu_iter   = self._param_row(self.tabu_frame, "Max Iter",    "500",  1)
        self.e_tabu_tenure = self._param_row(self.tabu_frame, "Tabu Tenure", "auto", 2)

        self.tabu_frame.grid_remove()   # default SA dulu
        row += 1

        # ── Tombol Run & Export ---------------------------------------------------
        self.btn_run = ctk.CTkButton(
            sb, text="▶  JALANKAN",
            fg_color=TEAL, text_color=NAVY, hover_color="#009E86",
            font=("Segoe UI", 14, "bold"), height=46, corner_radius=8,
            command=self._run
        )
        self.btn_run.grid(row=row, column=0, padx=16, pady=(18, 6), sticky="ew"); row += 1

        self.btn_export = ctk.CTkButton(
            sb, text="⬇  Export Hasil",
            fg_color="transparent", text_color=TEAL,
            border_color=TEAL, border_width=1,
            hover_color=CARD, font=("Segoe UI", 11),
            state="disabled", command=self._export
        )
        self.btn_export.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="ew"); row += 1

        # Status
        self.lbl_status = ctk.CTkLabel(sb, text="", font=("Segoe UI", 10),
                                        text_color=GRAY, wraplength=230)
        self.lbl_status.grid(row=row, column=0, padx=20, pady=(0, 20), sticky="w")

    def _build_main_panel(self):
        panel = ctk.CTkFrame(self, fg_color=NAVY)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # ── Stats bar -----------------------------------------------------------
        stats = ctk.CTkFrame(panel, height=64, fg_color=CARD)
        stats.grid(row=0, column=0, sticky="ew")
        stats.grid_propagate(False)
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.s_init  = self._stat_tile(stats, "Jarak Awal",            "—", 0)
        self.s_meta  = self._stat_tile(stats, "Setelah Metaheuristik", "—", 1)
        self.s_2opt  = self._stat_tile(stats, "Setelah 2-Opt",         "—", 2)
        self.s_gain  = self._stat_tile(stats, "Total Gain",             "—", 3)

        # ── Tabs ----------------------------------------------------------------
        self.tabs = ctk.CTkTabview(
            panel,
            fg_color=CARD,
            segmented_button_fg_color=NAVY,
            segmented_button_selected_color=TEAL,
            segmented_button_selected_hover_color="#009E86",
            segmented_button_unselected_color=NAVY,
            segmented_button_unselected_hover_color="#243545",
            text_color=FG,
        )
        self.tabs.grid(row=1, column=0, sticky="nsew")

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

    def _build_map_tab(self, parent):
        fig, ax = plt.subplots(figsize=(7, 5), facecolor=CARD)
        ax.set_facecolor(CARD)
        ax.set_title("Pilih file dan jalankan algoritma", color=GRAY, fontsize=11)
        self._style_ax(ax)
        self.map_fig, self.map_ax = fig, ax
        self.map_canvas = FigureCanvasTkAgg(fig, master=parent)
        self.map_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _build_conv_tab(self, parent):
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=CARD)
        ax.set_facecolor(CARD)
        ax.set_title("Jalankan algoritma dulu", color=GRAY, fontsize=11)
        self._style_ax(ax)
        self.conv_fig, self.conv_ax = fig, ax
        self.conv_canvas = FigureCanvasTkAgg(fig, master=parent)
        self.conv_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _build_info_tab(self, parent):
        self.txt_info = ctk.CTkTextbox(
            parent, fg_color=CARD, text_color=FG,
            font=("Courier New", 11), wrap="none"
        )
        self.txt_info.grid(row=0, column=0, sticky="nsew")
        self.txt_info.insert("1.0", "Belum ada hasil. Jalankan algoritma terlebih dahulu.")
        self.txt_info.configure(state="disabled")

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
                text=f"✓ {fname}\n{len(self.cities)} kota dimuat", text_color=TEAL
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
        self.s_gain.configure(text=f"{gain:.2f}  ({pct:.1f}%)")

        # Peta rute
        self._draw_map(coords, names, route)

        # Konvergensi
        self._draw_conv(history, meta_name)

        # Detail teks
        self._write_info(names, route, init_dist, meta_dist, final_dist)

        # Re-enable
        self.btn_run.configure(state="normal", text="▶  JALANKAN")
        self.btn_export.configure(state="normal")
        self._status(f"Selesai! Jarak optimal: {final_dist:.4f}")

    def _draw_map(self, coords, names, route):
        ax = self.map_ax
        ax.clear()
        ax.set_facecolor(CARD)

        # Gambar rute (tertutup)
        xs = [coords[i][0] for i in route] + [coords[route[0]][0]]
        ys = [coords[i][1] for i in route] + [coords[route[0]][1]]
        ax.plot(xs, ys, color=TEAL, linewidth=2, zorder=1, alpha=0.85)

        # Titik kota
        ax.scatter([c[0] for c in coords], [c[1] for c in coords],
                   color=TEAL, s=70, zorder=3, edgecolors=FG, linewidths=0.8)

        # Label kota
        for name, coord in zip(names, coords):
            ax.annotate(name, coord, fontsize=8, color=FG,
                        xytext=(6, 4), textcoords="offset points")

        # Tanda kota pertama (bintang emas)
        ax.scatter([coords[route[0]][0]], [coords[route[0]][1]],
                   color=GOLD, s=130, zorder=4, marker="*")

        ax.set_title("Rute Optimal TSP", color=FG, fontsize=11, pad=8)
        self._style_ax(ax)
        self.map_canvas.draw()

    def _draw_conv(self, history, meta_name):
        ax = self.conv_ax
        ax.clear()
        ax.set_facecolor(CARD)

        if not history:
            ax.set_title("Tidak ada data konvergensi", color=GRAY, fontsize=11)
            self.conv_canvas.draw()
            return

        iters      = [h["iter"] for h in history]
        best_dists = [h["best_dist"] for h in history]
        curr_dists = [h.get("current_dist", h["best_dist"]) for h in history]

        ax.plot(iters, curr_dists, color=GRAY,  linewidth=1.2, alpha=0.5, label="Current")
        ax.plot(iters, best_dists, color=TEAL,  linewidth=2.2, label="Best")

        ax.set_title(f"Konvergensi — {meta_name}", color=FG, fontsize=11, pad=8)
        ax.set_xlabel("Iterasi", color=GRAY, fontsize=9)
        ax.set_ylabel("Jarak", color=GRAY, fontsize=9)
        ax.legend(facecolor=CARD, edgecolor=GRAY, labelcolor=FG, fontsize=9)
        self._style_ax(ax)
        self.conv_canvas.draw()

    def _write_info(self, names, route, init_dist, meta_dist, final_dist):
        rn   = [names[i] for i in route]
        gain = init_dist - final_dist
        pct  = gain / init_dist * 100 if init_dist else 0

        lines = [
            "=" * 48,
            "  RUTE OPTIMAL TSP",
            "=" * 48,
            "",
            "  " + " → ".join(rn) + f" → {rn[0]}",
            "",
            f"  Jarak Awal             : {init_dist:.4f}",
            f"  Setelah Metaheuristik  : {meta_dist:.4f}",
            f"  Setelah 2-Opt          : {final_dist:.4f}",
            f"  Total Improvement      : {gain:.4f}  ({pct:.2f}%)",
            "",
            f"  Urutan indeks: {route}",
            "=" * 48,
        ]
        text = "\n".join(lines)

        self.txt_info.configure(state="normal")
        self.txt_info.delete("1.0", "end")
        self.txt_info.insert("1.0", text)
        self.txt_info.configure(state="disabled")

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

    def _divider(self, parent, row):
        ctk.CTkFrame(parent, height=1, fg_color=GRAY
                     ).grid(row=row, column=0, padx=16, sticky="ew", pady=(0, 10))

    def _param_row(self, parent, label, default, row):
        ctk.CTkLabel(parent, text=label, text_color=GRAY, font=("Segoe UI", 10)
                     ).grid(row=row, column=0, sticky="w", pady=3)
        entry = ctk.CTkEntry(parent, width=100, fg_color=NAVY, border_color=TEAL,
                              text_color=FG, font=("Segoe UI", 10))
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="e", pady=3)
        return entry

    def _stat_tile(self, parent, label, value, col):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, padx=16, pady=10, sticky="nsew")
        val_lbl = ctk.CTkLabel(f, text=value, font=("Segoe UI", 20, "bold"), text_color=TEAL)
        val_lbl.pack(anchor="w")
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 9), text_color=GRAY).pack(anchor="w")
        return val_lbl

    def _style_ax(self, ax):
        ax.tick_params(colors=GRAY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRAY)

    def _status(self, msg: str):
        self.lbl_status.configure(text=msg)


# ══════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()