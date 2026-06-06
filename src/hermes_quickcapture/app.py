from __future__ import annotations

import os
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

import pyperclip
from PIL import Image, ImageDraw

from .core import APP_NAME, build_hermes_prompt, load_config, save_capture, save_config

try:
    import pystray
except Exception:  # pragma: no cover - exercised manually on Windows
    pystray = None

try:
    import keyboard
except Exception:  # pragma: no cover
    keyboard = None


def make_icon_image(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (24, 31, 48, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=14, fill=(37, 99, 235, 255))
    d.rectangle((18, 18, size - 18, size - 14), fill=(255, 255, 255, 245))
    d.polygon([(22, 25), (size - 22, 25), (size // 2 + 5, 39), (size // 2 + 5, 48), (size // 2 - 5, 52), (size // 2 - 5, 39)], fill=(37, 99, 235, 255))
    return img


class QuickCaptureWindow:
    def __init__(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox
        self.tk = tk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("680x460")
        self.root.attributes("-topmost", True)
        self.root.after(250, lambda: self.root.attributes("-topmost", False))
        self.status = tk.StringVar(value=f"Inbox: {self.config.inbox_path}")
        self.action = tk.StringVar(value="inbox")
        self._build()

    def _build(self):
        tk = self.tk
        frame = tk.Frame(self.root, padx=12, pady=12)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Capture text / URL / clipboard item", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.text = tk.Text(frame, height=14, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True, pady=(8, 8))
        actions = tk.Frame(frame)
        actions.pack(fill="x")
        for label, value in [("Inbox", "inbox"), ("Task", "task"), ("Research idea", "research_idea"), ("Summarize", "summarize"), ("Rewrite", "rewrite")]:
            tk.Radiobutton(actions, text=label, variable=self.action, value=value).pack(side="left")
        buttons = tk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 6))
        tk.Button(buttons, text="Paste Clipboard", command=self.paste_clipboard).pack(side="left")
        tk.Button(buttons, text="Save to Obsidian", command=self.save_text).pack(side="left", padx=6)
        tk.Button(buttons, text="Copy Hermes Prompt", command=self.copy_prompt).pack(side="left")
        tk.Button(buttons, text="Settings", command=self.settings).pack(side="left", padx=6)
        tk.Button(buttons, text="Open Inbox", command=open_inbox).pack(side="left")
        tk.Label(frame, textvariable=self.status, wraplength=630, fg="#444").pack(anchor="w", pady=(8, 0))
        self.paste_clipboard()
        self.root.bind("<Control-Return>", lambda _e: self.save_text())
        self.root.bind("<Escape>", lambda _e: self.root.destroy())

    def paste_clipboard(self):
        data = pyperclip.paste() or ""
        if data:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", data)
            self.status.set("Clipboard pasted. Ctrl+Enter saves.")

    def _content(self) -> str:
        return self.text.get("1.0", "end").strip()

    def save_text(self):
        try:
            path = save_capture(self._content(), source="manual", action_hint=self.action.get())
            self.status.set(f"Saved: {path}")
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))

    def copy_prompt(self):
        content = self._content()
        if not content:
            self.messagebox.showwarning(APP_NAME, "Nothing to copy.")
            return
        pyperclip.copy(build_hermes_prompt(content, self.action.get()))
        self.status.set("Hermes prompt copied to clipboard.")

    def settings(self):
        current = load_config()
        initial = current.vault_path if Path(current.vault_path).exists() else str(Path.home())
        vault = self.filedialog.askdirectory(title="Choose Obsidian vault", initialdir=initial)
        if vault:
            current.vault_path = vault
            save_config(current)
            self.config = current
            self.status.set(f"Settings saved. Inbox: {current.inbox_path}")

    def run(self):
        self.root.mainloop()


def show_window():
    def runner():
        try:
            QuickCaptureWindow().run()
        except Exception:
            traceback.print_exc()
    threading.Thread(target=runner, daemon=True).start()


def capture_clipboard(action: str = "inbox"):
    try:
        content = pyperclip.paste() or ""
        path = save_capture(content, source="clipboard", action_hint=action)
        return path
    except Exception as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return None


def open_inbox():
    cfg = load_config()
    cfg.inbox_path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(cfg.inbox_path))  # type: ignore[attr-defined]


def open_project_page():
    webbrowser.open("https://github.com/klawcode193/hermes-quickcapture")


def setup_hotkey():
    if keyboard is None:
        return
    try:
        keyboard.add_hotkey("ctrl+alt+space", show_window)
        keyboard.add_hotkey("ctrl+alt+c", lambda: capture_clipboard("inbox"))
    except Exception as exc:
        print(f"Hotkey setup skipped: {exc}", file=sys.stderr)


def main():
    save_config(load_config())
    setup_hotkey()
    if pystray is None:
        show_window()
        try:
            while True:
                threading.Event().wait(3600)
        except KeyboardInterrupt:
            return
    menu = pystray.Menu(
        pystray.MenuItem("Open Quick Capture", lambda _icon, _item: show_window(), default=True),
        pystray.MenuItem("Capture Clipboard to Obsidian", lambda _icon, _item: capture_clipboard("inbox")),
        pystray.MenuItem("Clipboard -> Task", lambda _icon, _item: capture_clipboard("task")),
        pystray.MenuItem("Clipboard -> Research Idea", lambda _icon, _item: capture_clipboard("research_idea")),
        pystray.MenuItem("Open Inbox Folder", lambda _icon, _item: open_inbox()),
        pystray.MenuItem("Project / Donate", lambda _icon, _item: open_project_page()),
        pystray.MenuItem("Quit", lambda icon, _item: icon.stop()),
    )
    icon = pystray.Icon("HermesQuickCapture", make_icon_image(), APP_NAME, menu)
    icon.run()


if __name__ == "__main__":
    main()
