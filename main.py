import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from pynput import keyboard
from clicker import AutoClicker

CONFIG_FILE = "scripts.json"

# --- Constants & Colors ---
BG_COLOR = "#121212"
SURFACE_COLOR = "#1e1e1e" 
ACCENT_COLOR = "#BB86FC" # Vivid Purple for modern feel
TEXT_MAIN = "#FFFFFF"
TEXT_SEC = "#B3B3B3"
BUTTON_BG = "#2C2C2C"
BUTTON_HOVER = "#3C3C3C"
ERROR_COLOR = "#CF6679"
SUCCESS_COLOR = "#03DAC6"

class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = kwargs.get('bg', BUTTON_BG)
        self.hover_bg = kwargs.get('activebackground', BUTTON_HOVER)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        self['background'] = self.hover_bg
        
    def on_leave(self, e):
        self['background'] = self.default_bg

class AutoClickerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoClicker Pro")
        self.geometry("400x550")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        
        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # General formatting
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background=SURFACE_COLOR, relief="flat")
        
        # Labels
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=TEXT_MAIN, background=BG_COLOR)
        self.style.configure("CardHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground=ACCENT_COLOR, background=SURFACE_COLOR)
        self.style.configure("Card.TLabel", background=SURFACE_COLOR, foreground=TEXT_SEC)
        
        # Status Label
        self.style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"), background=SURFACE_COLOR)

        # Inputs (Entry) - simple flat look
        self.style.configure("TEntry", fieldbackground=BUTTON_BG, foreground=TEXT_MAIN, insertcolor=TEXT_MAIN, borderwidth=0, padding=5)
        
        # Combobox
        self.style.configure("TCombobox", fieldbackground=BUTTON_BG, background=BUTTON_BG, foreground=TEXT_MAIN, arrowcolor=TEXT_MAIN, borderwidth=0, padding=5)
        self.style.map("TCombobox", fieldbackground=[("readonly", BUTTON_BG)], selectbackground=[("readonly", BUTTON_BG)], selectforeground=[("readonly", TEXT_MAIN)])

        # Custom Radio Styling (Hidden standard, custom visual could be done, but simple clean radio for now)
        self.style.configure("TRadiobutton", background=SURFACE_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 10), indicatorcolor=ACCENT_COLOR)
        self.style.map("TRadiobutton", background=[("active", SURFACE_COLOR)], indicatorcolor=[("selected", ACCENT_COLOR)])

        # --- Logic Init ---
        self.clicker = AutoClicker()
        self.config = self.load_config()
        self.script_names = []
        if self.config:
            self.clicker.set_button(self.config.get("click_button", "left"))

        # --- UI Construction ---
        self.create_widgets()
        
        # --- Listeners ---
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_status_loop()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def create_widgets(self):
        # Container with padding
        container = ttk.Frame(self, padding=25)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(container, text="AutoClicker", style="Header.TLabel")
        header.pack(pady=(0, 5), anchor="w")

        # --- Status Card ---
        self.status_card = ttk.Frame(container, style="Card.TFrame", padding=15)
        self.status_card.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(self.status_card, text="STATUS", style="CardHeader.TLabel").pack(anchor="w")
        
        self.status_var = tk.StringVar(value="STOPPED")
        self.lbl_status = ttk.Label(self.status_card, textvariable=self.status_var, style="Status.TLabel", foreground=ERROR_COLOR)
        self.lbl_status.pack(pady=(10, 0))
        
        # --- Controls Card ---
        controls_card = ttk.Frame(container, style="Card.TFrame", padding=15)
        controls_card.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(controls_card, text="CONFIGURATION", style="CardHeader.TLabel").pack(anchor="w", pady=(0, 10))
        
        # Mode Switcher
        self.mode_var = tk.StringVar(value="fixed")
        
        mode_frame = ttk.Frame(controls_card, style="Card.TFrame")
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Radiobutton(mode_frame, text="Fixed Interval", variable=self.mode_var, value="fixed", command=self.toggle_mode_ui).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="Script Mode", variable=self.mode_var, value="sequence", command=self.toggle_mode_ui).pack(side=tk.LEFT)

        # Dynamic Content Area
        self.settings_frame = ttk.Frame(controls_card, style="Card.TFrame")
        self.settings_frame.pack(fill=tk.X)

        # Fixed Interval Input
        self.frame_fixed = ttk.Frame(self.settings_frame, style="Card.TFrame")
        
        ttk.Label(self.frame_fixed, text="Interval (ms)", style="Card.TLabel", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))
        self.entry_interval = ttk.Entry(self.frame_fixed, font=("Segoe UI", 11))
        self.entry_interval.insert(0, str(self.config.get("normal_interval_ms", 100)))
        self.entry_interval.pack(fill=tk.X)

        # Script Selector
        self.frame_script = ttk.Frame(self.settings_frame, style="Card.TFrame")
        
        ttk.Label(self.frame_script, text="Select Profile", style="Card.TLabel", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))
        self.combo_scripts = ttk.Combobox(self.frame_script, state="readonly", font=("Segoe UI", 10))
        self.combo_scripts.pack(fill=tk.X)
        
        if self.config and "scripts" in self.config:
            self.script_names = list(self.config["scripts"].keys())
            self.combo_scripts['values'] = self.script_names
            if self.script_names:
                self.combo_scripts.current(0)

        # --- Footer Actions ---
        # Toggle Button
        self.btn_toggle = ModernButton(container, text="START AUTO CLICKER", command=self.toggle_clicking,
                                     bg=ACCENT_COLOR, fg="#000000",
                                     font=("Segoe UI", 11, "bold"), relief="flat", pady=12,
                                     activebackground="#7f5ac0", activeforeground="#000000", cursor="hand2")
        self.btn_toggle.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(container, text="Press F6 to Toggle", foreground=TEXT_SEC, font=("Segoe UI", 9)).pack(side=tk.BOTTOM, pady=(0, 10))

        # Init State
        self.toggle_mode_ui()

    def toggle_mode_ui(self):
        if self.mode_var.get() == "fixed":
            self.frame_script.pack_forget()
            self.frame_fixed.pack(fill=tk.X)
            self.clicker.set_mode("fixed")
        else:
            self.frame_fixed.pack_forget()
            self.frame_script.pack(fill=tk.X)
            self.clicker.set_mode("sequence")

    def update_settings(self):
        try:
            ms = float(self.entry_interval.get())
            if ms < 1: ms = 1
            self.clicker.set_delay(ms / 1000.0)
        except ValueError:
            pass 

        if self.mode_var.get() == "sequence":
            idx = self.combo_scripts.current()
            if idx >= 0 and idx < len(self.script_names):
                name = self.script_names[idx]
                sequence_ms = self.config["scripts"][name]
                sequence_sec = [ms / 1000.0 for ms in sequence_ms]
                self.clicker.set_sequence(sequence_sec)

    def toggle_clicking(self):
        if self.clicker.running:
            self.clicker.stop_clicking()
            self.set_stopped_state()
        else:
            self.update_settings()
            self.clicker.start_clicking()
            self.set_running_state()

    def set_running_state(self):
        self.status_var.set("ACTIVE")
        self.lbl_status.configure(foreground=SUCCESS_COLOR)
        self.btn_toggle.configure(text="STOP AUTO CLICKER", bg=ERROR_COLOR, activebackground="#b05565")

    def set_stopped_state(self):
        self.status_var.set("STOPPED")
        self.lbl_status.configure(foreground=ERROR_COLOR)
        self.btn_toggle.configure(text="START AUTO CLICKER", bg=ACCENT_COLOR, activebackground="#7f5ac0")

    def on_press(self, key):
        if key == keyboard.Key.f6:
            self.after(0, self.toggle_clicking)

    def update_status_loop(self):
        if self.clicker.running:
             self.set_running_state()
        else:
             self.set_stopped_state()
        self.after(200, self.update_status_loop)

    def on_closing(self):
        self.clicker.exit()
        self.listener.stop()
        self.destroy()

if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
