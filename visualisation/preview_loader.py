"""
Pulls previews off the device and decodes them a few files ahead of the card on screen, so the user is never waiting on adb when they swipe.
"""

import os
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QImage

from config import isImage
from device.adb import ADB
from visualisation.images import OpenImage
from pvlogging import getLogger

log = getLogger(__name__)


def cacheDirectory() -> Path:
    """
    Returns the folder previews are pulled into, under the user's app data rather than the project folder so a packaged .exe can still write to it.
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    else:
        base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return (Path(base) / "PixVault" / "cache").resolve()


class PreviewJob(QRunnable):
    """
    One pull and decode, run on the loader's worker thread.
    """

    def __init__(self, loader: "PreviewLoader", fileName: str):
        super().__init__()
        self.loader = loader
        self.fileName = fileName


    def run(self) -> None:
        self.loader.fetch(self.fileName)


class PreviewLoader(QObject):
    """
    Keeps decoded previews ready ahead of the card on screen.

    Pulls run one at a time on a worker thread so the device is never asked for two files at
    once, and so the GUI thread never blocks on adb. Decoded images arrive on the GUI thread
    through ready(), where a null QImage means the file could not be previewed.
    """

    decoded = Signal(str, QImage)   # worker thread -> store()
    ready = Signal(str, QImage)     # once it is cached and safe for the screen to draw

    LOOKAHEAD = 3


    def __init__(self, adb: ADB):
        super().__init__()
        self.adb = adb
        self.viewer = OpenImage()
        self.devicePath = ""
        self.queue: list[str] = []
        self.cache: dict[str, QImage] = {}   # fileName : decoded image, only touched on the GUI thread
        self.requested: set[str] = set()     # already queued, so we do not pull the same file twice
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)
        self.decoded.connect(self.store)


    # GUI thread
    def start(self, devicePath: str, queue: list[str]) -> None:
        """
        Points the loader at a new deck and starts filling the cache from the front of it.
        """
        self.stop()
        self.devicePath = devicePath
        self.queue = list(queue)
        self.clearCacheFolder()
        self.prefetch(0)


    def stop(self) -> None:
        """
        Drops everything still queued, waits for the pull in flight, and frees the decoded images.
        """
        self.pool.clear()
        self.pool.waitForDone()
        self.cache.clear()
        self.requested.clear()


    def prefetch(self, index: int) -> None:
        """
        Queues the file at index and the next LOOKAHEAD after it, then drops the ones already passed.
        """
        for position in range(index, min(index + self.LOOKAHEAD + 1, len(self.queue))):
            fileName = self.queue[position]
            if fileName in self.requested:
                continue
            self.requested.add(fileName)
            self.pool.start(PreviewJob(self, fileName))
        self.evict(index)


    def evict(self, index: int) -> None:
        """
        Forgets previews outside the window around index. The deck only ever moves forward, so nothing behind the card is needed again.
        """
        keep = set(self.queue[index:index + self.LOOKAHEAD + 1])
        for fileName in list(self.cache):
            if fileName not in keep:
                del self.cache[fileName]
                self.requested.discard(fileName)


    def preview(self, fileName: str) -> QImage | None:
        """
        The decoded image for fileName if it is ready, otherwise None while it is still being pulled.
        """
        return self.cache.get(fileName)


    def store(self, fileName: str, image: QImage) -> None:
        """
        Takes a finished decode off the worker thread, caches it, then tells the screen it is there.
        """
        self.cache[fileName] = image
        self.ready.emit(fileName, image)


    def clearCacheFolder(self) -> None:
        """
        Empties the cache folder, in case a previous run was killed before it tidied up after itself.
        """
        folder = cacheDirectory()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            log.warning("Could not create the preview cache folder %s, previews will not load: %s", folder, e)
            return
        for leftover in folder.iterdir():
            if leftover.is_file():
                try:
                    leftover.unlink()
                except OSError as e:
                    log.debug("Could not delete the leftover preview %s: %s", leftover, e)


    # worker thread
    def fetch(self, fileName: str) -> None:
        """
        Pulls fileName into the cache folder, decodes it, then deletes the pulled copy.
        Always emits, so a file that cannot be previewed still gets its card drawn.
        """
        if not isImage(fileName):
            self.decoded.emit(fileName, QImage()) # video, that comes later
            return
        target = cacheDirectory() / fileName
        pulled = self.adb.pullFiles(remotePath=self.devicePath + fileName, localPath=str(target))
        if not pulled:
            self.decoded.emit(fileName, QImage())
            return
        image = self.viewer.loadImage(target)
        try:
            target.unlink(missing_ok=True)
        except OSError as e:
            log.debug("Could not delete the cached preview %s: %s", target, e)
        self.decoded.emit(fileName, image if image is not None else QImage())