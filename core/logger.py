import threading
from datetime import datetime

class UILogger:
    """Thread-safe logger that routes colored messages to the CustomTkinter Console."""
    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self._lock = threading.Lock()

    def set_widget(self, text_widget):
        self.text_widget = text_widget

    def _append(self, tag, prefix, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {prefix} {message}\n"
        
        with self._lock:
            if self.text_widget:
                # Use after to be 100% thread safe with Tkinter mainloop
                try:
                    self.text_widget.after(0, self._insert_to_widget, formatted, tag)
                except Exception:
                    print(formatted, end="")
            else:
                print(formatted, end="")

    def _insert_to_widget(self, text, tag):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", text, tag)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except Exception:
            pass

    def info(self, msg):
        self._append("INFO", "[*]", msg)

    def success(self, msg):
        self._append("SUCCESS", "[+]", msg)

    def error(self, msg):
        self._append("ERROR", "[-]", msg)

    def warn(self, msg):
        self._append("WARN", "[!]", msg)

    def brom(self, msg):
        self._append("BROM", "[⚡ BROM]", msg)
