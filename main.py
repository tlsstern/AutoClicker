import tkinter as tk
from tkinter import ttk
import json
import os
import threading
from pynput import keyboard
from clicker import AutoClicker

CONFIG_FILE = "scripts.json"

# ─── Theme ──────────────────────────────────────────────────────────────────────
THEME = {
    "bg":           "#121212",
    "surface":      "#1E1E1E",
    "surface2":     "#252526",
    "border":       "#333333",
    "accent":       "#3B8ED0",
    "accent_hover": "#4D9FE3",
    "accent_dim":   "#2A6A9E",
    "success":      "#4CAF50",
    "error":        "#E53935",
    "text":         "#E0E0E0",
    "text_sec":     "#AAAAAA",
    "text_dim":     "#666666",
    "input_bg":     "#2D2D2D",
    "input_border": "#3E3E42",
}

FONT        = "Segoe UI"
FONT_MONO   = "Consolas"

# ─── Custom Widgets ─────────────────────────────────────────────────────────────

class AccentButton(tk.Canvas):
    """A modern, flat-style button drawn on a Canvas."""
    def __init__(self, master, text="", command=None, bg=None, fg=None,
                 hover_bg=None, font_spec=None, height=44, **kw):
        super().__init__(master, highlightthickness=0, bd=0, bg=THEME["bg"], **kw)
        self._text = text
        self._command = command
        self._bg = bg or THEME["accent"]
        self._fg = fg or "#FFFFFF"
        self._hover_bg = hover_bg or THEME["accent_hover"]
        self._font = font_spec or (FONT, 10, "bold")
        self._h = height
        self._radius = 6
        self._pressed = False

        self.configure(height=self._h)
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1+r, y1,   x2-r, y1,   x2, y1,   x2, y1+r,
            x2, y2-r,   x2, y2,     x2-r, y2,  x1+r, y2,
            x1, y2,     x1, y2-r,   x1, y1+r,  x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kw)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        
        bg = self._bg
        if self._pressed:
            bg = self._bg
            
        self._round_rect(0, 0, w, h, self._radius, fill=bg, outline="")
        self.create_text(w/2, h/2, text=self._text, fill=self._fg,
                         font=self._font, anchor="center")

    def _on_enter(self, e):
        self._bg_saved = self._bg
        self._bg = self._hover_bg
        self._draw()
        self.configure(cursor="hand2")

    def _on_leave(self, e):
        self._bg = getattr(self, '_bg_saved', self._bg)
        self._pressed = False
        self._draw()

    def _on_press(self, e):
        self._pressed = True
        self._draw()

    def _on_release(self, e):
        if self._pressed and self._command:
            self._command()
        self._pressed = False
        self._draw()

    def set_config(self, **kw):
        if "text" in kw:   self._text = kw["text"]
        if "bg" in kw:     self._bg = kw["bg"]
        if "fg" in kw:     self._fg = kw["fg"]
        if "hover_bg" in kw: self._hover_bg = kw["hover_bg"]
        self._draw()


class SmallButton(tk.Canvas):
    """Compact utility button (e.g., +, x, 🗑). Transparent unless hovered."""
    def __init__(self, master, text="", icon=None, command=None, fg=None, size=28, **kw):
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, bd=0, bg=THEME["surface"], **kw)
        self._text = text
        self._icon = icon
        self._command = command
        self._fg = fg or THEME["text_sec"]
        self._fg_hover = THEME["text"]
        self._size = size
        self._pressed = False
        self._hovering = False

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, event=None, fill_fg=None):
        self.delete("all")
        s = self._size
        color = fill_fg or self._fg

        if self._hovering:
            self.create_oval(2, 2, s-2, s-2, fill=THEME["surface2"], outline="")

        if self._icon == "trash":
            self._draw_trash(s, color)
        else:
            self.create_text(s/2, s/2, text=self._text, fill=color,
                            font=(FONT, 12, "bold"), anchor="center")

    def _draw_trash(self, s, color):
        cx, cy = s/2, s/2
        
        # Bin
        x1, y1 = cx - 5, cy - 4
        x2, y2 = cx + 5, cy + 8
        self.create_rectangle(x1, y1, x2, y2, outline=color, width=1.5)
        
        # Lid
        lx1, ly1 = cx - 6, cy - 6
        lx2, ly2 = cx + 6, cy - 4
        self.create_line(lx1, ly1, lx2, ly1, fill=color, width=1.5)
        # Handle
        hx1, hy1 = cx - 2, cy - 7   
        hx2, hy2 = cx + 2, cy - 7
        self.create_line(hx1, hy1, hx2, hy1, fill=color, width=1.5)

        self.create_line(cx-2, y1+2, cx-2, y2-2, fill=color, width=1)
        self.create_line(cx+2, y1+2, cx+2, y2-2, fill=color, width=1)

    def _hover(self, on):
        self._hovering = on
        self._draw(fill_fg=self._fg_hover if on else self._fg)
        self.configure(cursor="hand2" if on else "")
    
    def _on_press(self, e):
        self._pressed = True
    
    def _on_release(self, e):
        if self._pressed and self._command:
            self._command()
        self._pressed = False


# ─── Main Application ──────────────────────────────────────────────────────────

class AutoClickerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoClicker")
        self.geometry("420x600")
        self.resizable(False, False)
        self.configure(bg=THEME["bg"])

        # ── ttk Styles ──
        self.style = ttk.Style()
        self.style.theme_use('clam')

        S = THEME  # shortcut

        self.style.configure(".", background=S["bg"], foreground=S["text"],
                             font=(FONT, 10))
        self.style.configure("TFrame", background=S["bg"])
        self.style.configure("Card.TFrame", background=S["surface"])
        self.style.configure("TLabel", background=S["bg"], foreground=S["text"],
                             font=(FONT, 10))
        self.style.configure("Title.TLabel", font=(FONT, 20, "bold"),
                             foreground=S["text"], background=S["bg"])
        self.style.configure("Subtitle.TLabel", font=(FONT, 9),
                             foreground=S["text_sec"], background=S["bg"])
        self.style.configure("Section.TLabel", font=(FONT, 9, "bold"),
                             foreground=S["text_sec"], background=S["surface"])
        self.style.configure("Card.TLabel", background=S["surface"],
                             foreground=S["text_sec"], font=(FONT, 9))
        self.style.configure("Status.TLabel", font=(FONT, 12, "bold"),
                             background=S["surface"])

        # Entry
        self.style.configure("TEntry",
            fieldbackground=S["input_bg"], foreground=S["text"],
            insertcolor=S["text"], borderwidth=0, padding=10,
            relief="flat",
            bordercolor=S["input_bg"],
            lightcolor=S["input_bg"],
            darkcolor=S["input_bg"])
        self.style.map("TEntry",
            bordercolor=[("focus", S["accent"])], # Subtle hint if needed, or keep flat
            lightcolor=[("focus", S["accent"])],
            darkcolor=[("focus", S["accent"])])

        # Combobox
        self.style.configure("TCombobox",
            fieldbackground=S["input_bg"], background=S["input_bg"],
            foreground=S["text"], arrowcolor=S["text_sec"], arrowsize=14,
            borderwidth=0, padding=10, relief="flat",
            selectbackground=S["input_bg"], selectforeground=S["text"],
            bordercolor=S["input_bg"],
            lightcolor=S["input_bg"],
            darkcolor=S["input_bg"])
        self.style.map("TCombobox",
            fieldbackground=[("readonly", S["input_bg"])],
            selectbackground=[("readonly", S["input_bg"])],
            selectforeground=[("readonly", S["text"])],
            bordercolor=[("focus", S["input_bg"])],
            arrowcolor=[("pressed", S["text"]), ("active", S["text"])])

        # Dark dropdown popdown - Enhanced styling
        self.option_add('*TCombobox*Listbox.background', S["surface2"])
        self.option_add('*TCombobox*Listbox.foreground', S["text"])
        self.option_add('*TCombobox*Listbox.selectBackground', S["accent"])
        self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
        self.option_add('*TCombobox*Listbox.font', (FONT, 10))
        self.option_add('*TCombobox*Listbox.relief', 'flat')
        self.option_add('*TCombobox*Listbox.borderwidth', '0')
        self.option_add('*TCombobox*Listbox.highlightThickness', '0')

        # Global Scrollbar (Classic) - Fixes Combobox popdown scrollbar
        self.option_add('*Scrollbar.background', S["surface"])
        self.option_add('*Scrollbar.troughColor', S["bg"])
        self.option_add('*Scrollbar.highlightThickness', '0')
        self.option_add('*Scrollbar.activeBackground', S["accent"])
        self.option_add('*Scrollbar.borderWidth', '0')
        self.option_add('*Scrollbar.width', '12')

        # Radiobutton
        self.style.configure("TRadiobutton",
            background=S["surface"], foreground=S["text"],
            font=(FONT, 10), indicatorcolor=S["input_bg"], 
            padding=4)
        self.style.map("TRadiobutton",
            background=[("active", S["surface"])],
            indicatorcolor=[("selected", S["accent"])])

        # Scrollbar
        self.style.layout('Vertical.TScrollbar',
            [('Vertical.Scrollbar.trough',
              {'children': [('Vertical.Scrollbar.thumb',
                             {'expand': '1', 'sticky': 'nswe'})],
               'sticky': 'ns'})])
        self.style.configure("Vertical.TScrollbar",
            troughcolor=S["surface"], background=S["border"],
            borderwidth=0, relief="flat", arrowsize=0)
        self.style.map("Vertical.TScrollbar",
            background=[("active", S["text_sec"])])

        # ── Logic Init ──
        self.clicker = AutoClicker()
        self.config = self.load_config()
        self.script_names = []
        if self.config:
            self.clicker.set_button(self.config.get("click_button", "left"))

        self._pulse_on = True

        # ── UI ──
        self.create_widgets()

        # ── Listeners ──
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_status_loop()

    # ── Config I/O ──────────────────────────────────────────────────────────────

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {"normal_interval_ms": 100, "click_button": "left", "scripts": {}}
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"normal_interval_ms": 100, "click_button": "left", "scripts": {}}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    # ── Widget Construction ─────────────────────────────────────────────────────

    def create_widgets(self):
        S = THEME

        # ── Accent top bar ─────────────────────────────────
        accent_bar = tk.Canvas(self, height=3, bg=S["bg"], highlightthickness=0, bd=0)
        accent_bar.pack(fill=tk.X)
        accent_bar.bind("<Configure>",
            lambda e: accent_bar.delete("all") or
                      accent_bar.create_rectangle(0, 0, e.width, 3,
                                                  fill=S["accent"], outline=""))

        # ── Main container ─────────────────────────────────
        container = ttk.Frame(self, padding=(28, 22, 28, 20))
        container.pack(fill=tk.BOTH, expand=True)

        # ── Title Row ──────────────────────────────────────
        title_row = ttk.Frame(container)
        title_row.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(title_row, text="AutoClicker", style="Title.TLabel").pack(
            side=tk.LEFT, anchor="w")

        # ── Status Card ────────────────────────────────────
        status_card = ttk.Frame(container, style="Card.TFrame", padding=(20, 16))
        status_card.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(status_card, text="STATUS", style="Section.TLabel").pack(
            anchor="w")

        status_row = ttk.Frame(status_card, style="Card.TFrame")
        status_row.pack(fill=tk.X, pady=(12, 0))

        self.status_dot = tk.Canvas(status_row, width=12, height=12,
            bg=S["surface"], highlightthickness=0, bd=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 12))
        self.status_dot.create_oval(1, 1, 11, 11, fill=S["error"],
                                    outline="", tags="dot")

        self.status_var = tk.StringVar(value="STOPPED")
        self.lbl_status = ttk.Label(status_row, textvariable=self.status_var,
                                    style="Status.TLabel", foreground=S["error"])
        self.lbl_status.pack(side=tk.LEFT)

        # ── Configuration Card ─────────────────────────────
        ctrl_card = ttk.Frame(container, style="Card.TFrame", padding=(20, 16))
        ctrl_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        ttk.Label(ctrl_card, text="CONFIGURATION", style="Section.TLabel").pack(
            anchor="w", pady=(0, 16))

        # Mouse Button
        btn_frame = ttk.Frame(ctrl_card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=(0, 16))
        ttk.Label(btn_frame, text="Mouse Button", style="Card.TLabel").pack(
            anchor="w", pady=(0, 6))
        self.click_btn_var = tk.StringVar(
            value=self.config.get("click_button", "left").title())
        self.combo_btn = ttk.Combobox(btn_frame, textvariable=self.click_btn_var,
            state="readonly", values=["Left", "Right"], font=(FONT, 10))
        self.combo_btn.pack(fill=tk.X)
        self.combo_btn.bind("<<ComboboxSelected>>", self.on_btn_change)

        # Separator (Simplified)
        sep = tk.Frame(ctrl_card, height=1, bg=S["border"])
        sep.pack(fill=tk.X, pady=(4, 16))

        # Mode Radio
        mode_frame = ttk.Frame(ctrl_card, style="Card.TFrame")
        mode_frame.pack(fill=tk.X, pady=(0, 16))

        self.mode_var = tk.StringVar(value="fixed")
        ttk.Radiobutton(mode_frame, text="Fixed Interval",
                        variable=self.mode_var, value="fixed",
                        command=self.toggle_mode_ui).pack(side=tk.LEFT,
                                                          padx=(0, 24))
        ttk.Radiobutton(mode_frame, text="Script Mode",
                        variable=self.mode_var, value="sequence",
                        command=self.toggle_mode_ui).pack(side=tk.LEFT)

        # Dynamic Settings Area
        self.settings_frame = ttk.Frame(ctrl_card, style="Card.TFrame")
        self.settings_frame.pack(fill=tk.BOTH, expand=True)

        # ── Fixed Interval UI ──────────────────────────────
        self.frame_fixed = ttk.Frame(self.settings_frame, style="Card.TFrame")
        ttk.Label(self.frame_fixed, text="Interval (ms)", style="Card.TLabel").pack(
            anchor="w", pady=(0, 6))
        self.entry_interval = ttk.Entry(self.frame_fixed, font=(FONT, 11))
        self.entry_interval.insert(0, str(self.config.get("normal_interval_ms", 100)))
        self.entry_interval.pack(fill=tk.X)
        self.entry_interval.bind("<FocusOut>", self.save_interval)

        # ── Script Mode UI ─────────────────────────────────
        self.frame_script = ttk.Frame(self.settings_frame, style="Card.TFrame")

        # Script header (label + buttons)
        script_header = ttk.Frame(self.frame_script, style="Card.TFrame")
        script_header.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(script_header, text="Profile", style="Card.TLabel").pack(
            side=tk.LEFT)

        self.btn_del_profile = SmallButton(script_header, icon="trash",
            command=self.delete_profile, fg=S["error"])
        self.btn_cancel_new = SmallButton(script_header, text="✕",
            command=self.cancel_new_profile, fg=S["error"])
        self.btn_new_profile = SmallButton(script_header, text="+",
            command=self.show_new_profile_ui, fg=S["success"])
        self.btn_del_profile.pack(side=tk.RIGHT, padx=(4, 0))
        self.btn_new_profile.pack(side=tk.RIGHT, padx=(4, 0))

        # Selector row
        self.script_sel_frame = ttk.Frame(self.frame_script, style="Card.TFrame")
        self.script_sel_frame.pack(fill=tk.X, pady=(0, 12))

        self.combo_scripts = ttk.Combobox(self.script_sel_frame, state="readonly",
                                          font=(FONT, 10))
        self.combo_scripts.pack(fill=tk.X, expand=True)
        self.combo_scripts.bind("<<ComboboxSelected>>", self.on_script_change)

        self.entry_new_profile = ttk.Entry(self.script_sel_frame, font=(FONT, 10))
        self.entry_new_profile.bind("<Return>", lambda e: self.save_new_profile())
        self.entry_new_profile.bind("<FocusOut>", lambda e: self.save_new_profile())

        # Text editor
        ttk.Label(self.frame_script, text="Sequence (ms, comma-separated):",
                  style="Card.TLabel").pack(anchor="w", pady=(0, 6))
        editor_frame = tk.Frame(self.frame_script, bg=S["input_bg"],
                                bd=0, highlightthickness=0)
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        self.txt_script = tk.Text(editor_frame, height=5,
            bg=S["input_bg"], fg=S["text"], insertbackground=S["accent"],
            relief="flat", font=(FONT_MONO, 10), padx=12, pady=12,
            selectbackground=S["accent_dim"], selectforeground=S["text"],
            wrap=tk.WORD, bd=0, highlightthickness=0)
        self.txt_script.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.txt_script.bind("<FocusOut>", self.save_current_script_text)

        # Save button
        self.btn_save = AccentButton(self.frame_script, text="SAVE PROFILE",
            command=self.manual_save_script,
            bg=S["surface2"], fg=S["accent"], hover_bg=S["border"],
            font_spec=(FONT, 10, "bold"), height=42)
        self.btn_save.pack(fill=tk.X)

        # Populate scripts
        if self.config and "scripts" in self.config:
            self.script_names = list(self.config["scripts"].keys())
            self.combo_scripts['values'] = self.script_names
            if self.script_names:
                self.combo_scripts.current(0)
                self.on_script_change()

        # ── Footer ─────────────────────────────────────────
        self.btn_toggle = AccentButton(container, text="START CLICKING",
            command=self.toggle_clicking,
            bg=S["accent"], fg="#FFFFFF", hover_bg=S["accent_hover"],
            font_spec=(FONT, 12, "bold"), height=54)
        self.btn_toggle.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Label(container, text="Press F6 to toggle",
                  style="Subtitle.TLabel").pack(side=tk.BOTTOM, pady=(0, 12))

        # Init view
        self.toggle_mode_ui()

    # ── Mode Switching ──────────────────────────────────────────────────────────

    def toggle_mode_ui(self):
        if self.mode_var.get() == "fixed":
            self.frame_script.pack_forget()
            self.frame_fixed.pack(fill=tk.X)
            self.clicker.set_mode("fixed")
            self.geometry("420x600")
        else:
            self.frame_fixed.pack_forget()
            self.frame_script.pack(fill=tk.BOTH, expand=True)
            self.clicker.set_mode("sequence")
            self.geometry("420x720")

    # ── Event Handlers ──────────────────────────────────────────────────────────

    def on_btn_change(self, event=None):
        btn = self.click_btn_var.get().lower()
        self.clicker.set_button(btn)
        self.config["click_button"] = btn
        self.save_config()

    def save_interval(self, event=None):
        try:
            ms = int(self.entry_interval.get())
            self.config["normal_interval_ms"] = ms
            self.save_config()
        except ValueError:
            pass

    def on_script_change(self, event=None):
        idx = self.combo_scripts.current()
        if idx >= 0:
            name = self.script_names[idx]
            seq = self.config["scripts"][name]
            self.txt_script.delete("1.0", tk.END)
            self.txt_script.insert("1.0", ", ".join(map(str, seq)))
            self.update_settings()

    def save_current_script_text(self, event=None):
        idx = self.combo_scripts.current()
        if idx < 0:
            return
        name = self.script_names[idx]
        raw = self.txt_script.get("1.0", tk.END).replace("\n", ",")
        try:
            new_seq = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
            if new_seq:
                self.config["scripts"][name] = new_seq
                self.save_config()
                self.update_settings()
                return True
        except ValueError:
            pass
        return False

    def manual_save_script(self):
        if self.save_current_script_text():
            # Show success feedback
            self._show_save_success()
        else:
            self._show_save_error()

    def _show_save_error(self):
        """Show visual feedback that save failed."""
        S = THEME
        self.btn_save.set_config(
            text="⚠ INVALID!",
            bg=S["error"],
            fg="#FFFFFF",
            hover_bg=S["error"]
        )
        self.after(1500, lambda: self.btn_save.set_config(
            text="SAVE PROFILE",
            bg=S["surface2"],
            fg=S["accent"],
            hover_bg=S["border"]
        ))
    
    def _show_save_success(self):
        """Show visual feedback that save was successful."""
        S = THEME
        # Change button to success state
        self.btn_save.set_config(
            text="✓ SAVED!",
            bg=S["success"],
            fg="#000000",
            hover_bg=S["success"]
        )
        # Reset after 1.5 seconds
        self.after(1500, lambda: self.btn_save.set_config(
            text="SAVE PROFILE",
            bg=S["surface2"],
            fg=S["accent"],
            hover_bg=S["border"]
        ))

    # ── Profile Management ──────────────────────────────────────────────────────

    def show_new_profile_ui(self):
        try:
            # Ensure we're in Script Mode so the UI is visible
            if self.mode_var.get() != "sequence":
                self.mode_var.set("sequence")
                self.toggle_mode_ui()
            
            self.combo_scripts.pack_forget()
            self.btn_new_profile.pack_forget()
            self.btn_del_profile.pack_forget()

            self.entry_new_profile.pack(fill=tk.X, expand=True)
            self.entry_new_profile.delete(0, tk.END)
            self.entry_new_profile.focus()
            self.btn_cancel_new.pack(side=tk.RIGHT)
        except Exception as e:
            pass

    def cancel_new_profile(self):
        self.entry_new_profile.pack_forget()
        self.btn_cancel_new.pack_forget()

        self.combo_scripts.pack(fill=tk.X, expand=True)
        self.btn_del_profile.pack(side=tk.RIGHT, padx=(4, 0))
        self.btn_new_profile.pack(side=tk.RIGHT, padx=(4, 0))

    def save_new_profile(self):
        name = self.entry_new_profile.get().strip()
        if not name:
            self.cancel_new_profile()
            return
        if name in self.config["scripts"]:
            self.cancel_new_profile()
            return

        self.config["scripts"][name] = []
        self.save_config()

        self.entry_new_profile.pack_forget()
        self.btn_cancel_new.pack_forget()

        self.script_names = list(self.config["scripts"].keys())
        self.combo_scripts['values'] = self.script_names
        self.combo_scripts.pack(fill=tk.X, expand=True)
        self.btn_del_profile.pack(side=tk.RIGHT, padx=(4, 0))
        self.btn_new_profile.pack(side=tk.RIGHT, padx=(4, 0))
        
        try:
            idx = self.script_names.index(name)
            self.combo_scripts.current(idx)
            self.on_script_change()
        except ValueError:
            pass

    def delete_profile(self):
        idx = self.combo_scripts.current()
        if idx < 0:
            return
        name = self.script_names[idx]
        del self.config["scripts"][name]
        self.save_config()
        self.script_names = list(self.config["scripts"].keys())
        self.combo_scripts['values'] = self.script_names
        self.txt_script.delete("1.0", tk.END)
        if self.script_names:
            self.combo_scripts.current(0)
            self.on_script_change()
        else:
            self.combo_scripts.set("")

    # ── Clicker Control ─────────────────────────────────────────────────────────

    def update_settings(self):
        try:
            ms = float(self.entry_interval.get())
            if ms < 1:
                ms = 1
            self.clicker.set_delay(ms / 1000.0)
        except ValueError:
            pass

        if self.mode_var.get() == "sequence":
            idx = self.combo_scripts.current()
            if 0 <= idx < len(self.script_names):
                name = self.script_names[idx]
                seq_ms = self.config["scripts"][name]
                self.clicker.set_sequence([ms / 1000.0 for ms in seq_ms])

    def toggle_clicking(self):
        if self.clicker.running:
            self.clicker.stop_clicking()
            self.set_stopped_state()
        else:
            self.update_settings()
            self.clicker.start_clicking()
            self.set_running_state()

    def set_running_state(self):
        S = THEME
        self.status_var.set("ACTIVE")
        self.lbl_status.configure(foreground=S["success"])
        self.status_dot.itemconfigure("dot", fill=S["success"])
        self.btn_toggle.set_config(text="STOP AUTO CLICKER",
                                   bg=S["error"], hover_bg="#FF7F99")

    def set_stopped_state(self):
        S = THEME
        self.status_var.set("STOPPED")
        self.lbl_status.configure(foreground=S["error"])
        self.status_dot.itemconfigure("dot", fill=S["error"])
        self.btn_toggle.set_config(text="START AUTO CLICKER",
                                   bg=S["accent"], hover_bg=S["accent_hover"])

    def on_press(self, key):
        if key == keyboard.Key.f6:
            self.after(0, self.toggle_clicking)

    def update_status_loop(self):
        if self.clicker.running:
            self.set_running_state()
            # Pulse the status dot
            self._pulse_on = not self._pulse_on
            fill = THEME["success"] if self._pulse_on else THEME["surface"]
            self.status_dot.itemconfigure("dot", fill=fill)
        else:
            self.set_stopped_state()
        self.after(500, self.update_status_loop)

    def on_closing(self):
        self.clicker.exit()
        self.listener.stop()
        self.destroy()


if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
