# PyInstaller build for the Windows release, run with: pyinstaller PixVault.spec --noconfirm
# Builds dist/PixVault/, a folder holding PixVault.exe and everything it needs, which the release zips up.

a = Analysis(
    ["main.py"],
    datas=[("vendor/platform-tools", "platform-tools")], # resolveADBPath() looks for sys._MEIPASS/platform-tools/adb.exe
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PixVault",
    console=False, # a windowed app, no terminal behind it
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="PixVault",
)
