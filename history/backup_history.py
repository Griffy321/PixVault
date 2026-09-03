"""
This code allows that app to keep a record of all the files that the user has backed up. So if they backup a file then move it off their computer (e.g. onto a external drive) then tehy dont have to back it up again
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
import os
from pvlogging import getLogger

log = getLogger(__name__)


class BackupHistory:

    def __init__(self):
        pass


    def histDirectory(self):
        """
        Returns the directory where the history sits
        """
        if os.name == "nt":
            base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        else:
            base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
        return (Path(base) / "PixVault" / "data").resolve()


    def checkForHistFile(self):
        """
        Checks if the history file exists, creates it if not
        """
        filePath = Path(self.histDirectory() / "backed_up_files.db")
        if filePath.exists():
            log.info("Found file path to save backed up files to: %s", str(filePath))
            return True
        else:
            log.warning("No file found to save historical backed up files to, creating one: %s", str(filePath))
            try:
                filePath.parent.mkdir(parents=True, exist_ok=True)
                filePath.touch()
            except Exception:
                log.warning("Unable to create history file: %s", str(filePath))
                return False
            log.info("File created to save historical backed up files to: %s", str(filePath))
            return True


    def setupTable(self):
        connection = sqlite3.connect(self.histDirectory() / "backed_up_files.db")
        sqlEngine = connection.cursor()
        try:
            sqlEngine.execute("""
                create table if not exists saved_files (
                    id TEXT PRIMARY KEY,
                    file_name TEXT,
                    file_bytes INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    deleted_at TEXT
                )
                """)
            connection.commit()
        finally:
            connection.close()


    def recordFile(self, fileName, fileBytes):
        """
        Adds the file to the table along with its size and created, updated and deleted at timestamps
        """
        now = datetime.now(timezone.utc).isoformat()
        row = (str(uuid.uuid4()), fileName, fileBytes, now, now, None)

        connection = sqlite3.connect(self.histDirectory() / "backed_up_files.db")
        try:
            connection.execute(
                """
                insert into saved_files (id, file_name, file_bytes, created_at, updated_at, deleted_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            connection.commit()
        except sqlite3.Error:
            log.warning("Failed to record %s file to history", fileName)
            connection.rollback()
        finally:
            connection.close()