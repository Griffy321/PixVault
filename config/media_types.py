"""
The file extensions PixVault treats as media are stored here.
"""

IMAGE_TYPES = (
    ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff",
)

RAW_TYPES = (
    ".dng", ".raw", ".arw", ".cr2", ".cr3", ".crw", ".nef", ".nrw", ".orf", ".raf", ".rw2", ".srw", ".pef", ".sr2", ".erf", ".kdc", ".3fr", ".mef", ".mos", ".iiq", ".x3f",
)

VIDEO_TYPES = (
    ".mp4", ".m4v", ".mov", ".3gp", ".3g2", ".mkv", ".webm", ".avi", ".wmv", ".flv", ".f4v", ".mpg", ".mpeg", ".mpe", ".m2v", ".ts", ".m2ts", ".mts", ".ogv", ".vob", ".asf", ".divx", ".rm", ".rmvb", ".mxf",
)

MEDIA_TYPES = IMAGE_TYPES + RAW_TYPES + VIDEO_TYPES


def isMedia(fileName: str) -> bool:
    """True for any photo or video PixVault will back up."""
    return fileName.lower().endswith(MEDIA_TYPES)


def isImage(fileName: str) -> bool:
    """True for a still image, raw files included."""
    return fileName.lower().endswith(IMAGE_TYPES + RAW_TYPES)


def isVideo(fileName: str) -> bool:
    """True for a video, so the viewer knows to open it with OpenVideo."""
    return fileName.lower().endswith(VIDEO_TYPES)
