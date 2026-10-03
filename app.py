import os
import sys
import time
import threading
import ctypes
from ctypes import wintypes
import pyautogui
import tkinter as tk
from tkinter import ttk

# Disable PyAutoGUI's fail-safe to prevent accidental crashes
pyautogui.FAILSAFE = False

PREFERRED_ICON = "keystroke2.ico"
FALLBACK_ICON = "keystroke.ico"
KEYSYM_TO_PYAUTOGUI = {
    "backspace": "backspace",
    "caps_lock": "capslock",
    "control_l": "ctrlleft",
    "control_r": "ctrlright",
    "escape": "esc",
    "return": "enter",
    "shift_l": "shiftleft",
    "shift_r": "shiftright",
    "alt_l": "altleft",
    "alt_r": "altright",
    "prior": "pageup",
    "next": "pagedown",
}
KEY_LABELS = {
    "shiftleft": "Left Shift",
    "shiftright": "Right Shift",
    "ctrlleft": "Left Ctrl",
    "ctrlright": "Right Ctrl",
    "altleft": "Left Alt",
    "altright": "Right Alt",
    "enter": "Enter",
    "esc": "Escape",
    "space": "Space",
    "pageup": "Page Up",
    "pagedown": "Page Down",
}


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class KeystrokeSimulator:
    def __init__(self, interval, activity_methods, keyboard_key, mouse_mode="nudge", mouse_position=None):
        self.interval = interval
        self.activity_methods = activity_methods
        self.keyboard_key = keyboard_key
        self.mouse_mode = mouse_mode
        self.mouse_position = mouse_position
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.simulate_keystrokes, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def simulate_keystrokes(self):
        while self.running:
            perform_activity(
                self.activity_methods,
                self.keyboard_key,
                self.mouse_mode,
                self.mouse_position,
            )
            
            # Incremental sleep so the thread stops immediately when requested
            for _ in range(int(self.interval * 10)):
                if not self.running:
                    break
                time.sleep(0.1)


def perform_activity(activity_methods, keyboard_key="shiftleft", mouse_mode="nudge", mouse_position=None):
    if "keyboard" in activity_methods:
        pyautogui.press(keyboard_key)
    if "mouse" in activity_methods:
        x, y = pyautogui.position()
        screen_width, screen_height = pyautogui.size()
        if mouse_mode == "saved" and mouse_position is not None:
            target_x = min(max(mouse_position[0], 0), screen_width - 1)
            target_y = min(max(mouse_position[1], 0), screen_height - 1)
            if (target_x, target_y) == (x, y):
                target_x = x + 1 if x < screen_width - 1 else x - 1
        else:
            target_x = x + 1 if x < screen_width - 1 else x - 1
            target_y = y
        pyautogui.moveTo(target_x, target_y, duration=0)
        pyautogui.moveTo(x, y, duration=0)


def get_last_input_info():
    if os.name != "nt":
        raise OSError("Windows last-input information is only available on Windows.")

    class LastInputInfo(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    info = LastInputInfo()
    info.cbSize = ctypes.sizeof(info)
    get_last_input_info = ctypes.windll.user32.GetLastInputInfo
    get_last_input_info.argtypes = [ctypes.POINTER(LastInputInfo)]
    get_last_input_info.restype = wintypes.BOOL
    if not get_last_input_info(ctypes.byref(info)):
        raise ctypes.WinError()

    get_tick_count = ctypes.windll.kernel32.GetTickCount
    get_tick_count.restype = wintypes.DWORD
    idle_ms = (get_tick_count() - info.dwTime) & 0xFFFFFFFF
    return info.dwTime, idle_ms / 1000

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("IdleGuard")
        self.root.geometry("340x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")  # Dark background palette
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.keyboard_enabled = tk.BooleanVar(value=True)
        self.mouse_enabled = tk.BooleanVar(value=False)
        self.keyboard_key = tk.StringVar(value="shiftleft")
        self.screen_width, self.screen_height = pyautogui.size()
        cursor_x, cursor_y = pyautogui.position()
        self.mouse_mode = tk.StringVar(value="nudge")
        self.mouse_target_x = tk.IntVar(value=min(max(cursor_x, 0), self.screen_width - 1))
        self.mouse_target_y = tk.IntVar(value=min(max(cursor_y, 0), self.screen_height - 1))
        self.mouse_target_controls = []
        self.options_window = None
        self.idle_status_label = None
        self.idle_refresh_id = None
        self.mouse_capture_after_id = None

        self.menu_bar = tk.Menu(self.root)
        settings_menu = tk.Menu(self.menu_bar, tearoff=False)
        settings_menu.add_command(label="Options", command=self.open_options)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=self.exit_app)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.root.configure(menu=self.menu_bar)

        # Remove minimize/maximize button safely while keeping Alt+Tab support
        self.root.transient(None)

        # Handle Icon Packaging safely
        self.icon_path = None
        for candidate in (PREFERRED_ICON, FALLBACK_ICON):
            candidate_path = resource_path(candidate)
            if os.path.exists(candidate_path):
                self.icon_path = candidate_path
                break

        if self.icon_path:
            self.root.iconbitmap(self.icon_path)

        # Configure Global Custom Styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        
        # Label Elements
        self.style.configure("TLabel", font=("Segoe UI", 10), foreground="#cdd6f4", background="#1e1e2e")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "bold"), foreground="#a6adc8", background="#1e1e2e")
        self.style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), foreground="#cdd6f4", background="#1e1e2e")
        self.style.configure("TCheckbutton", font=("Segoe UI", 10), foreground="#cdd6f4", background="#1e1e2e", indicatorcolor="#313244")
        self.style.map(
            "TCheckbutton",
            background=[("active", "#1e1e2e")],
            foreground=[("disabled", "#6c7086")],
            indicatorcolor=[("selected", "#a6e3a1")],
        )
        self.style.configure("TRadiobutton", font=("Segoe UI", 10), foreground="#cdd6f4", background="#1e1e2e", indicatorcolor="#313244")
        self.style.map(
            "TRadiobutton",
            background=[("active", "#1e1e2e")],
            foreground=[("disabled", "#6c7086")],
            indicatorcolor=[("selected", "#89dceb")],
        )
        self.style.configure("TSpinbox", fieldbackground="#313244", foreground="#cdd6f4", arrowcolor="#cdd6f4")
        self.style.configure("Options.TButton", font=("Segoe UI", 9, "bold"), foreground="#cdd6f4", background="#313244", borderwidth=0, padding=(10, 6))
        self.style.map("Options.TButton", background=[("active", "#45475a")], foreground=[("active", "#cdd6f4")])
        
        # Dynamic Master Action Button Settings
        self.style.configure("Start.TButton", font=("Segoe UI", 10, "bold"), foreground="#11111b", background="#a6e3a1", borderwidth=0)
        self.style.map("Start.TButton", background=[("active", "#89dceb")])
        
        self.style.configure("Stop.TButton", font=("Segoe UI", 10, "bold"), foreground="#11111b", background="#f38ba8", borderwidth=0)
        self.style.map("Stop.TButton", background=[("active", "#eba0ac")])

        # Form Controls
        self.style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", insertcolor="#cdd6f4")

        # Layout Framing
        self.main_frame = ttk.Frame(self.root, padding=25, style="TFrame")
        self.style.configure("TFrame", background="#1e1e2e")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Elements Architecture
        self.interval_label = ttk.Label(self.main_frame, text="Interval (seconds):")
        self.interval_label.pack(anchor="w", pady=(0, 6))

        vcmd = (self.root.register(self.validate_numeric_input), '%P')
        self.interval_entry = ttk.Entry(self.main_frame, font=("Segoe UI", 11), justify="center", validate="key", validatecommand=vcmd)
        self.interval_entry.insert(0, "240")
        self.interval_entry.pack(fill=tk.X, pady=(0, 22))

        self.interval_entry.bind("<Return>", self.on_enter_pressed)

        self.toggle_button = ttk.Button(self.main_frame, text="Start", style="Start.TButton", command=self.handle_toggle)
        self.toggle_button.pack(fill=tk.X, ipady=7, pady=(0, 18))

        self.status_label = ttk.Label(self.main_frame, text="Status: Idle", style="Status.TLabel", anchor="center")
        self.status_label.pack(fill=tk.X)

        self.simulator = None
        self.keyboard_enabled.trace_add("write", self.update_simulator_methods)
        self.mouse_enabled.trace_add("write", self.update_simulator_methods)
        self.keyboard_key.trace_add("write", self.update_simulator_methods)
        self.mouse_mode.trace_add("write", self.update_simulator_methods)
        self.mouse_target_x.trace_add("write", self.update_simulator_methods)
        self.mouse_target_y.trace_add("write", self.update_simulator_methods)
        self.keyboard_enabled.trace_add("write", self.update_keyboard_controls)
        self.mouse_enabled.trace_add("write", self.update_mouse_controls)

    def open_options(self):
        if self.options_window and self.options_window.winfo_exists():
            self.activate_options_window()
            return

        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Options")
        self.options_window.geometry("400x450")
        self.options_width = 500
        self.options_min_height = 300
        self.options_max_height = 450
        self.options_window.resizable(False, False)
        self.options_window.configure(bg="#1e1e2e")
        self.options_window.transient(self.root)
        self.options_window.protocol("WM_DELETE_WINDOW", self.close_options)
        if self.icon_path:
            self.options_window.iconbitmap(self.icon_path)

        options_container = ttk.Frame(self.options_window)
        options_container.pack(fill=tk.BOTH, expand=True)
        options_container.grid_rowconfigure(0, weight=1)
        options_container.grid_columnconfigure(0, weight=1)

        self.options_canvas = tk.Canvas(options_container, bg="#1e1e2e", highlightthickness=0, borderwidth=0)
        self.options_canvas.grid(row=0, column=0, sticky="nsew")
        self.options_scrollbar = ttk.Scrollbar(options_container, orient=tk.VERTICAL, command=self.options_canvas.yview)
        self.options_scrollbar.grid(row=0, column=1, sticky="ns")
        self.options_scrollbar.grid_remove()
        self.options_canvas.configure(yscrollcommand=self.options_scrollbar.set)

        frame = ttk.Frame(self.options_canvas, padding=22)
        self.options_canvas_window = self.options_canvas.create_window((0, 0), window=frame, anchor="nw")
        self.options_content = frame
        self.options_canvas.bind("<Configure>", self.resize_options_content)
        frame.bind("<Configure>", self.schedule_options_scroll_update)

        ttk.Label(frame, text="Activity controls", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        activity_control_style = {
            "background": "#1e1e2e",
            "foreground": "#cdd6f4",
            "activebackground": "#1e1e2e",
            "activeforeground": "#a6e3a1",
            "selectcolor": "#313244",
            "font": ("Segoe UI", 10),
            "bd": 0,
            "highlightthickness": 0,
            "anchor": "w",
            "cursor": "hand2",
            "padx": 0,
            "pady": 3,
        }
        tk.Checkbutton(frame, text="Keyboard press", variable=self.keyboard_enabled, **activity_control_style).pack(anchor="w", pady=3)
        keyboard_options = ttk.Frame(frame)
        key_row = ttk.Frame(keyboard_options)
        key_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(key_row, text="Key:").pack(side=tk.LEFT)
        self.keyboard_key_label = ttk.Label(key_row, text=self.key_display_name())
        self.keyboard_key_label.pack(side=tk.LEFT, padx=(6, 0), expand=True, anchor="w")
        self.key_capture_button = ttk.Button(key_row, text="Change...", width=16, style="Options.TButton")
        self.key_capture_button.pack(side=tk.RIGHT)
        self.key_capture_button.configure(command=self.begin_key_capture)
        self.key_capture_button.bind("<KeyPress>", self.capture_keyboard_key)
        self.mouse_checkbox = tk.Checkbutton(frame, text="Mouse Movement", variable=self.mouse_enabled, **activity_control_style)
        self.mouse_checkbox.pack(anchor="w", pady=3)
        mouse_options_host = ttk.Frame(frame)
        mouse_options = ttk.Frame(mouse_options_host)
        radio_control_style = {
            **activity_control_style,
            "selectcolor": "#313244",
            "pady": 1,
        }
        tk.Radiobutton(
            mouse_options,
            text="Nudge and return",
            variable=self.mouse_mode,
            value="nudge",
            command=self.update_mouse_controls,
            **radio_control_style,
        ).pack(anchor="w", pady=1)
        tk.Radiobutton(
            mouse_options,
            text="Saved point and return",
            variable=self.mouse_mode,
            value="saved",
            command=self.update_mouse_controls,
            **radio_control_style,
        ).pack(anchor="w", pady=1)

        mouse_target_row = ttk.Frame(mouse_options)
        ttk.Label(mouse_target_row, text="X:").pack(side=tk.LEFT)
        self.mouse_x_spinbox = ttk.Spinbox(
            mouse_target_row,
            from_=0,
            to=self.screen_width - 1,
            width=6,
            textvariable=self.mouse_target_x,
        )
        self.mouse_x_spinbox.pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(mouse_target_row, text="Y:").pack(side=tk.LEFT)
        self.mouse_y_spinbox = ttk.Spinbox(
            mouse_target_row,
            from_=0,
            to=self.screen_height - 1,
            width=6,
            textvariable=self.mouse_target_y,
        )
        self.mouse_y_spinbox.pack(side=tk.LEFT, padx=(4, 12))
        self.record_mouse_position_button = ttk.Button(
            mouse_target_row,
            text="Use cursor position",
            command=self.begin_mouse_position_capture,
            style="Options.TButton",
        )
        self.record_mouse_position_button.pack(side=tk.LEFT)
        self.keyboard_options_frame = keyboard_options
        self.key_options_row = key_row
        self.mouse_options_host = mouse_options_host
        self.mouse_options_frame = mouse_options
        self.mouse_target_row = mouse_target_row

        self.style.configure("Options.TButton", padding=(2, 1))

        self.activity_separator = ttk.Separator(frame)
        self.activity_separator.pack(fill=tk.X, pady=12)
        ttk.Label(frame, text="Windows inactivity check", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(
            frame,
            text="Windows reports time since the last input, but not which app caused it. The test checks whether that timestamp advances.",
            font=("Segoe UI", 9),
            wraplength=360,
        ).pack(anchor="w", pady=(0, 6))
        self.idle_status_label = ttk.Label(frame, text="Checking system idle time...", style="Status.TLabel", wraplength=360)
        self.idle_status_label.pack(anchor="w", pady=(0, 8))
        ttk.Button(frame, text="Check selected method", command=self.check_inactivity_reset, style="Options.TButton").pack(fill=tk.X)

        self.update_keyboard_controls()
        self.update_mouse_controls()
        self.schedule_options_scroll_update()
        self.options_window.after_idle(self.activate_options_window)
        self.refresh_idle_status()

    def activate_options_window(self):
        if self.options_window and self.options_window.winfo_exists():
            self.options_window.lift()
            self.options_window.grab_set()
            self.options_window.focus_force()

    def resize_options_content(self, event):
        self.options_canvas.itemconfigure(self.options_canvas_window, width=event.width)
        self.schedule_options_scroll_update()

    def schedule_options_scroll_update(self, *_):
        if self.options_window and self.options_window.winfo_exists():
            self.options_window.after_idle(self.update_options_scrollbar)

    def update_options_scrollbar(self):
        if not self.options_window or not self.options_window.winfo_exists():
            return

        self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all"))
        content_height = self.options_content.winfo_reqheight()
        viewport_height = self.options_canvas.winfo_height()
        window_height = min(max(content_height, self.options_min_height), self.options_max_height)
        if self.options_window.winfo_height() != window_height:
            self.options_window.geometry(f"{self.options_width}x{window_height}")

        if viewport_height > 1 and content_height > self.options_max_height:
            self.options_scrollbar.grid()
        else:
            self.options_scrollbar.grid_remove()
            self.options_canvas.yview_moveto(0)

    def selected_activity_methods(self):
        methods = []
        if self.keyboard_enabled.get():
            methods.append("keyboard")
        if self.mouse_enabled.get():
            methods.append("mouse")
        return methods

    def update_simulator_methods(self, *_):
        if self.simulator and self.simulator.running:
            self.simulator.activity_methods = self.selected_activity_methods()
            self.simulator.keyboard_key = self.keyboard_key.get()
            self.simulator.mouse_mode = self.mouse_mode.get()
            self.simulator.mouse_position = self.selected_mouse_position()

    def selected_mouse_position(self):
        screen_width, screen_height = pyautogui.size()
        try:
            x = int(self.mouse_target_x.get())
        except (tk.TclError, ValueError):
            x = 0
        try:
            y = int(self.mouse_target_y.get())
        except (tk.TclError, ValueError):
            y = 0
        return min(max(x, 0), screen_width - 1), min(max(y, 0), screen_height - 1)

    def update_mouse_controls(self, *_):
        if self.mouse_enabled.get():
            if not self.mouse_options_host.winfo_manager():
                self.mouse_options_host.pack(
                    fill=tk.X,
                    padx=(24, 0),
                    pady=(0, 4),
                    before=self.activity_separator,
                )
            if not self.mouse_options_frame.winfo_manager():
                self.mouse_options_frame.pack(fill=tk.X)
            if self.mouse_mode.get() == "saved":
                if not self.mouse_target_row.winfo_manager():
                    self.mouse_target_row.pack(fill=tk.X, pady=(5, 0))
            else:
                self.mouse_target_row.pack_forget()
        else:
            self.mouse_options_host.pack_forget()
        self.schedule_options_scroll_update()

    def update_keyboard_controls(self, *_):
        if self.keyboard_enabled.get():
            if not self.keyboard_options_frame.winfo_manager():
                self.keyboard_options_frame.pack(
                    fill=tk.X,
                    padx=(24, 0),
                    before=self.mouse_checkbox,
                )
        else:
            self.keyboard_options_frame.pack_forget()
        self.schedule_options_scroll_update()

    def begin_mouse_position_capture(self):
        if not self.options_window or not self.options_window.winfo_exists():
            return
        if self.mouse_capture_after_id:
            self.options_window.after_cancel(self.mouse_capture_after_id)
        self.record_mouse_position(3)

    def record_mouse_position(self, countdown=3):
        if not self.options_window or not self.options_window.winfo_exists():
            return
        if countdown > 0:
            self.record_mouse_position_button.configure(text=f"Move cursor ({countdown})")
            self.mouse_capture_after_id = self.options_window.after(
                1000,
                lambda: self.record_mouse_position(countdown - 1),
            )
            return

        x, y = pyautogui.position()
        screen_width, screen_height = pyautogui.size()
        self.mouse_target_x.set(min(max(x, 0), screen_width - 1))
        self.mouse_target_y.set(min(max(y, 0), screen_height - 1))
        self.record_mouse_position_button.configure(text="Position saved")
        self.mouse_capture_after_id = self.options_window.after(1500, self.reset_mouse_capture_button)

    def reset_mouse_capture_button(self):
        self.mouse_capture_after_id = None
        if self.options_window and self.options_window.winfo_exists():
            self.record_mouse_position_button.configure(text="Use cursor position")

    def key_display_name(self):
        key = self.keyboard_key.get()
        return KEY_LABELS.get(key, key.upper() if len(key) == 1 else key.replace("_", " ").title())

    def begin_key_capture(self):
        self.key_capture_button.configure(text="Press a key...")
        self.key_capture_button.focus_set()

    def capture_keyboard_key(self, event):
        key = KEYSYM_TO_PYAUTOGUI.get(event.keysym.lower())
        if key is None and len(event.char) == 1:
            key = event.char.lower()
        if key not in pyautogui.KEYBOARD_KEYS:
            self.key_capture_button.configure(text="Unsupported key")
            self.options_window.after(1200, lambda: self.key_capture_button.configure(text="Change..."))
            return "break"

        self.keyboard_key.set(key)
        self.keyboard_key_label.configure(text=self.key_display_name())
        self.key_capture_button.configure(text="Change...")
        self.update_simulator_methods()
        return "break"

    def refresh_idle_status(self):
        if not self.options_window or not self.options_window.winfo_exists():
            return
        try:
            _, idle_seconds = get_last_input_info()
            self.idle_status_label.configure(text=f"Current system idle time: {idle_seconds:.1f} seconds")
        except (OSError, AttributeError) as error:
            self.idle_status_label.configure(text=f"Unable to read Windows idle time: {error}")
        self.idle_refresh_id = self.options_window.after(1000, self.refresh_idle_status)

    def check_inactivity_reset(self):
        methods = self.selected_activity_methods()
        if not methods:
            self.idle_status_label.configure(text="Select at least one activity method first.")
            return
        if self.idle_refresh_id:
            self.options_window.after_cancel(self.idle_refresh_id)
            self.idle_refresh_id = None
        try:
            previous_tick, _ = get_last_input_info()
            perform_activity(
                methods,
                self.keyboard_key.get(),
                self.mouse_mode.get(),
                self.selected_mouse_position(),
            )
        except (OSError, AttributeError) as error:
            self.idle_status_label.configure(text=f"The inactivity check could not run: {error}")
            return

        self.idle_status_label.configure(text="Checking whether Windows registered the selected activity...")
        self.options_window.after(250, lambda: self.finish_inactivity_check(previous_tick, 8))

    def finish_inactivity_check(self, previous_tick, attempts_remaining):
        if not self.options_window or not self.options_window.winfo_exists():
            return
        try:
            current_tick, idle_seconds = get_last_input_info()
        except (OSError, AttributeError) as error:
            self.idle_status_label.configure(text=f"Unable to read Windows idle time: {error}")
            self.idle_refresh_id = self.options_window.after(5000, self.refresh_idle_status)
            return
        if current_tick != previous_tick:
            result = "Windows' last-input timestamp advanced during the test."
        elif attempts_remaining > 1:
            self.options_window.after(
                250,
                lambda: self.finish_inactivity_check(previous_tick, attempts_remaining - 1),
            )
            return
        else:
            result = "Windows' last-input timestamp did not change during the test."
        self.idle_status_label.configure(text=f"{result}\nCurrent system idle time: {idle_seconds:.1f} seconds")
        self.idle_refresh_id = self.options_window.after(5000, self.refresh_idle_status)

    def close_options(self):
        if self.idle_refresh_id and self.options_window:
            self.options_window.after_cancel(self.idle_refresh_id)
            self.idle_refresh_id = None
        if self.mouse_capture_after_id and self.options_window:
            self.options_window.after_cancel(self.mouse_capture_after_id)
            self.mouse_capture_after_id = None
        if self.options_window:
            try:
                self.options_window.grab_release()
            except tk.TclError:
                pass
            self.options_window.destroy()
            self.options_window = None

    def exit_app(self):
        if self.simulator:
            self.simulator.stop()
        self.close_options()
        self.root.destroy()

    def validate_numeric_input(self, new_value):
        if new_value == "":
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    def on_enter_pressed(self, event):
        if not (self.simulator and self.simulator.running):
            self.start_simulation()

    def show_windows_toast(self, title, message):
        """Generates a clean Windows-native pop-up notification without forcing app focus."""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toast_icon = resource_path(PREFERRED_ICON)
            if not os.path.exists(toast_icon):
                toast_icon = resource_path(FALLBACK_ICON)
            threading.Thread(target=toaster.show_toast, args=(title, message, toast_icon, 4), daemon=True).start()
        except ImportError:
            # Fallback inline overlay if library is missing or running on a non-windows dev environment
            self.status_label.configure(text=f"Notification: {message}")

    def handle_toggle(self):
        if self.simulator and self.simulator.running:
            self.stop_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        val = self.interval_entry.get()
        if not val or float(val) <= 0:
            self.show_windows_toast("Validation Error", "Please enter a valid positive number.")
            return
            
        interval = float(val)
        methods = self.selected_activity_methods()
        if not methods:
            self.show_windows_toast("Validation Error", "Select at least one activity method in Settings > Options.")
            return

        self.simulator = KeystrokeSimulator(
            interval,
            methods,
            self.keyboard_key.get(),
            self.mouse_mode.get(),
            self.selected_mouse_position(),
        )
        self.simulator.start()
        
        self.status_label.configure(text="Status: Running...", foreground="#a6e3a1")
        self.toggle_button.configure(text="Stop", style="Stop.TButton")
        self.interval_entry.configure(state="disabled")
        
        self.show_windows_toast("IdleGuard", "Simulation started successfully.")

    def stop_simulation(self):
        if self.simulator and self.simulator.running:
            self.simulator.stop()
            
            self.status_label.configure(text="Status: Idle", foreground="#a6adc8")
            self.toggle_button.configure(text="Start", style="Start.TButton")
            self.interval_entry.configure(state="normal")
            
            self.show_windows_toast("IdleGuard", "Simulation has been stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
