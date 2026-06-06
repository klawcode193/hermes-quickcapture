# Hermes QuickCapture

Hermes QuickCapture is a small Windows tray app for getting copied text, URLs, snippets, and ideas out of your head/clipboard and into an Obsidian inbox — with quick actions that prepare the capture for Hermes Agent.

Working goal: combine an **Obsidian Capture Inbox** and a **Hermes Clipboard Supercharger** into one low-friction desktop utility.

## MVP features

- Windows system tray app.
- Global hotkeys:
  - `Ctrl+Alt+Space`: open capture window.
  - `Ctrl+Alt+C`: save current clipboard to Obsidian inbox.
- Capture window for pasted text/URLs/snippets.
- Save markdown captures to an Obsidian inbox folder.
- Mark captures as inbox, task, research idea, summarize, or rewrite.
- Copy a ready-to-send Hermes prompt for clipboard content.
- Configurable Obsidian vault folder.
- Open-source / donationware-friendly project structure.

## Default capture location

By default the app uses `OBSIDIAN_VAULT_PATH` if set, otherwise it tries:

```text
C:/Users/somec/Kevin Obsidian Vault/Inbox/Hermes QuickCapture/
```

The vault can be changed from the app's Settings button.

## Development

```bash
cd C:/Users/somec/i7_hermes_projects/hermes-quickcapture
uv venv
uv pip install -e ".[dev]"
python -m pytest -q
python -m hermes_quickcapture.app
```

## Build Windows exe

```bash
python -m PyInstaller --noconsole --onefile --name HermesQuickCapture --icon assets/hermes-quickcapture.ico --add-data "assets/hermes-quickcapture.ico;assets" --add-data "assets/hermes-quickcapture.png;assets" --paths src launcher.py
```

The executable will be created at:

```text
dist/HermesQuickCapture.exe
```

## Safety model

QuickCapture writes markdown files into the configured Obsidian vault. It does not permanently delete files. Clipboard captures stay local unless you manually paste/send the generated Hermes prompt somewhere else.

## Donationware / open source

This project is intended to be open source and donation-supported. Donation links are intentionally placeholders until live public accounts/pages are chosen.

Suggested donation surfaces:

- GitHub Sponsors
- Ko-fi / Buy Me a Coffee
- Custom donation page

## Roadmap

- Direct Hermes CLI action runner.
- Clipboard history queue.
- Screenshot/OCR capture.
- Voice memo capture.
- Daily inbox triage digest.
- Obsidian routing rules by project/category.
- Installer and signed Windows release.
