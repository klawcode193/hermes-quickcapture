from pathlib import Path

import pytest

from hermes_quickcapture.core import QuickCaptureConfig, build_hermes_prompt, save_capture, slugify, title_from_content


def test_slugify_handles_empty_and_symbols():
    assert slugify("Hello, Hermes!") == "hello-hermes"
    assert slugify("!!!") == "capture"


def test_title_from_first_nonblank_line():
    assert title_from_content("\n\nFirst line\nSecond") == "First line"


def test_save_capture_creates_markdown_note(tmp_path: Path):
    cfg = QuickCaptureConfig(vault_path=str(tmp_path), inbox_relative_path="Inbox/Test")
    path = save_capture("Remember to test this", cfg, source="clipboard", action_hint="task")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "# Remember to test this" in text
    assert "source: clipboard" in text
    assert "Suggested action: `task`" in text


def test_empty_capture_rejected(tmp_path: Path):
    cfg = QuickCaptureConfig(vault_path=str(tmp_path))
    with pytest.raises(ValueError):
        save_capture("   ", cfg)


def test_hermes_prompt_modes():
    prompt = build_hermes_prompt("some pasted thing", "research_idea")
    assert "paid research report" in prompt
    assert "some pasted thing" in prompt
