# Contributing to PixVault

Thanks for taking an interest in PixVault. This document covers how to get set up and what to expect when opening a
pull request.

## Getting set up

See the [README](README.md) for full requirements. In short:

```bash
git clone https://github.com/Griffy321/PixVault.git
cd PixVault
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

To exercise anything under `device/` you will need an Android device with USB debugging enabled. You do not need to
install `adb` yourself on Windows — `resolveADBPath()` in `device/adb.py` prefers the copy bundled in
`vendor/platform-tools/`, falling back to an `adb` on your `PATH` if the bundled one is missing (as it will be on
Linux and macOS, where only the Windows `adb.exe` is vendored).

## Before you start

Open an issue first for anything larger than a small fix. It avoids two people solving the same problem in different
ways, and it is a good place to agree on an approach before code gets written.

## Making a change

1. Branch off `main` — `git checkout -b short-description-of-change`
2. Keep the change focused. One concern per pull request.
3. Check the app still launches (`python main.py`) before pushing.
4. Open a pull request describing **what** changed and **why**.

## Code style

The existing code follows a few conventions worth matching:

- `camelCase` for methods and variables, `PascalCase` for classes
- A short docstring on every class and public method
- Type hints where they clarify intent, as in `device/navigation.py`
- Two blank lines between methods
- `TODO:` comments for known gaps, kept near the code they describe

Consistency with the surrounding file matters more than any rule here.

## Project layout

| Path             | Purpose                                        |
| ---------------- | ---------------------------------------------- |
| `main.py`        | Entry point                                    |
| `app/`           | PySide6 screens and widgets                    |
| `device/`        | ADB wrapper, filesystem navigation, saving     |
| `local/`         | Scanning the destination folder on this PC     |
| `history/`       | Local record of backed up files, in SQLite     |
| `config/`        | Media types, default destination, stylesheet   |
| `visualisation/` | Image and video preview helpers                |
| `pvlogging/`     | Application logging                            |

Anything touching the device should go through the `ADB` wrapper in `device/adb.py` rather than calling `subprocess`
directly, so device access stays in one place.

Anything PixVault writes for itself — logs, the history database — belongs under the user's app data directory rather
than the project folder, so a packaged build can still write to it. Follow the pattern in
`pvlogging.logDirectory()` / `BackupHistory.histDirectory()`.

SQL should always use `?` placeholders for values rather than f-string interpolation, so filenames containing quotes
cannot break or inject into a query.

## Reporting bugs

Include your OS, Python version, `adb devices` output, and the steps that triggered the problem. A traceback is worth
more than a description of it.

## License

By contributing you agree that your contributions are licensed under the Apache License 2.0, the same license that
covers this project.
