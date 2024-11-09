import customtkinter as ctk
from tkinter import ttk
import time
from plyer import notification
import threading
import pystray
from PIL import Image, ImageTk
import pickle
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
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
        self.is_paused = False
        self.is_expired = False
        self.last_notification = 0
        self.name = f"Timer {index + 1}"
        self.pause_time = 0
        self.start_time = 0
        self.elapsed_before_pause = 0  # Track time elapsed before pause
        # Initialize UI elements as None
        self.time_var = None
        self.label = None
        self.entry = None
        self.name_entry = None
        self.start_button = None
        self.stop_button = None
        self.clear_button = None

    def start(self):
        if not self.is_running and self.duration > 0:
            self.is_running = True
            self.is_expired = False
            self.is_paused = False
            self.start_time = time.time()
            self.elapsed_before_pause = 0
            threading.Thread(target=self.run, daemon=True).start()

    def pause(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            # Calculate time elapsed until pause
            self.elapsed_before_pause += time.time() - self.start_time
            self.pause_time = self.remaining

    def resume(self):
        if self.is_paused:
            self.is_paused = False
            self.start_time = time.time()  # Reset start time for new counting period
            threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self.elapsed_before_pause = 0
        self.start_time = 0

    def reset(self):
        self.stop()
        self.remaining = self.duration
        self.is_expired = False
        self.is_paused = False
        if self.app:
            self.app.update_display(self.index)

    def clear(self):
        self.stop()
        self.duration = 0
        self.remaining = 0
        self.is_expired = False
        self.is_paused = False
        if self.app:
            self.app.update_display(self.index)

    def run(self):
        while self.is_running and self.remaining > 0:
            if not self.is_paused:
                # Calculate remaining time considering both current period and previously elapsed time
                current_elapsed = time.time() - self.start_time
                total_elapsed = current_elapsed + self.elapsed_before_pause
                self.remaining = max(0, self.duration - int(total_elapsed))
                
                if self.app:
                    self.app.update_display(self.index)
            time.sleep(0.1)
        
        if self.is_running and not self.is_paused:
            self.is_expired = True
            self.is_running = False
            self.remaining = 0
            if self.app:
                self.app.update_display(self.index)
                self.app.show_notification(self.index)

class TimerApp:
    def __init__(self):
        self.timers = [Timer(self, i) for i in range(10)]
        self.root = None
        self.icon = None
        self.setup_icon()

    def setup_icon(self):
        try:
            icon_path = get_resource_path("kk.ico")
            if os.path.exists(icon_path):
                self.icon_image = Image.open(icon_path)
                menu = pystray.Menu(
                    pystray.MenuItem("Show", self.show_window),
                    pystray.MenuItem("Exit", self.quit_window)
                )
                self.icon = pystray.Icon("TimeBoss", self.icon_image, "TimeBoss", menu)
                threading.Thread(target=self.icon.run, daemon=True).start()
            else:
                print(f"Warning: Icon file not found at {icon_path}")
                # Create a default red icon as fallback
                self.icon_image = Image.new('RGB', (64, 64), color='red')
                menu = pystray.Menu(
                    pystray.MenuItem("Show", self.show_window),
                    pystray.MenuItem("Exit", self.quit_window)
                )
                self.icon = pystray.Icon("TimeBoss", self.icon_image, "TimeBoss", menu)
                threading.Thread(target=self.icon.run, daemon=True).start()
        except Exception as e:
            print(f"Error setting up icon: {e}")

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#1a1a1a", corner_radius=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        for i, timer in enumerate(self.timers):
            self.main_frame.grid_rowconfigure(i, weight=1)
            
            # Timer name entry
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

            # Time input entry
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

            # Start/Pause button
            timer.start_button = ctk.CTkButton(
                button_frame,
                text="Start",
                command=lambda t=timer: self.toggle_start_pause(t),
                height=32,
                fg_color="#2FA572",
                hover_color="#248c5e",
                corner_radius=5
            )
            timer.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

            # Stop/Reset button
            timer.stop_button = ctk.CTkButton(
                button_frame,
                text="Stop",
                command=lambda t=timer: self.toggle_stop_reset(t),
                height=32,
                fg_color="#D35B58",
                hover_color="#b34946",
                corner_radius=5
            )
            timer.stop_button.grid(row=0, column=1, padx=5, sticky="ew")

            # Clear button
            timer.clear_button = ctk.CTkButton(
                button_frame,
                text="Clear",
                command=lambda t=timer: self.clear_timer(t),
                height=32,
                fg_color="#586AD3",
                hover_color="#4657b3",
                corner_radius=5
            )
            timer.clear_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def toggle_start_pause(self, timer):
        if not timer.is_running:
            # Start timer
            try:
                # Parse the input time
                total_seconds = self.parse_time(timer.entry.get())
                timer.duration = total_seconds
                timer.remaining = timer.duration
                
                # Format the input field to show HH:MM:SS
                formatted_time = self.format_time(total_seconds)
                timer.entry.delete(0, 'end')
                timer.entry.insert(0, formatted_time)
                
                timer.name = timer.name_entry.get()
                timer.start()
                timer.start_button.configure(text="Pause")
                self.save_timers()
            except ValueError:
                timer.time_var.set("Invalid input")
        elif timer.is_running and not timer.is_paused:
            # Pause timer
            timer.pause()
            timer.start_button.configure(text="Resume")
        else:
            # Resume timer
            timer.resume()
            timer.start_button.configure(text="Pause")

    def toggle_stop_reset(self, timer):
        if timer.is_running or timer.is_paused:
            # Stop timer
            timer.stop()
            timer.stop_button.configure(text="Reset")
            timer.start_button.configure(text="Start")
        else:
            # Reset timer
            timer.reset()
            timer.stop_button.configure(text="Stop")
            timer.entry.delete(0, 'end')
            timer.entry.insert(0, self.format_time(timer.duration))

    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def parse_time(self, time_str):
        time_str = time_str.strip()
        try:
            # If it's just a number, treat as seconds
            if time_str.isdigit():
                seconds = int(time_str)
                return seconds

            # Handle MM:SS format
            if time_str.count(':') == 1:
                minutes, seconds = map(int, time_str.split(':'))
                return minutes * 60 + seconds

            # Handle HH:MM:SS format
            if time_str.count(':') == 2:
                hours, minutes, seconds = map(int, time_str.split(':'))
                return hours * 3600 + minutes * 60 + seconds

            # Try to parse any other numeric input as seconds
            return int(float(time_str))
        except (ValueError, TypeError):
            raise ValueError("Invalid time format")

    def clear_timer(self, timer):
        timer.clear()
        timer.entry.delete(0, 'end')
        timer.entry.insert(0, "hh:mm:ss")
        timer.start_button.configure(text="Start")
        timer.stop_button.configure(text="Stop")
        self.save_timers()

    def update_display(self, index):
        timer = self.timers[index]
        if timer.time_var is None:
            return
            
        if timer.is_expired:
            timer.time_var.set("EXPIRED")
            timer.label.configure(text_color="#D35B58")
        else:
            timer.time_var.set(self.format_time(timer.remaining))
            timer.label.configure(text_color="#ffffff")

    def show_notification(self, index):
        timer = self.timers[index]
        current_time = time.time()
        if current_time - timer.last_notification >= 60:
            try:
                if self.root and self.root.winfo_ismapped():
                    notification.notify(
                        title=f"{timer.name} Expired!",
                        message=f"{timer.name} has completed!",
                        app_name="TimeBoss",
                        timeout=10
                    )
                elif self.icon:
                    self.icon.notify(f"{timer.name} Expired!")
            except Exception as e:
                print(f"Error showing notification: {e}")
            timer.last_notification = current_time

    def check_expired_timers(self):
        current_time = time.time()
        for timer in self.timers:
            if timer.is_expired and current_time - timer.last_notification >= 60:
                self.show_notification(timer.index)
                timer.last_notification = current_time
        if self.root:
            self.root.after(1000, self.check_expired_timers)

    def show_window(self):
        if self.root is None:
            self.root = ctk.CTk()
            self.root.title("TimeBoss")
            self.root.geometry("800x400")
            self.root.minsize(900, 500)
            
            # Set window icon
            if hasattr(self, 'icon_image'):
                if sys.platform == "win32":
                    icon_path = get_resource_path("kk.ico")
                    self.root.iconbitmap(icon_path)
                else:
                    photo = ImageTk.PhotoImage(self.icon_image)
                    self.root.iconphoto(True, photo)
            
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
        if self.icon:
            self.icon.stop()

    def save_timers(self):
        timer_data = [
            (t.name, t.duration, t.remaining, t.is_running, t.is_expired, t.is_paused)
            for t in self.timers
        ]
        with open('timer_data.pkl', 'wb') as f:
            pickle.dump(timer_data, f)

    def load_timers(self):
        if os.path.exists('timer_data.pkl'):
            try:
                with open('timer_data.pkl', 'rb') as f:
                    timer_data = pickle.load(f)
                for i, data in enumerate(timer_data):
                    if len(data) == 5:  # Old format
                        name, duration, remaining, is_running, is_expired = data
                        is_paused = False
                    else:  # New format
                        name, duration, remaining, is_running, is_expired, is_paused = data
                    
                    self.timers[i].name = name
                    self.timers[i].duration = duration
                    self.timers[i].remaining = remaining
                    self.timers[i].is_running = is_running
                    self.timers[i].is_expired = is_expired
                    self.timers[i].is_paused = is_paused
                    
                    if is_running and not is_paused:
                        self.timers[i].start()
            except Exception as e:
                print(f"Error loading timer data: {e}")
                try:
                    os.remove('timer_data.pkl')
                except:
                    pass

    def run(self):
        self.load_timers()
        self.show_window()
        self.root.mainloop()

if __name__ == "__main__":
    app = TimerApp()
    app.run()