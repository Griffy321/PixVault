"""
This class handles opening images using cv2
"""

import cv2 as cv
import numpy as np
from pathlib import Path

from PySide6.QtGui import QImage
from pvlogging import getLogger

log = getLogger(__name__)


class OpenImage:
    """
    Turns a pulled image file into a QImage the saving card can draw.
    """

    MAX_EDGE = 1280 # previews are shrunk to this before being handed over


    def loadImage(self, path: Path) -> QImage | None:
        """
        Reads path with cv2 and returns it as a QImage, or None if cv2 cannot decode it.
        Safe to call off the GUI thread, QImage is, QPixmap is not.
        """
        image = self.decode(path)
        if image is None:
            return None
        return self.fromFrame(image)


    def fromFrame(self, image) -> QImage:
        """
        Turns a BGR frame from cv2 into a QImage the card can draw, video frames included.
        """
        image = self.shrink(image)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        height, width, channels = image.shape
        # QImage does not copy the buffer it is handed, so copy it before the numpy array is collected
        return QImage(image.data, width, height, channels * width, QImage.Format.Format_RGB888).copy()


    def decode(self, path: Path):
        """
        Reads the file off disk and hands it to cv2, returning None for anything cv2 has no decoder for.
        """
        try:
            data = np.fromfile(str(path), dtype=np.uint8) # imread cannot open non ascii paths on Windows
        except OSError as e:
            log.warning("Could not read %s off disk: %s", path, e)
            return None
        image = cv.imdecode(data, cv.IMREAD_COLOR)
        if image is None:
            log.info("cv2 has no decoder for %s, it will show as no preview", path.name)
        return image


    def shrink(self, image):
        """
        Scales image down until its longest edge is MAX_EDGE, leaving anything smaller alone.
        """
        height, width = image.shape[:2]
        longest = max(height, width)
        if longest <= self.MAX_EDGE:
            return image
        scale = self.MAX_EDGE / longest
        return cv.resize(image, (int(width * scale), int(height * scale)), interpolation=cv.INTER_AREA)
