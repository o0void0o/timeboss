import customtkinter as ctk
from tkinter import ttk
import time
from plyer import notification
import threading
import pystray
from PIL import Image
import pickle
import os
from PIL import Image, ImageTk
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Timer:
    def __init__(self, app, index):
        self.app = app
        self.index = index
        self.duration = 0
        self.remaining = 0
        self.is_running = False
        self.is_expired = False
        self.last_notification = 0
        self.name = f"Timer {index + 1}"

    def start(self):
        if not self.is_running and self.duration > 0:
            self.is_running = True
            self.is_expired = False
            threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.is_running = False

    def clear(self):
        self.stop()
        self.duration = 0
        self.remaining = 0
        self.is_expired = False
        self.app.update_display(self.index)

    def run(self):
        start_time = time.time()
        while self.is_running and self.remaining > 0:
            self.remaining = max(0, self.duration - int(time.time() - start_time))
            self.app.update_display(self.index)
            time.sleep(0.1)
        
        if self.is_running:
            self.is_expired = True
            self.is_running = False
            self.remaining = 0
            self.app.update_display(self.index)
            self.app.show_notification(self.index)

class TimerApp:
    def __init__(self):
        self.timers = [Timer(self, i) for i in range(10)]
        self.root = None
       # Handle icon setting for both Windows and other platforms
        try:
            icon_path = get_resource_path("kk.ico")
            if os.path.exists(icon_path):
                if sys.platform == "win32":
                    # For Windows, use the .ico file
                    self.wm_iconbitmap(icon_path)
                else:
                    # For other platforms, convert ico to PhotoImage
                    icon = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(icon)
                    self.wm_iconphoto(True, photo)
        except Exception as e:
            print(f"Could not load icon: {e}")
        self.create_tray_icon()

    def create_widgets(self):
        # Configure the root window to expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame with dark background
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#1a1a1a", corner_radius=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure main frame grid
        self.main_frame.grid_columnconfigure(1, weight=1)  # Time display column should expand
        
        for i, timer in enumerate(self.timers):
            # Configure row weight
            self.main_frame.grid_rowconfigure(i, weight=1)
            
            # Timer name entry (dark gray background)
            timer.name_entry = ctk.CTkEntry(
                self.main_frame,
                placeholder_text=f"Timer {i+1}",
                width=120,
                height=32,
                fg_color="#2b2b2b",
                border_color="#404040",
                corner_radius=5
            )
            timer.name_entry.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            timer.name_entry.insert(0, timer.name)

            # Timer display
            timer.time_var = ctk.StringVar(value="00:00:00")
            timer.label = ctk.CTkLabel(
                self.main_frame,
                textvariable=timer.time_var,
                font=("Arial", 20),
                fg_color="transparent",
                anchor="center"
            )
            timer.label.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

            # Time input entry (dark gray background)
            timer.entry = ctk.CTkEntry(
                self.main_frame,
                placeholder_text="hh:mm:ss",
                width=120,
                height=32,
                fg_color="#2b2b2b",
                border_color="#404040",
                corner_radius=5
            )
            timer.entry.grid(row=i, column=2, padx=10, pady=5, sticky="ew")

            # Buttons frame
            button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            button_frame.grid(row=i, column=3, padx=10, pady=5, sticky="ew")
            button_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="button")

            # Create buttons with specific colors matching your screenshot
            timer.start_button = ctk.CTkButton(
                button_frame,
                text="Start",
                command=lambda t=timer: self.start_timer(t),
                height=32,
                fg_color="#2FA572",  # Green color
                hover_color="#248c5e",
                corner_radius=5
            )
            timer.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

            timer.stop_button = ctk.CTkButton(
                button_frame,
                text="Stop",
                command=lambda t=timer: self.stop_timer(t),
                height=32,
                fg_color="#D35B58",  # Red color
                hover_color="#b34946",
                corner_radius=5
            )
            timer.stop_button.grid(row=0, column=1, padx=5, sticky="ew")

            timer.clear_button = ctk.CTkButton(
                button_frame,
                text="Clear",
                command=lambda t=timer: self.clear_timer(t),
                height=32,
                fg_color="#586AD3",  # Blue color
                hover_color="#4657b3",
                corner_radius=5
            )
            timer.clear_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def parse_time(self, time_str):
        time_str = time_str.strip()
        if time_str.isdigit():
            return int(time_str)
        time_parts = time_str.split(':')
        if len(time_parts) == 2:
            minutes, seconds = map(int, time_parts)
            return minutes * 60 + seconds
        elif len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError("Invalid time format")

    def start_timer(self, timer):
        try:
            timer.duration = self.parse_time(timer.entry.get())
            timer.remaining = timer.duration
            timer.name = timer.name_entry.get()
            timer.start()
            self.save_timers()
        except ValueError:
            timer.time_var.set("Invalid input")

    def stop_timer(self, timer):
        timer.stop()
        self.save_timers()

    def clear_timer(self, timer):
        timer.clear()
        timer.entry.delete(0, 'end')
        timer.entry.insert(0, "hh:mm:ss")
        self.save_timers()

    def update_display(self, index):
        timer = self.timers[index]
        if timer.is_expired:
            timer.time_var.set("EXPIRED")
            timer.label.configure(text_color="#D35B58")  # Red color for expired
        else:
            hours, rem = divmod(timer.remaining, 3600)
            minutes, seconds = divmod(rem, 60)
            timer.time_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            timer.label.configure(text_color="#ffffff")  # White color for active

    def show_notification(self, index):
        timer = self.timers[index]
        current_time = time.time()
        if current_time - timer.last_notification >= 60:
            if self.root and self.root.winfo_ismapped():
                # Show notification only if the main window is visible
                notification.notify(
                    title=f"{timer.name} Expired!",
                    message=f"{timer.name} has completed!",
                    app_name="TimeBoss",
                    timeout=10
                )
            else:
                # Show notification through the tray icon
                self.icon.notify(f"{timer.name} Expired!")
            timer.last_notification = current_time

    def check_expired_timers(self):
        current_time = time.time()
        for timer in self.timers:
            if timer.is_expired and current_time - timer.last_notification >= 60:
                self.show_notification(timer.index)
                timer.last_notification = current_time
        self.root.after(1000, self.check_expired_timers)

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color = (255, 0, 0))
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.quit_window)
        )
        self.icon = pystray.Icon("timer_app", image, "Timer App", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self):
        if self.root is None:
            self.root = ctk.CTk()
            self.root.title("TimeBoss")
            self.root.geometry("800x400")  # Adjusted default size
            self.root.minsize(900, 500)    # Set minimum window size
            
            # Configure the appearance
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("dark-blue")
            
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
            self.create_widgets()
            self.check_expired_timers()
        self.root.deiconify()

    def hide_window(self):
        self.root.withdraw()

    def quit_window(self):
        self.save_timers()
        if self.root:
            self.root.quit()
        self.icon.stop()

    def save_timers(self):
        timer_data = [(t.name, t.duration, t.remaining, t.is_running, t.is_expired) for t in self.timers]
        with open('timer_data.pkl', 'wb') as f:
            pickle.dump(timer_data, f)

    def load_timers(self):
        if os.path.exists('timer_data.pkl'):
            with open('timer_data.pkl', 'rb') as f:
                timer_data = pickle.load(f)
            for i, (name, duration, remaining, is_running, is_expired) in enumerate(timer_data):
                self.timers[i].name = name
                self.timers[i].duration = duration
                self.timers[i].remaining = remaining
                self.timers[i].is_running = is_running
                self.timers[i].is_expired = is_expired
                if is_running:
                    self.timers[i].start()

    def run(self):
        self.load_timers()
        self.show_window()
        self.root.mainloop()

if __name__ == "__main__":
    app = TimerApp()
    app.run()