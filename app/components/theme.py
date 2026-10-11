"""
app/components/theme.py
Palet warna + font bersama untuk GUI dan peta (satu sumber supaya konsisten).
Tema: "peta kertas" -- krem hangat, tinta navy, aksen coral & teal.
"""

P = {
    "bg":        "#F5EFE3",   # latar aplikasi (krem)
    "surface":   "#FFFFFF",   # kartu
    "surface2":  "#FBF8F2",   # kartu sekunder / input
    "line":      "#E4DCCB",   # garis tipis / border
    "ink":       "#1E2A3A",   # teks utama
    "muted":     "#6B7686",   # teks sekunder
    "coral":     "#FF6B4A",   # aksen utama (tombol, rute)
    "coral_dk":  "#E5502F",
    "coral_lt":  "#FFE3DB",
    "teal":      "#14A3A0",   # aksen kedua
    "teal_dk":   "#0E8683",
    "teal_lt":   "#D8F1F0",
    "sun":       "#FFC247",   # kuning (depot / highlight)
    "sky":       "#7A8CA8",   # garis "current"
    "grass":     "#2EA86B",   # tanda perbaikan
    "map_bg":    "#FFFDF8",
    "grid":      "#EDE5D4",
}

# Urutan preferensi font. Dipilih yang pertama tersedia di komputer pengguna.
HEAD_FONTS = ["Bahnschrift SemiBold", "Bahnschrift", "Segoe UI Semibold", "Segoe UI", "Arial"]
BODY_FONTS = ["Segoe UI", "Calibri", "Arial"]
MONO_FONTS = ["Cascadia Mono", "Consolas", "Courier New"]

_FONT = {"head": "Segoe UI", "body": "Segoe UI", "mono": "Consolas"}


def init_fonts():
    """Panggil SETELAH jendela Tk dibuat. Memilih font yang benar-benar terpasang."""
    from tkinter import font as tkfont
    have = set(tkfont.families())

    def pick(cands):
        for c in cands:
            if c in have:
                return c
        return cands[-1]

    _FONT["head"] = pick(HEAD_FONTS)
    _FONT["body"] = pick(BODY_FONTS)
    _FONT["mono"] = pick(MONO_FONTS)


def fh(size, weight="bold"):
    """Font judul / angka besar."""
    if "SemiBold" in _FONT["head"] or "Semibold" in _FONT["head"]:
        weight = "normal"
    return (_FONT["head"], size, weight)


def fb(size, weight="normal"):
    """Font isi."""
    return (_FONT["body"], size, weight)


def fm(size, weight="normal"):
    """Font monospace."""
    return (_FONT["mono"], size, weight)


def apply_mpl_style():
    """Gaya dasar matplotlib supaya grafik senada dengan GUI."""
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Calibri", "Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
    })
