"""Colors, fonts and ttk styles shared by the whole app."""
import sys
from tkinter import font as tkfont
from tkinter import ttk

BG = "#FFFFFF"
SIDEBAR = "#F8FAFC"
SUBTLE = "#F2F5F9"
HOVER = "#EDF1F6"
BORDER = "#E2E7EE"
DIVIDER = "#EEF1F5"
TEXT = "#1A1A1A"
MUTED = "#64748B"
PRIMARY = "#1F3A5F"
PRIMARY_HOVER = "#2B4C78"
PRIMARY_DISABLED = "#A7B4C6"
SELECT = "#E3EAF4"
ZEBRA = "#FAFBFD"
TOAST = "#1F2937"

# (background, foreground) pairs for badges, banners and row colors
KINDS = {
    "red": ("#FDECEC", "#B42318"),
    "amber": ("#FEF4E6", "#B54708"),
    "green": ("#E7F6EC", "#067647"),
    "blue": ("#E8F0FB", "#1F3A5F"),
}

IS_MAC = sys.platform == "darwin"
FONTS = {}


def _family(root):
    available = set(tkfont.families(root))
    for name in ("Inter", "Segoe UI", "Helvetica Neue", "Helvetica", "DejaVu Sans", "Arial"):
        if name in available:
            return name
    return "TkDefaultFont"


def setup(root):
    family = _family(root)
    scale = 1.3 if IS_MAC else 1.0  # macOS Tk renders points smaller

    def f(size, weight="normal"):
        return (family, round(size * scale), weight)

    FONTS.update(
        body=f(10), body_b=f(10, "bold"), small=f(9), small_b=f(9, "bold"),
        h1=f(18, "bold"), h2=f(11, "bold"), stat=f(20, "bold"), brand=f(12, "bold"),
    )
    root.option_add("*Font", FONTS["body"])
    root.option_add("*TCombobox*Listbox.font", FONTS["body"])
    root.option_add("*TCombobox*Listbox.background", BG)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", SELECT)
    root.option_add("*TCombobox*Listbox.selectForeground", TEXT)

    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TEXT, font=FONTS["body"], bordercolor=BORDER,
                lightcolor=BG, darkcolor=BG, troughcolor=BG, focuscolor=BG)

    # buttons
    btn = dict(padding=(16, 8), relief="flat", borderwidth=1, font=FONTS["body_b"])
    s.configure("Primary.TButton", background=PRIMARY, foreground="#FFFFFF", bordercolor=PRIMARY,
                lightcolor=PRIMARY, darkcolor=PRIMARY, **btn)
    s.map("Primary.TButton",
          background=[("disabled", PRIMARY_DISABLED), ("active", PRIMARY_HOVER)],
          bordercolor=[("disabled", PRIMARY_DISABLED), ("active", PRIMARY_HOVER)],
          lightcolor=[("disabled", PRIMARY_DISABLED), ("active", PRIMARY_HOVER)],
          darkcolor=[("disabled", PRIMARY_DISABLED), ("active", PRIMARY_HOVER)],
          foreground=[("disabled", "#FFFFFF")])
    for name, fg in (("Secondary", TEXT), ("Danger", KINDS["red"][1])):
        s.configure(f"{name}.TButton", background=BG, foreground=fg, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, **btn)
        s.map(f"{name}.TButton", background=[("disabled", BG), ("active", SUBTLE)],
              lightcolor=[("active", SUBTLE)], darkcolor=[("active", SUBTLE)],
              foreground=[("disabled", "#B4BDC9")])
    red_bg, red = "#C0392B", KINDS["red"][1]
    s.configure("DangerSolid.TButton", background=red_bg, foreground="#FFFFFF", bordercolor=red_bg,
                lightcolor=red_bg, darkcolor=red_bg, **btn)
    s.map("DangerSolid.TButton", background=[("active", red)], bordercolor=[("active", red)],
          lightcolor=[("active", red)], darkcolor=[("active", red)])

    # inputs
    field = dict(fieldbackground=SUBTLE, foreground=TEXT, bordercolor=BORDER, lightcolor=SUBTLE,
                 darkcolor=SUBTLE, padding=7, insertcolor=TEXT)
    s.configure("TEntry", **field)
    s.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", SUBTLE)])
    s.configure("TCombobox", background=SUBTLE, arrowcolor=MUTED, arrowsize=14, **field)
    s.map("TCombobox", bordercolor=[("focus", PRIMARY)],
          fieldbackground=[("readonly", SUBTLE)], background=[("readonly", SUBTLE), ("active", SUBTLE)],
          selectbackground=[("readonly", SUBTLE), ("!focus", SUBTLE)],
          selectforeground=[("readonly", TEXT), ("!focus", TEXT)])
    s.configure("TSpinbox", background=SUBTLE, arrowcolor=MUTED, arrowsize=12, **field)
    s.map("TSpinbox", bordercolor=[("focus", PRIMARY)])
    s.configure("TCheckbutton", background=BG, foreground=TEXT, indicatorbackground=BG,
                indicatorforeground=PRIMARY, indicatormargin=(0, 0, 8, 0))
    s.map("TCheckbutton", background=[("active", BG)],
          indicatorbackground=[("selected", BG), ("active", SUBTLE)])

    # tables
    s.configure("Treeview", background=BG, fieldbackground=BG, foreground=TEXT, borderwidth=0,
                rowheight=34 if IS_MAC else 30, font=FONTS["body"])
    s.map("Treeview", background=[("selected", SELECT)], foreground=[("selected", TEXT)])
    s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    s.configure("Treeview.Heading", background=SUBTLE, foreground=MUTED, font=FONTS["small_b"],
                relief="flat", padding=(10, 8), bordercolor=BORDER, lightcolor=SUBTLE, darkcolor=SUBTLE)
    s.map("Treeview.Heading", background=[("active", SUBTLE)])
    s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG, bordercolor=BG,
                arrowcolor=MUTED, lightcolor=BORDER, darkcolor=BORDER, gripcount=0, arrowsize=12)

    # tabs
    s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
    s.configure("TNotebook.Tab", background=BG, foreground=MUTED, padding=(14, 8), borderwidth=0,
                font=FONTS["body_b"], bordercolor=BG, lightcolor=BG)
    s.map("TNotebook.Tab", foreground=[("selected", PRIMARY)], background=[("selected", BG)],
          lightcolor=[("selected", BG)], expand=[("selected", (0, 0, 0, 0))])
    return s


def bg_of(kind):
    return KINDS[kind][0]


def fg_of(kind):
    return KINDS[kind][1]
