#!/usr/bin/env python3
"""
Next Slide — Voice-controlled Google Slides navigator
------------------------------------------------------
Listens for "Next Slide" or "Previous Slide" (and variations)
and sends the matching keystroke to your browser.

Requirements:  pip3 install SpeechRecognition PyAudio
macOS setup:   brew install portaudio  (needed by PyAudio)
"""

import subprocess
import threading
import tkinter as tk
import time
import sys

try:
    import speech_recognition as sr
except ImportError:
    print("ERROR: SpeechRecognition not installed.")
    print("Run:  pip3 install SpeechRecognition PyAudio")
    sys.exit(1)

# ── Voice command phrase lists ────────────────────────────────────────────────

FORWARD_PHRASES = [
    "next slide",
    "advance slide",
    "move forward",
    "go forward",
    "forward slide",
]

BACKWARD_PHRASES = [
    "previous slide",
    "go back",
    "back slide",
    "last slide",
    "prior slide",
]

# ── AppleScript key codes (macOS physical key codes) ─────────────────────────
# 124 = Right Arrow   123 = Left Arrow
APPLESCRIPT_NEXT = 'tell application "System Events" to key code 124'
APPLESCRIPT_PREV = 'tell application "System Events" to key code 123'


def send_keystroke(applescript: str) -> bool:
    """Run an AppleScript one-liner. Returns True on success."""
    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


# ── Colour palette ────────────────────────────────────────────────────────────

BG      = "#0d0d1a"   # deep navy background
CARD    = "#16162a"   # slightly lighter card
ACCENT  = "#7c6af7"   # purple accent
GREEN   = "#3ee0ac"   # teal-green  (listening / next)
RED     = "#ff6b6b"   # coral-red   (stop / prev)
GOLD    = "#f5c542"   # amber       (calibrating)
TEXT    = "#e8e8f0"
DIM     = "#4a4a6a"
WHITE   = "#ffffff"


# ── Main application ──────────────────────────────────────────────────────────

class NextSlideApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Next Slide")
        self.root.geometry("400x380")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)   # float above Zoom

        self.listening   = False
        self.recognizer  = sr.Recognizer()
        self.recognizer.pause_threshold    = 0.6   # shorter pause = faster response
        self.recognizer.energy_threshold   = 300    # will be calibrated
        self.microphone  = sr.Microphone()
        self._stop_bg    = None
        self._flash_id   = None
        self._command_count = 0

        self._build_ui()
        threading.Thread(target=self._calibrate, daemon=True).start()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Top bar ──────────────────────────────────────────────────────────
        top = tk.Frame(root, bg=BG)
        top.pack(fill=tk.X, padx=28, pady=(26, 0))

        tk.Label(top, text="🎙", font=("Helvetica", 28),
                 bg=BG, fg=WHITE).pack(side=tk.LEFT, padx=(0, 10))

        title_frame = tk.Frame(top, bg=BG)
        title_frame.pack(side=tk.LEFT)
        tk.Label(title_frame, text="Next Slide",
                 font=("Helvetica Neue", 22, "bold"),
                 bg=BG, fg=WHITE).pack(anchor="w")
        tk.Label(title_frame, text="Voice slide navigator for Google Slides",
                 font=("Helvetica Neue", 10),
                 bg=BG, fg=DIM).pack(anchor="w")

        # ── Divider ───────────────────────────────────────────────────────────
        tk.Frame(root, bg=CARD, height=1).pack(fill=tk.X, padx=28, pady=(16, 0))

        # ── Status row ────────────────────────────────────────────────────────
        status_row = tk.Frame(root, bg=BG)
        status_row.pack(pady=(14, 0))

        self._dot = tk.Label(status_row, text="●", font=("Helvetica", 13),
                             bg=BG, fg=DIM)
        self._dot.pack(side=tk.LEFT, padx=(0, 7))

        self._status_lbl = tk.Label(status_row, text="Calibrating microphone…",
                                    font=("Helvetica Neue", 12),
                                    bg=BG, fg=DIM)
        self._status_lbl.pack(side=tk.LEFT)

        # ── Action flash ──────────────────────────────────────────────────────
        self._action_lbl = tk.Label(root, text="",
                                    font=("Helvetica Neue", 22, "bold"),
                                    bg=BG, fg=GREEN)
        self._action_lbl.pack(pady=(10, 0))

        # ── Last-heard text ───────────────────────────────────────────────────
        self._heard_lbl = tk.Label(root, text="",
                                   font=("Helvetica Neue", 10, "italic"),
                                   bg=BG, fg=DIM, wraplength=340)
        self._heard_lbl.pack(pady=(2, 0))

        # ── Toggle button ─────────────────────────────────────────────────────
        self._btn = tk.Button(
            root, text="Start Listening",
            font=("Helvetica Neue", 14, "bold"),
            bg=GREEN, fg=BG,
            relief=tk.FLAT, padx=32, pady=11,
            cursor="hand2",
            activebackground=GREEN, activeforeground=BG,
            command=self._toggle,
        )
        self._btn.pack(pady=18)

        # ── Counter ───────────────────────────────────────────────────────────
        self._count_lbl = tk.Label(root, text="Commands executed: 0",
                                   font=("Helvetica Neue", 10),
                                   bg=BG, fg=DIM)
        self._count_lbl.pack()

        # ── Hints ─────────────────────────────────────────────────────────────
        hints = tk.Frame(root, bg=CARD, bd=0)
        hints.pack(fill=tk.X, padx=28, pady=(14, 0))

        for label, action in [
            ("🟢  "Next Slide"  →  advance", GREEN),
            ("🔴  "Previous Slide"  →  go back", RED),
        ]:
            tk.Label(hints, text=label, font=("Helvetica Neue", 10),
                     bg=CARD, fg=action,
                     anchor="w", padx=12, pady=5).pack(fill=tk.X)

        # ── Footer note ───────────────────────────────────────────────────────
        tk.Label(root,
                 text="Keep Google Slides in presenter mode (Cmd+Shift+Enter)",
                 font=("Helvetica Neue", 9),
                 bg=BG, fg=DIM, wraplength=360).pack(pady=(8, 0))

    # ── Thread-safe UI helpers ────────────────────────────────────────────────

    def _set_status(self, text: str, color: str):
        self.root.after(0, lambda: [
            self._status_lbl.config(text=text, fg=color),
            self._dot.config(fg=color),
        ])

    def _set_heard(self, text: str):
        display = f'Heard: "{text}"' if text else ""
        self.root.after(0, lambda: self._heard_lbl.config(text=display))

    def _flash_action(self, text: str, color: str):
        if self._flash_id:
            self.root.after_cancel(self._flash_id)
        self.root.after(0, lambda: self._action_lbl.config(text=text, fg=color))
        self._flash_id = self.root.after(2400, lambda: self._action_lbl.config(text=""))

    def _increment_counter(self):
        self._command_count += 1
        n = self._command_count
        self.root.after(0, lambda: self._count_lbl.config(
            text=f"Commands executed: {n}"))

    # ── Microphone calibration ────────────────────────────────────────────────

    def _calibrate(self):
        self._set_status("Calibrating microphone…", GOLD)
        try:
            with self.microphone as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=1.5)
            self._set_status("Ready — press Start to begin", DIM)
        except Exception as e:
            self._set_status(f"Mic error: {e}", RED)

    # ── Listening toggle ──────────────────────────────────────────────────────

    def _toggle(self):
        if self.listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        self.listening = True
        self._btn.config(text="Stop Listening", bg=RED, fg=WHITE,
                         activebackground=RED, activeforeground=WHITE)
        self._set_status("Listening…", GREEN)
        self._set_heard("")
        self._stop_bg = self.recognizer.listen_in_background(
            self.microphone,
            self._audio_callback,
            phrase_time_limit=5,
        )

    def _stop_listening(self):
        self.listening = False
        if self._stop_bg:
            self._stop_bg(wait_for_stop=False)
            self._stop_bg = None
        self._btn.config(text="Start Listening", bg=GREEN, fg=BG,
                         activebackground=GREEN, activeforeground=BG)
        self._set_status("Stopped", DIM)
        self._set_heard("")

    # ── Speech recognition callback ───────────────────────────────────────────

    def _audio_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData):
        """Called from background thread whenever a phrase is captured."""
        try:
            text = recognizer.recognize_google(audio).lower().strip()
        except sr.UnknownValueError:
            return   # nothing heard / couldn't parse
        except sr.RequestError as e:
            self._set_status(f"Network error — {e}", RED)
            return

        self._set_heard(text)
        self._process_command(text)

    # ── Command matching ──────────────────────────────────────────────────────

    def _process_command(self, text: str):
        for phrase in FORWARD_PHRASES:
            if phrase in text:
                ok = send_keystroke(APPLESCRIPT_NEXT)
                label = "▶  Next Slide" if ok else "▶  Next Slide (key error)"
                self._flash_action(label, GREEN)
                self._increment_counter()
                return

        for phrase in BACKWARD_PHRASES:
            if phrase in text:
                ok = send_keystroke(APPLESCRIPT_PREV)
                label = "◀  Previous Slide" if ok else "◀  Previous Slide (key error)"
                self._flash_action(label, RED)
                self._increment_counter()
                return


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = NextSlideApp(root)

    def on_close():
        if app._stop_bg:
            app._stop_bg(wait_for_stop=False)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
