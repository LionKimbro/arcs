"""Today's layered Tk surfaces and flat controls, translated into amber."""

from tkinter import ttk

COLORS = {
    "app": "#211508", "top": "#2E1F0C", "panel": "#382810",
    "control": "#453418", "editor": "#251B0C", "border": "#806029",
    "divider": "#55401A", "primary-text": "#F7EFE0",
    "secondary-text": "#CCB894", "muted-text": "#AB9167",
    "accent": "#FFBD4C", "hover": "#62491E", "selection": "#8A601E",
}


def install_amber_theme_for_tk_windows(root):
    root.configure(background=COLORS["app"])
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=COLORS["panel"], foreground=COLORS["primary-text"],
                    font=("TkDefaultFont", 10), bordercolor=COLORS["border"],
                    lightcolor=COLORS["control"], darkcolor=COLORS["control"])
    style.configure("TFrame", background=COLORS["panel"])
    style.configure("App.TFrame", background=COLORS["app"])
    style.configure("Top.TFrame", background=COLORS["top"])
    style.configure("TLabel", background=COLORS["panel"], foreground=COLORS["primary-text"])
    style.configure("Muted.TLabel", foreground=COLORS["secondary-text"])
    style.configure("UUID.TLabel", foreground=COLORS["muted-text"], font=("Consolas", 10))
    style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"))
    style.configure("Heading.TLabel", font=("TkDefaultFont", 12, "bold"))
    style.configure("Top.Title.TLabel", background=COLORS["top"])
    style.configure("App.Muted.TLabel", background=COLORS["app"])
    style.configure("TButton", background=COLORS["control"], padding=(10, 6),
                    relief="flat", borderwidth=1, focusthickness=1, focuscolor=COLORS["accent"])
    style.map("TButton", background=[("disabled", COLORS["top"]), ("pressed", COLORS["divider"]),
                                      ("active", COLORS["hover"])],
              foreground=[("disabled", COLORS["muted-text"])],
              bordercolor=[("focus", COLORS["accent"]), ("active", COLORS["border"])])
    style.configure("Primary.TButton", background=COLORS["accent"], foreground=COLORS["app"])
    style.map("Primary.TButton", background=[("disabled", COLORS["control"]),
                                              ("pressed", "#DFA13B"), ("active", "#FFCD75")],
              foreground=[("disabled", COLORS["muted-text"]), ("!disabled", COLORS["app"])])
    style.configure("TEntry", fieldbackground=COLORS["editor"], insertcolor=COLORS["primary-text"],
                    padding=(8, 6), selectbackground=COLORS["selection"],
                    selectforeground=COLORS["primary-text"])
    style.map("TEntry", fieldbackground=[("disabled", COLORS["top"])],
              foreground=[("disabled", COLORS["muted-text"])],
              bordercolor=[("focus", COLORS["accent"])])
    style.configure("TCombobox", fieldbackground=COLORS["editor"], background=COLORS["control"],
                    foreground=COLORS["primary-text"], arrowcolor=COLORS["secondary-text"], padding=(8, 6))
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["editor"])],
              foreground=[("readonly", COLORS["primary-text"])], bordercolor=[("focus", COLORS["accent"])])
    for option, value in {"background": COLORS["control"], "foreground": COLORS["primary-text"],
                          "selectBackground": COLORS["selection"], "selectForeground": COLORS["primary-text"]}.items():
        root.option_add("*TCombobox*Listbox." + option, value)
    for name in ("TCheckbutton", "TRadiobutton"):
        style.configure(name, background=COLORS["panel"], foreground=COLORS["primary-text"],
                        indicatorbackground=COLORS["editor"], indicatorforeground=COLORS["accent"])
        style.map(name, background=[("active", COLORS["panel"])],
                  indicatorbackground=[("selected", COLORS["accent"]), ("active", COLORS["control"])])
    style.configure("TPanedwindow", background=COLORS["divider"], sashwidth=6, relief="flat")
    style.configure("Sash", background=COLORS["divider"], sashthickness=6)
    style.map("Sash", background=[("active", COLORS["border"])])
    style.configure("Treeview", background=COLORS["editor"], fieldbackground=COLORS["editor"],
                    rowheight=28, borderwidth=0)
    style.map("Treeview", background=[("selected", COLORS["selection"])],
              foreground=[("selected", COLORS["primary-text"])])
    style.configure("Treeview.Heading", background=COLORS["control"],
                    foreground=COLORS["secondary-text"], font=("TkDefaultFont", 10, "bold"),
                    relief="flat", padding=(8, 6))
    style.map("Treeview.Heading", background=[("active", COLORS["hover"])])
    for direction in ("Vertical", "Horizontal"):
        name = direction + ".TScrollbar"
        style.configure(name, background=COLORS["control"], troughcolor=COLORS["editor"],
                        arrowcolor=COLORS["secondary-text"], borderwidth=0)
        style.map(name, background=[("active", COLORS["divider"])],
                  arrowcolor=[("active", COLORS["primary-text"])])
    for kind in ("Text", "Entry"):
        for option, value in {
                "background": COLORS["editor"], "foreground": COLORS["primary-text"],
                "insertBackground": COLORS["primary-text"], "selectBackground": COLORS["selection"],
                "selectForeground": COLORS["primary-text"], "relief": "flat", "borderWidth": 0,
                "highlightThickness": 1, "highlightBackground": COLORS["border"],
                "highlightColor": COLORS["accent"]}.items():
            root.option_add("*" + kind + "." + option, value)
    root.option_add("*Entry.disabledBackground", COLORS["top"])
    root.option_add("*Entry.disabledForeground", COLORS["muted-text"])
    root.option_add("*Text.padX", 8)
    root.option_add("*Text.padY", 6)
    root.option_add("*Canvas.background", COLORS["panel"])
    root.option_add("*Toplevel.background", COLORS["app"])
