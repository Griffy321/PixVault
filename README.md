# PixVault

The application within this repository allows a user to backup photos from their phone onto their computer using a simple user friendly UI.

PixVault talks to an Android device over [ADB](https://developer.android.com/tools/adb), lets you browse the device's
filesystem from a desktop window, preview the media it finds, and copy what you want onto your machine.

## Status

Early development. Device browsing and the navigation UI are in place; saving and preview are still being built out.

## Requirements

- Python 3.11 or newer
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) (`adb` must be on your `PATH`)
- An Android device with **USB debugging** enabled and the connection authorised

Verify ADB can see your phone before starting the app:

```bash
adb devices
```

You should see exactly one device listed as `device` (not `unauthorized`).

## Installation

```bash
git clone https://github.com/Griffy321/PixVault.git
cd PixVault
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install PySide6
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
| `visualisation/` | Image and video preview helpers                                    |
| `logging/`       | Application logging                                                |

## Supported media

`.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) if it is available, or open an issue to discuss a
change before starting work.

## License

Licensed under the Apache License 2.0 — see [LICENSE](LICENSE).
