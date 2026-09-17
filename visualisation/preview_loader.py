"""
Pulls previews off the device and decodes them a few files ahead of the card on screen, so the user is never waiting on adb when they swipe.
"""

import os
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QImage

from config import isImage, isVideo
from device.adb import ADB
from visualisation.images import OpenImage
from visualisation.videos import OpenVideo
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
    once, and so the GUI thread never blocks on adb. ready() fires on the GUI thread once a
    file is cached, and the screen reads it back with preview().

    A still is decoded and its pulled copy deleted straight away. A video's copy is kept, as
    QMediaPlayer plays from the file itself, and is deleted when the card moves past it.
    """

    decoded = Signal(str, QImage, str, float)   # worker thread -> store()
    ready = Signal(str)                         # once it is cached and the screen can read it

    LOOKAHEAD = 3
    MAX_VIDEO_BYTES = 150 * 1024 * 1024 # bigger clips stall the queue for longer than they are worth


    def __init__(self, adb: ADB):
        super().__init__()
        self.adb = adb
        self.viewer = OpenImage()
        self.clips = OpenVideo()
        self.devicePath = ""
        self.queue: list[str] = []
        self.sizes: dict[str, int] = {}
        self.cache: dict[str, tuple[QImage, str, float]] = {} # fileName : (image, video path or "", seconds)
        self.requested: set[str] = set()     # already queued, so we do not pull the same file twice
        self.stale: list[Path] = []          # deletes to retry, Windows will not unlink a file the player still holds
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)
        self.decoded.connect(self.store)


    # GUI thread
    def start(self, devicePath: str, queue: list[str], sizes: dict[str, int]) -> None:
        """
        Points the loader at a new deck and starts filling the cache from the front of it.
        """
        self.stop()
        self.devicePath = devicePath
        self.queue = list(queue)
        self.sizes = dict(sizes)
        self.clearCacheFolder()
        self.prefetch(0)


    def stop(self) -> None:
        """
        Drops everything still queued, waits for the pull in flight, then frees the decoded images and the videos on disk.
        """
        self.pool.clear()
        self.pool.waitForDone()
        for fileName in list(self.cache):
            self.drop(fileName)
        self.cache.clear()
        self.requested.clear()
        self.clearStale()


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
                self.drop(fileName)
        self.clearStale()


    def drop(self, fileName: str) -> None:
        """
        Forgets one preview, deleting its pulled copy if it was a video we had kept on disk.
        """
        image, videoPath, seconds = self.cache.pop(fileName)
        self.requested.discard(fileName)
        if videoPath:
            self.discard(Path(videoPath))


    def preview(self, fileName: str) -> tuple[QImage, str, float] | None:
        """
        The cached (image, video path, seconds) for fileName, or None while it is still being pulled.
        """
        return self.cache.get(fileName)


    def store(self, fileName: str, image: QImage, videoPath: str, seconds: float) -> None:
        """
        Takes a finished decode off the worker thread, caches it, then tells the screen it is there.
        """
        self.cache[fileName] = (image, videoPath, seconds)
        self.ready.emit(fileName)


    def discard(self, path: Path) -> None:
        """
        Deletes a pulled copy, keeping it back to retry if the player has not let go of it yet.
        """
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            log.debug("Could not delete %s yet, will retry: %s", path, e)
            self.stale.append(path)


    def clearStale(self) -> None:
        """
        Retries the deletes that failed while a file was still open.
        """
        for path in list(self.stale):
            try:
                path.unlink(missing_ok=True)
                self.stale.remove(path)
            except OSError:
                pass # still held, try again next time round


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
        Pulls fileName and reads a preview off it. Always emits, so a file we cannot preview still gets its card drawn.
        """
        if isImage(fileName):
            self.fetchImage(fileName)
        elif isVideo(fileName):
            self.fetchVideo(fileName)
        else:
            self.decoded.emit(fileName, QImage(), "", 0.0)


    def fetchImage(self, fileName: str) -> None:
        """
        Pulls a still, decodes it, then deletes the pulled copy.
        """
        target = self.pull(fileName)
        if target is None:
            self.decoded.emit(fileName, QImage(), "", 0.0)
            return
        image = self.viewer.loadImage(target)
        self.discard(target)
        self.decoded.emit(fileName, image if image is not None else QImage(), "", 0.0)


    def fetchVideo(self, fileName: str) -> None:
        """
        Pulls a clip and reads a poster frame off it, keeping the file for QMediaPlayer to play from.
        Anything over MAX_VIDEO_BYTES is left on the device and shows as a placeholder instead.
        """
        size = self.sizes.get(fileName, 0)
        if size > self.MAX_VIDEO_BYTES:
            log.info("%s is %.1f MB, over the %.0f MB preview cap, leaving it on the device", fileName, size / (1024 * 1024), self.MAX_VIDEO_BYTES / (1024 * 1024))
            self.decoded.emit(fileName, QImage(), "", 0.0)
            return
        target = self.pull(fileName)
        if target is None:
            self.decoded.emit(fileName, QImage(), "", 0.0)
            return
        image, seconds = self.clips.loadPoster(target)
        self.decoded.emit(fileName, image if image is not None else QImage(), str(target), seconds)


    def pull(self, fileName: str) -> Path | None:
        """
        Copies fileName off the device into the cache folder, returning where it landed.
        """
        target = cacheDirectory() / fileName
        if self.adb.pullFiles(remotePath=self.devicePath + fileName, localPath=str(target)):
            return target
        return None
