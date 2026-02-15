import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from pynput import keyboard
from clicker import AutoClicker

CONFIG_FILE = "scripts.json"

class AutoClickerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoClicker")
        self.geometry("350x400")
        self.resizable(False, False)

        self.clicker = AutoClicker()
        self.config = self.load_config()
        self.script_names = []
        
        # Apply default button config
        if self.config:
            self.clicker.set_button(self.config.get("click_button", "left"))

        self.create_widgets()
        
        # Hotkey Listener
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
        # Style
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=5)

        # Main Frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="AutoClicker", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # Status
        self.status_var = tk.StringVar(value="STOPPED")
        self.lbl_status = ttk.Label(main_frame, textvariable=self.status_var, foreground="red", font=("Segoe UI", 12, "bold"))
        self.lbl_status.pack(pady=(0, 20))

        # Mode Selection
        self.mode_var = tk.StringVar(value="fixed")
        
        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Fixed Interval", variable=self.mode_var, value="fixed", command=self.toggle_mode_ui).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Script Mode", variable=self.mode_var, value="sequence", command=self.toggle_mode_ui).pack(anchor=tk.W)

        # Fixed Interval UI
        self.frame_fixed = ttk.Frame(main_frame)
        self.frame_fixed.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.frame_fixed, text="Interval (ms):").pack(side=tk.LEFT)
        self.entry_interval = ttk.Entry(self.frame_fixed, width=10)
        self.entry_interval.insert(0, str(self.config.get("normal_interval_ms", 100)))
        self.entry_interval.pack(side=tk.LEFT, padx=5)

        # Script UI
        self.frame_script = ttk.Frame(main_frame)
        
        ttk.Label(self.frame_script, text="Select Script:").pack(anchor=tk.W)
        self.combo_scripts = ttk.Combobox(self.frame_script, state="readonly")
        self.combo_scripts.pack(fill=tk.X, pady=5)
        
        if self.config and "scripts" in self.config:
            self.script_names = list(self.config["scripts"].keys())
            self.combo_scripts['values'] = self.script_names
            if self.script_names:
                self.combo_scripts.current(0)
        
        # Start/Stop Info
        ttk.Label(main_frame, text="Press F6 to Start/Stop", font=("Segoe UI", 10, "italic")).pack(side=tk.BOTTOM, pady=10)

        # Initial UI State
        self.toggle_mode_ui()

    def toggle_mode_ui(self):
        if self.mode_var.get() == "fixed":
            self.frame_script.pack_forget()
            self.frame_fixed.pack(fill=tk.X, pady=10)
            self.clicker.set_mode("fixed")
        else:
            self.frame_fixed.pack_forget()
            self.frame_script.pack(fill=tk.X, pady=10)
            self.clicker.set_mode("sequence")

    def update_settings(self):
        # Update Fixed Delay
        try:
            ms = float(self.entry_interval.get())
            if ms < 1: ms = 1
            self.clicker.set_delay(ms / 1000.0)
        except ValueError:
            pass 

        # Update Sequence
        if self.mode_var.get() == "sequence":
            idx = self.combo_scripts.current()
            if idx >= 0:
                name = self.script_names[idx]
                sequence_ms = self.config["scripts"][name]
                sequence_sec = [ms / 1000.0 for ms in sequence_ms]
                self.clicker.set_sequence(sequence_sec)

    def toggle_clicking(self):
        if self.clicker.running:
            self.clicker.stop_clicking()
            self.status_var.set("STOPPED")
            self.lbl_status.configure(foreground="red")
        else:
            self.update_settings()
            self.clicker.start_clicking()
            self.status_var.set("RUNNING...")
            self.lbl_status.configure(foreground="green")

    def on_press(self, key):
        if key == keyboard.Key.f6:
            # Schedule toggle on main thread
            self.after(0, self.toggle_clicking)

    def update_status_loop(self):
        # Keep UI in sync if something else changes state (rare here but good practice)
        if self.clicker.running:
             self.status_var.set("RUNNING...")
             self.lbl_status.configure(foreground="green")
        else:
             self.status_var.set("STOPPED")
             self.lbl_status.configure(foreground="red")
        self.after(200, self.update_status_loop)

    def on_closing(self):
        self.clicker.exit()
        self.listener.stop()
        self.destroy()

if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
