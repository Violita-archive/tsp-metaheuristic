"""
app/components/map_plot.py
Visualisasi TSP dengan matplotlib. Semua fungsi RETURN matplotlib Figure.

plot_route(coords, names, route, ...)        -> peta rute (titik bernomor urutan kunjungan)
plot_convergence(history, init_dist, ...)    -> grafik konvergensi SA / Tabu
save_route_png(path, ...)                    -> simpan peta ke PNG

Semua fungsi menerima ax=... (gambar ke Axes yang sudah ada di GUI) atau
tanpa ax (bikin Figure baru).
"""
import matplotlib.patheffects as pe
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

try:
    from components.theme import P, apply_mpl_style
except ImportError:
    from app.components.theme import P, apply_mpl_style

apply_mpl_style()


def rotate_to_depot(route, depot=0):
    """Putar rute supaya mulai dari depot (rute tertutup, jarak tidak berubah)."""
    r = list(route)
    if len(r) > 1 and r[0] == r[-1]:
        r = r[:-1]
    k = r.index(depot) if depot in r else 0
    return r[k:] + r[:k]


def _prepare_axes(ax, size=(7, 5)):
    if ax is None:
        fig = Figure(figsize=size, facecolor=P["surface"])
        ax = fig.add_subplot(111)
    else:
        fig = ax.figure
    ax.clear()
    ax.set_axis_on()
    ax.set_facecolor(P["map_bg"])
    return fig, ax


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(P["line"])
    ax.tick_params(colors=P["muted"], labelsize=8, length=0, pad=6)
    ax.grid(True, color=P["grid"], lw=0.8, ls=(0, (2, 3)))
    ax.set_axisbelow(True)


def _heading(ax, title, subtitle=None):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold",
                 color=P["ink"], pad=24 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.025, subtitle, transform=ax.transAxes, fontsize=9,
                color=P["muted"], va="bottom")


def plot_route(coords, names, route, initial_route=None,
               title="Rute Optimal TSP", subtitle=None, ax=None, **_ignored):
    """Peta rute. Titik diberi nomor urutan kunjungan, depot = oranye + bintang.

    coords        : list/array (x, y), index 0 = depot
    names         : list nama kota
    route         : rute akhir (list index)
    initial_route : rute awal (opsional) -> garis putus-putus abu-abu
    ax            : opsional, gambar ke Axes yang sudah ada
    Return: matplotlib Figure
    """
    fig, ax = _prepare_axes(ax)
    _style_axes(ax)
    halo = [pe.withStroke(linewidth=3.2, foreground=P["map_bg"])]

    # rute awal (pembanding)
    if initial_route is not None:
        r0 = rotate_to_depot(initial_route)
        r0 = r0 + [r0[0]]
        ax.plot([coords[i][0] for i in r0], [coords[i][1] for i in r0],
                color=P["sky"], lw=1.4, ls=(0, (4, 3)), alpha=0.8, zorder=1)

    # rute akhir + panah arah
    r = rotate_to_depot(route)
    closed = r + [r[0]]
    for a, b in zip(closed[:-1], closed[1:]):
        ax.annotate("", xy=coords[b], xytext=coords[a], zorder=2,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.55,head_width=0.28",
                                    color=P["coral"], lw=2.4,
                                    shrinkA=11, shrinkB=11))

    # titik kota bernomor
    order = {city: k + 1 for k, city in enumerate(r)}
    for i, (x, y) in enumerate(coords):
        depot = i == 0
        ax.scatter([x], [y], s=430 if depot else 300, zorder=4,
                   color=P["sun"] if depot else P["surface"],
                   edgecolors=P["ink"], linewidths=1.8)
        ax.text(x, y, "★" if depot else str(order[i]), ha="center", va="center",
                fontsize=11 if depot else 9, fontweight="bold", color=P["ink"], zorder=5)
        ax.annotate(names[i] + ("  · DEPOT" if depot else ""), (x, y),
                    xytext=(0, -19 if depot else 17), textcoords="offset points",
                    ha="center", va="top" if depot else "baseline",
                    fontsize=9, fontweight="bold", color=P["ink"],
                    path_effects=halo, zorder=6)

    ax.margins(0.14)
    handles = [Line2D([0], [0], color=P["coral"], lw=2.4, label="Rute akhir")]
    if initial_route is not None:
        handles.append(Line2D([0], [0], color=P["sky"], lw=1.4, ls=(0, (4, 3)),
                              label="Rute awal"))
    handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=P["sun"],
                          markeredgecolor=P["ink"], markersize=8, label="Depot"))
    ax.legend(handles=handles, loc="best", frameon=True, framealpha=0.95,
              facecolor=P["surface"], edgecolor=P["line"], fontsize=8, labelcolor=P["ink"])
    _heading(ax, title, subtitle)
    return fig


def plot_convergence(history, init_dist=None, title="Konvergensi", subtitle=None, ax=None):
    """Grafik konvergensi dari history (list of dict: iter, best_dist, current_dist).
    Return: matplotlib Figure."""
    fig, ax = _prepare_axes(ax, size=(7, 4))
    _style_axes(ax)

    if not history:
        ax.text(0.5, 0.5, "Tidak ada data konvergensi", transform=ax.transAxes,
                ha="center", va="center", color=P["muted"], fontsize=11)
        return fig

    it = [h["iter"] for h in history]
    best = [h["best_dist"] for h in history]
    cur = [h.get("current_dist", h["best_dist"]) for h in history]

    ax.plot(it, cur, color=P["sky"], lw=1.2, alpha=0.65, label="Solusi saat ini", zorder=2)
    ax.fill_between(it, best, min(best + cur), color=P["coral"], alpha=0.10, zorder=1)
    ax.plot(it, best, color=P["coral"], lw=2.8, label="Terbaik", zorder=3,
            solid_capstyle="round")
    if init_dist is not None:
        ax.axhline(init_dist, color=P["teal"], lw=1.3, ls=(0, (5, 3)), zorder=1,
                   label="Jarak awal")

    ax.scatter([it[-1]], [best[-1]], s=70, color=P["coral"], edgecolors=P["ink"],
               linewidths=1.5, zorder=5)
    ax.annotate(f"Terbaik {best[-1]:.2f}", (it[-1], best[-1]), xytext=(-10, 16),
                textcoords="offset points", ha="right", fontsize=9, fontweight="bold",
                color=P["ink"],
                path_effects=[pe.withStroke(linewidth=3, foreground=P["map_bg"])])

    ax.margins(x=0.05, y=0.08)
    ax.set_xlabel("Iterasi", color=P["muted"], fontsize=9, labelpad=8)
    ax.set_ylabel("Jarak", color=P["muted"], fontsize=9, labelpad=8)
    ax.legend(loc="upper right", frameon=True, framealpha=0.95, facecolor=P["surface"],
              edgecolor=P["line"], fontsize=8, labelcolor=P["ink"])
    _heading(ax, title, subtitle)
    return fig


def save_route_png(path, coords, names, route, initial_route=None,
                   title="Rute Optimal TSP", subtitle=None, dpi=200, **_ignored):
    """Simpan peta rute ke PNG (tidak butuh GUI / pyplot). Return path."""
    fig = Figure(figsize=(9, 7), facecolor=P["surface"])
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    plot_route(coords, names, route, initial_route, title=title,
               subtitle=subtitle, ax=ax)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    return path
