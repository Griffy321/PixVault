# PixVault

The application within this repository allows a user to backup photos from their phone onto their computer using a simple user friendly UI.

PixVault talks to an Android device over [ADB](https://developer.android.com/tools/adb), lets you browse the device's
filesystem from a desktop window, preview the media it finds, and copy what you want onto your machine.

## Status

Early development. Device browsing, the navigation UI, media preview, choosing a backup destination, and saving with
de-duplication against the destination folder are in place. Every saved file is now recorded in a local history
database; using that history to skip files you have already backed up and since moved elsewhere is still to come.

## Requirements

- Python 3.11 or newer
- [PySide6](https://doc.qt.io/qtforpython-6/) and [OpenCV](https://pypi.org/project/opencv-python/) (both in `requirements.txt`)
- An Android device with **USB debugging** enabled and the connection authorised

ADB itself ships with the app for Windows (see `vendor/platform-tools/`) — no separate Android Platform Tools install
or `PATH` setup needed. On other platforms the bundled binary does not apply and PixVault falls back to an `adb` on
your `PATH`. Plug your phone in, enable USB debugging, and accept the "Allow USB debugging" prompt on the device when
it appears; the app will detect it automatically.

## Installation

```bash
git clone https://github.com/Griffy321/PixVault.git
cd PixVault
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The navigation window opens at `/sdcard` on the connected device. Browse into folders to find your photos and videos,
then select the files you want to pull across.

## Project structure

| Path             | Purpose                                                            |
| ---------------- | ------------------------------------------------------------------ |
| `main.py`        | Entry point — builds the `QApplication` and shows the first screen |
| `app/`           | PySide6 screens and widgets                                        |
| `device/`        | ADB wrapper, device filesystem navigation, and file saving          |
| `local/`         | Scanning the destination folder on this PC                         |
| `history/`       | Local record of every file backed up, in SQLite                    |
| `config/`        | Media types, default destination, and stylesheet                   |
| `visualisation/` | Image and video preview helpers                                    |
| `pvlogging/`     | Application logging                                                |
| `vendor/`        | Bundled third-party binaries (adb, from Android Platform Tools)    |

## Where PixVault keeps its own files

Your photos go wherever you pick as the destination (`~/Pictures/PixVault Backup` by default). PixVault's own logs and
the backup-history database live outside the project folder, under `%LOCALAPPDATA%\PixVault\` on Windows and
`~/.local/state/PixVault/` elsewhere, so a packaged build can still write to them.

## Supported media

Common photo, RAW, and video formats — `.jpg`, `.png`, `.heic`, and `.webp` through to `.dng`, `.cr3`, `.nef`, `.mp4`,
`.mov`, and `.mkv`. The full list is defined in [`config/media_types.py`](config/media_types.py).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code style, and how to open a pull
request. Please open an issue to discuss anything larger than a small fix before starting work.

## License

Licensed under the Apache License 2.0 — see [LICENSE](LICENSE).
