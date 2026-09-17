"""
This class handles opening videos using cv2
"""

import cv2 as cv
from pathlib import Path

from PySide6.QtGui import QImage
from visualisation.images import OpenImage
from pvlogging import getLogger

log = getLogger(__name__)


class OpenVideo:
    """
    Reads a pulled video with cv2, for the poster frame the card falls back to when Qt will not play it.
    """

    POSTER_AT = 0.1 # a tenth in, the opening frames are often black or still focusing


    def __init__(self):
        self.stills = OpenImage()


    def loadPoster(self, path: Path) -> tuple[QImage | None, float]:
        """
        Grabs a representative frame and the clip's length in one pass, returning (None, 0.0) if cv2 cannot open it.
        Safe to call off the GUI thread, QImage is, QPixmap is not.
        """
        capture = cv.VideoCapture(str(path))
        if not capture.isOpened():
            log.info("cv2 could not open %s, it will show as no preview", path.name)
            return None, 0.0
        try:
            fps = capture.get(cv.CAP_PROP_FPS)
            frames = capture.get(cv.CAP_PROP_FRAME_COUNT)
            read, frame = self.readPoster(capture, frames)
        finally:
            capture.release()
        seconds = frames / fps if fps > 0 and frames > 0 else 0.0
        if not read:
            log.info("cv2 opened %s but could not read a frame from it", path.name)
            return None, seconds
        return self.stills.fromFrame(frame), seconds


    def readPoster(self, capture, frames: float):
        """
        Reads the frame a tenth of the way in, falling back to the first one on a short or damaged clip.
        """
        if frames > 0:
            capture.set(cv.CAP_PROP_POS_FRAMES, int(frames * self.POSTER_AT))
        read, frame = capture.read()
        if not read:
            capture.set(cv.CAP_PROP_POS_FRAMES, 0)
            read, frame = capture.read()
        return read, frame
