"""
The backup destination PixVault recommends by default, when the user has not
picked their own.
"""
from pathlib import Path

BACKUP_DESTINATION = str(Path.home() / "Pictures" / "PixVault Backup")
