# 🎙 Next Slide

A lightweight macOS app that listens for voice commands during a Zoom call and automatically advances or goes back in Google Slides — no clicker required.

---

## How it works

Next Slide runs in a small floating window that stays on top of your other apps. Once you hit **Start Listening**, it continuously monitors your microphone. When it hears a matching phrase, it sends the appropriate arrow key to your browser to navigate the slide.

---

## Voice commands

| Say this | Action |
|---|---|
| "Next Slide" | Advance to the next slide ▶ |
| "Previous Slide" | Go back one slide ◀ |
| "Advance slide" / "Go forward" | Next slide ▶ |
| "Go back" / "Last slide" | Previous slide ◀ |

---

## Requirements

- macOS (uses AppleScript to send keystrokes)
- Python 3
- [Homebrew](https://brew.sh) (for PortAudio)
- Google Slides open in a browser in **Presenter mode** (`Cmd + Shift + Enter`)

---

## Installation & setup

**1. Clone the repo**
```bash
git clone git@github.com:brianneidhardtclz/next-slide.git
cd next-slide
```

**2. Run the install script**
```bash
bash install_and_run.sh
```

This will install PortAudio via Homebrew and the required Python packages (`SpeechRecognition`, `PyAudio`), then launch the app.

**3. Grant macOS permissions (first run only)**

macOS will prompt you for two permissions:

- **Microphone** — approve the popup when it appears
- **Accessibility** — required so the app can send keystrokes to your browser:
  - Go to **System Settings → Privacy & Security → Accessibility**
  - Add **Terminal** (or whichever shell app you use) and enable it

---

## Usage

1. Open your Google Slides presentation and enter Presenter mode (`Cmd + Shift + Enter`)
2. Start your Zoom call
3. Run `python3 next_slide.py` (or use `install_and_run.sh`)
4. Click **Start Listening** in the app window
5. Say "Next Slide" or "Previous Slide" at any time during your call

The app window floats above all other windows so you can always see its status.

> **Note:** Speech recognition uses Google's Web Speech API and requires an internet connection.

---

## Running after initial setup

Once dependencies are installed, you can launch directly with:

```bash
python3 next_slide.py
```

---

## Troubleshooting

**"No module named speech_recognition"**
```bash
pip3 install SpeechRecognition PyAudio --break-system-packages
```

**Keystrokes not reaching Google Slides**
Make sure Terminal has Accessibility permission in System Settings → Privacy & Security → Accessibility.

**Slides not advancing in the browser**
Confirm Google Slides is in Presenter mode (`Cmd + Shift + Enter`). In edit mode, arrow keys move the cursor inside text boxes rather than changing slides.

**"Network error" in the app**
The app requires an internet connection for speech recognition. Check your connection and try again.
