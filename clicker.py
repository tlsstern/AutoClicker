import threading
import time
import pyautogui
from pynput.mouse import Button, Controller

class AutoClicker:
    def __init__(self):
        self.running = False
        self.program_running = True
        self.delay = 0.1
        self.mode = "fixed"
        self.sequence_delays = []
        self.sequence_index = 0
        
        self.button = Button.left
        self.thread = threading.Thread(target=self.click_loop, daemon=True)
        self.thread.start()
        self.mouse = Controller()

    def start_clicking(self):
        self.running = True
        self.sequence_index = 0

    def stop_clicking(self):
        self.running = False

    def exit(self):
        self.stop_clicking()
        self.program_running = False
        self.thread.join()

    def set_delay(self, delay):
        self.delay = delay

    def set_mode(self, mode):
        self.mode = mode

    def set_sequence(self, sequence):
        self.sequence_delays = sequence
        self.sequence_index = 0

    def set_button(self, button_str):
        if button_str.lower() == "left":
            self.button = Button.left
        elif button_str.lower() == "right":
            self.button = Button.right
    
    def wait(self, duration):
        """Sleeps for 'duration' seconds but checks running state frequently."""
        end_time = time.time() + duration
        while time.time() < end_time:
            if not self.running or not self.program_running:
                return
            time.sleep(0.01)

    def click_loop(self):
        while self.program_running:
            if self.running:
                delay = self.delay
                if self.mode == "sequence" and self.sequence_delays:
                     delay = self.sequence_delays[self.sequence_index]
                     self.sequence_index = (self.sequence_index + 1) % len(self.sequence_delays)
                
                self.mouse.click(self.button)
                self.wait(delay)
            else:
                time.sleep(0.1)
