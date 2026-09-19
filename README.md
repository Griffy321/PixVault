# PixVault

The application within this repository allows a user to backup photos and videos from their phone onto their computer using a simple user friendly UI.

It talks to the phone over ADB, which comes bundled with the app, so there's nothing else to install.

## Status

Working on Windows, not tested on Mac or Linux yet. You can browse your phone, preview photos and videos, pick which ones to keep and back them up. Anything you've backed up before gets skipped, even if you've since moved it off your PC (e.g. onto an external drive).

## Download (Windows)

1. Download the zip from the [latest release](https://github.com/Griffy321/PixVault/releases/latest).
2. Unzip it and run `PixVault.exe` from the `PixVault` folder. No install or Python needed.
3. If Windows says "Windows protected your PC", click "More info" then "Run anyway". It shows because the app isn't code signed.

## Setting up your phone

You only need to do this once.

1. Go to Settings > About phone and tap Build number 7 times to turn on Developer options.
2. In Developer options, turn on USB debugging.
3. Plug your phone in and allow USB debugging when it asks. Tick "Always allow from this computer" so it doesn't ask every time.

Menu names differ a bit between phones. If your phone still isn't found you may need its USB driver, mostly on Samsungs.

## Using it

1. Pick the folder on your phone you want to back up, e.g. `DCIM/Camera`.
2. Pick where to save it on your PC, or use the default `Pictures\PixVault Backup`.
3. Go through each photo and video and keep or skip it. The arrow keys work too.
4. PixVault copies across everything you kept and shows you what was saved.

## Running from source

Needs Python 3.11 or newer.

```bash
git clone https://github.com/Griffy321/PixVault.git
cd PixVault
python -m venv .venv
.venv\Scripts\activate      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The Windows adb lives in `vendor/platform-tools/`. On Mac or Linux it uses the `adb` on your PATH instead.

## Building a release

Pushing a version tag builds the Windows zip on GitHub and puts it on a draft release (see [`.github/workflows/release.yml`](.github/workflows/release.yml)).

```bash
git tag v1.0.0
git push origin v1.0.0
```

To build it yourself, `pip install pyinstaller` then `pyinstaller PixVault.spec --noconfirm`. It ends up in `dist/PixVault/`.

## Where things are saved

Your backups go wherever you pick. PixVault keeps its own logs and backup history in `%LOCALAPPDATA%\PixVault\`, or `~/.local/state/PixVault/` on Mac and Linux.

## Supported files

Most photo, RAW and video formats, e.g. `.jpg`, `.heic`, `.dng`, `.mp4` and `.mov`. The full list is in [`config/media_types.py`](config/media_types.py). HEIC and RAW files back up fine but don't get a preview yet.

## Project structure

| Path             | What's in it                                            |
| ---------------- | ------------------------------------------------------- |
| `main.py`        | Starts the app                                          |
| `app/`           | The screens                                             |
| `device/`        | Talking to the phone over ADB, browsing it, saving files |
| `local/`         | Scanning the backup folder on your PC                   |
| `history/`       | The record of everything backed up, in SQLite           |
| `config/`        | File types, the default save folder and styling         |
| `visualisation/` | Photo and video previews                                |
| `pvlogging/`     | Logging                                                 |
| `vendor/`        | The bundled adb                                         |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For anything bigger than a small fix, open an issue first.

## License

Apache 2.0, see [LICENSE](LICENSE).
