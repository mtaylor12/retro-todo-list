"""
Classic Notepad Checklist
A compact sticky-note style checklist with a vintage Mac feel.
Remembers your items between sessions using a local JSON file.

Requirements: Python 3.x (tkinter is included with Python)
To build .exe: pyinstaller --onefile --windowed notepad.py
"""

import tkinter as tk
from tkinter import font as tkfont
import json
import os
import sys

# ── Data file sits next to the .exe / script ─────────────────────────────────
_base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(_base, "notepad_data.json")

# ── Colours (classic Mac System 7 palette) ────────────────────────────────────
BG_WINDOW   = "#DDDDDD"   # classic light grey window chrome
BG_TITLEBAR = "#000000"   # black title bar
FG_TITLE    = "#FFFFFF"   # white title text
BG_PAPER    = "#FFFFEF"   # warm off-white notepad body
BG_ENTRY    = "#FFFFFF"
FG_NORMAL   = "#000000"
FG_CHECKED  = "#999999"
BG_BUTTON   = "#BBBBBB"
BG_BTN_ACT  = "#888888"
BORDER      = "#444444"
RULE        = "#CCCCCC"


class NotepadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notepad")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_WINDOW)

        # Remove default title bar and draw our own (classic Mac style)
        self.root.overrideredirect(True)

        # Keep window on top optionally — comment out if unwanted
        # self.root.attributes("-topmost", True)

        # Centre on screen
        w, h = 280, 380
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Track drag offset for moving the window
        self._drag_x = 0
        self._drag_y = 0

        # Item data: list of {"text": str, "checked": bool}
        self.items = []
        self.item_widgets = []   # list of (frame, var, cb, label) tuples

        self._build_ui()
        self._load()
        self._refresh_list()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Custom title bar ──────────────────────────────────────────────────
        self.titlebar = tk.Frame(self.root, bg=BG_TITLEBAR, height=22)
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.pack_propagate(False)

        # Close box (classic Mac square button top-left)
        close_box = tk.Label(
            self.titlebar, text=" ■ ", bg=BG_TITLEBAR, fg=FG_TITLE,
            cursor="hand2", font=("Courier", 9))
        close_box.pack(side="left", padx=4)
        close_box.bind("<Button-1>", lambda e: self.root.destroy())

        title_lbl = tk.Label(
            self.titlebar, text="✎  Notepad",
            bg=BG_TITLEBAR, fg=FG_TITLE,
            font=("Helvetica", 10, "bold"))
        title_lbl.pack(side="left", padx=4)

        # Drag to move
        for widget in (self.titlebar, title_lbl):
            widget.bind("<ButtonPress-1>",   self._drag_start)
            widget.bind("<B1-Motion>",       self._drag_move)

        # ── Paper body ────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG_PAPER, bd=2, relief="sunken")
        body.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Scrollable checklist area ─────────────────────────────────────────
        list_frame_outer = tk.Frame(body, bg=BG_PAPER)
        list_frame_outer.pack(fill="both", expand=True, padx=4, pady=(6, 2))

        self.canvas = tk.Canvas(
            list_frame_outer, bg=BG_PAPER,
            highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(
            list_frame_outer, orient="vertical",
            command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.list_frame = tk.Frame(self.canvas, bg=BG_PAPER)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",     self._on_canvas_configure)

        # Mouse wheel scroll
        self.canvas.bind_all("<MouseWheel>",   self._on_mousewheel)
        self.canvas.bind_all("<Button-4>",     self._on_mousewheel)
        self.canvas.bind_all("<Button-5>",     self._on_mousewheel)

        # ── Divider ───────────────────────────────────────────────────────────
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=4, pady=2)

        # ── Add item row ──────────────────────────────────────────────────────
        add_row = tk.Frame(body, bg=BG_PAPER)
        add_row.pack(fill="x", padx=4, pady=(2, 4))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            add_row, textvariable=self.entry_var,
            bg=BG_ENTRY, fg=FG_NORMAL,
            relief="sunken", bd=2,
            font=("Geneva", 10),
            insertbackground=FG_NORMAL)
        self.entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.entry.bind("<Return>", lambda e: self._add_item())

        add_btn = self._make_button(add_row, "Add", self._add_item)
        add_btn.pack(side="left", padx=(4, 0))

        # ── Bottom buttons ────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=BG_PAPER)
        btn_row.pack(fill="x", padx=4, pady=(0, 6))

        self._make_button(
            btn_row, "Delete Checked", self._delete_checked,
            width=14
        ).pack(side="left")

    def _make_button(self, parent, text, command, width=None):
        """Classic Mac-style raised button."""
        kwargs = dict(
            text=text, command=command,
            bg=BG_BUTTON, fg=FG_NORMAL,
            activebackground=BG_BTN_ACT,
            relief="raised", bd=2,
            font=("Geneva", 9),
            cursor="hand2",
            padx=4, pady=2)
        if width:
            kwargs["width"] = width
        return tk.Button(parent, **kwargs)

    # ── Checklist rendering ───────────────────────────────────────────────────

    def _refresh_list(self):
        """Rebuild the checklist from self.items."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.item_widgets.clear()

        for i, item in enumerate(self.items):
            self._add_item_row(i, item["text"], item["checked"])

        self._update_scroll()

    def _add_item_row(self, index, text, checked):
        var = tk.BooleanVar(value=checked)

        row = tk.Frame(self.list_frame, bg=BG_PAPER)
        row.pack(fill="x", pady=1)

        # Draw a subtle horizontal rule every other row
        if index % 2 == 0:
            row.configure(bg="#F5F5E8")

        cb = tk.Checkbutton(
            row, variable=var,
            bg=row.cget("bg"),
            activebackground=row.cget("bg"),
            command=lambda i=index, v=var: self._on_check(i, v))
        cb.pack(side="left")

        lbl_font = tkfont.Font(family="Geneva", size=10)
        lbl = tk.Label(
            row, text=text,
            bg=row.cget("bg"),
            font=lbl_font,
            anchor="w")
        lbl.pack(side="left", fill="x", expand=True)

        self._apply_check_style(lbl, lbl_font, checked)
        self.item_widgets.append((row, var, cb, lbl, lbl_font))

    def _apply_check_style(self, label, fnt, checked):
        if checked:
            fnt.configure(overstrike=True)
            label.configure(fg=FG_CHECKED)
        else:
            fnt.configure(overstrike=False)
            label.configure(fg=FG_NORMAL)

    def _on_check(self, index, var):
        self.items[index]["checked"] = var.get()
        _, _, _, lbl, fnt = self.item_widgets[index]
        self._apply_check_style(lbl, fnt, var.get())
        self._save()

    # ── Add / Delete ──────────────────────────────────────────────────────────

    def _add_item(self):
        text = self.entry_var.get().strip()
        if not text:
            return
        self.items.append({"text": text, "checked": False})
        self.entry_var.set("")
        self._refresh_list()
        self._save()
        # Scroll to bottom so the new item is visible
        self.canvas.after(50, lambda: self.canvas.yview_moveto(1.0))

    def _delete_checked(self):
        self.items = [item for item in self.items if not item["checked"]]
        self._refresh_list()
        self._save()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Basic validation
                if isinstance(data, list):
                    self.items = [
                        {"text": str(d.get("text", "")),
                         "checked": bool(d.get("checked", False))}
                        for d in data if isinstance(d, dict)
                    ]
            except Exception as e:
                print(f"Load error: {e}")
                self.items = []

    # ── Scroll helpers ────────────────────────────────────────────────────────

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _update_scroll(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ── Window drag ───────────────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = NotepadApp(root)
    root.mainloop()