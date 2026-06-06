from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

APP_NAME = "Hermes QuickCapture"
APP_SLUG = "HermesQuickCapture"
DEFAULT_INBOX_RELATIVE = "Inbox/Hermes QuickCapture"


def _windows_appdata() -> Path:
    return Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))


def default_config_path() -> Path:
    return _windows_appdata() / APP_SLUG / "config.json"


def resolve_default_vault_path() -> Path:
    env = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env:
        return Path(env)
    known = Path("C:/Users/somec/Kevin Obsidian Vault")
    if known.exists():
        return known
    return Path.home() / "Documents" / "Obsidian Vault"


@dataclass
class QuickCaptureConfig:
    vault_path: str
    inbox_relative_path: str = DEFAULT_INBOX_RELATIVE
    include_frontmatter: bool = True
    hermes_command: str = "hermes"

    @property
    def inbox_path(self) -> Path:
        return Path(self.vault_path) / self.inbox_relative_path


def load_config(path: Optional[Path] = None) -> QuickCaptureConfig:
    path = path or default_config_path()
    if not path.exists():
        return QuickCaptureConfig(vault_path=str(resolve_default_vault_path()))
    data = json.loads(path.read_text(encoding="utf-8"))
    return QuickCaptureConfig(**data)


def save_config(config: QuickCaptureConfig, path: Optional[Path] = None) -> Path:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    return path


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    text = re.sub(r"-+", "-", text)
    return (text[:max_len].strip("-") or "capture")


def title_from_content(content: str) -> str:
    line = next((ln.strip() for ln in content.splitlines() if ln.strip()), "Untitled capture")
    return line[:80]


def build_note(content: str, source: str = "manual", action_hint: str = "inbox") -> tuple[str, str]:
    now = datetime.now().astimezone()
    title = title_from_content(content)
    frontmatter = (
        "---\n"
        f"created: {now.isoformat(timespec='seconds')}\n"
        f"source: {source}\n"
        f"action_hint: {action_hint}\n"
        "tags:\n"
        "  - quickcapture\n"
        "  - inbox\n"
        "---\n\n"
    )
    body = (
        f"# {title}\n\n"
        f"Captured by [[{APP_NAME}]].\n\n"
        "## Capture\n\n"
        f"{content.strip()}\n\n"
        "## Next action\n\n"
        f"- [ ] Triage this capture. Suggested action: `{action_hint}`\n"
    )
    return title, frontmatter + body


def save_capture(content: str, config: Optional[QuickCaptureConfig] = None, source: str = "manual", action_hint: str = "inbox") -> Path:
    if not content or not content.strip():
        raise ValueError("Cannot save an empty capture.")
    config = config or load_config()
    inbox = config.inbox_path
    inbox.mkdir(parents=True, exist_ok=True)
    title, note = build_note(content, source=source, action_hint=action_hint)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = inbox / f"{stamp}-{slugify(title)}.md"
    counter = 2
    while path.exists():
        path = inbox / f"{stamp}-{slugify(title)}-{counter}.md"
        counter += 1
    path.write_text(note, encoding="utf-8")
    return path


def build_hermes_prompt(content: str, mode: str) -> str:
    modes = {
        "summarize": "Summarize this clearly and concisely, then suggest any useful next actions.",
        "rewrite": "Rewrite this in a polished, human, concise voice without changing the meaning.",
        "task": "Turn this into a practical task with context, acceptance criteria, and a suggested next step.",
        "research_idea": "Evaluate this as a potential paid research report or product idea. Give go/no-go, buyer, MVP, and next action.",
        "obsidian": "Classify this capture and suggest where it belongs in my Obsidian vault.",
        "inbox": "Classify this capture and suggest the smallest useful next step.",
    }
    instruction = modes.get(mode, modes["obsidian"])
    return f"{instruction}\n\n---\n\n{content.strip()}"


def launch_hermes_prompt(content: str, mode: str, config: Optional[QuickCaptureConfig] = None) -> subprocess.Popen:
    config = config or load_config()
    prompt = build_hermes_prompt(content, mode)
    return subprocess.Popen([config.hermes_command, prompt], close_fds=True)
