from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QStackedWidget
from PySide6.QtCore import Signal, Qt, QTimer, QUrl
from PySide6.QtGui import QKeyEvent, QImage, QPixmap, QResizeEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from device import FileSaving
from config import STYLESHEET, isVideo
from visualisation import PreviewLoader
from pvlogging import getLogger

log = getLogger(__name__)

class SavingScreen(QWidget):
    """
    The screen where users can see the deduped files they will want to save.

    One card at a time: right keeps the file for backup, left drops it.
    self.saving.toBackup is the deck to review and is left alone until
    commitToBackup() replaces it with what the user kept.

    Previews come from self.loader, which pulls and decodes a few files ahead of the one on
    screen so a swipe does not wait on adb. Stills are drawn on a label, clips play in a
    video widget, and self.cardStack swaps between the two.
    """

    reviewFinished = Signal()


    def __init__(self, saving: FileSaving):
        super().__init__()
        self.saving = saving
        self.queue: list[str] = []      # deduped files still to be shown
        self.approved: list[str] = []   # the ones swiped right
        self.index = 0                  # position in self.queue
        self.cardPixmap: QPixmap | None = None # the preview at full size, rescaled to fit the card
        self.poster: QImage | None = None       # a clip's still, shown if Qt turns out not to play it
        self.loader = PreviewLoader(saving.adb)
        self.loader.ready.connect(self.onPreviewReady)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(12)
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("PixVault - Choose a folder")
        self.setStyleSheet(STYLESHEET)


    # builders - make a widget and add it to the layout (run once)
    def buildScreen(self) -> None:
        """
        Runs the builders in display order.
        """
        self.buildCounter()
        self.buildCard()
        self.buildPlayer()
        self.buildCaption()
        self.buildToast()
        self.buildFooter()
        self.buildMuteButton()
        self.buildSkipButton()
        self.buildKeepButton()


    def buildCounter(self) -> None:
        """
        Creates self.counterLabel, the "12 kept, 38 to go" line.
        """
        self.filesRemaining = QLabel(f"You have backed up {len(self.saving.toBackup)} out of {len(self.saving.deviceFileContent)} files.")
        self.layout.addWidget(self.filesRemaining)


    def buildCard(self) -> None:
        """
        Creates self.cardStack, the panel the current file is previewed in - a label for stills and placeholders, a video widget for clips.
        """
        self.cardStack = QStackedWidget()
        self.card = QLabel()
        self.card.setObjectName("card")
        self.card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card.setMinimumSize(1, 1)
        self.card.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored) # or the pixmap drives the layout and the window grows every resize
        self.videoCard = QVideoWidget()
        self.videoCard.setMinimumSize(1, 1)
        self.cardStack.addWidget(self.card)
        self.cardStack.addWidget(self.videoCard)
        self.layout.addWidget(self.cardStack, stretch=1)


    def buildPlayer(self) -> None:
        """
        Creates the player the video card draws into. Starts muted, a whole deck autoplaying sound is too much.
        """
        self.audio = QAudioOutput()
        self.audio.setMuted(True)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.videoCard)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.errorOccurred.connect(self.onPlayerError)


    def buildCaption(self) -> None:
        """
        Creates self.caption, the line under the card naming the file on it.
        """
        self.caption = QLabel()
        self.caption.setObjectName("pathLabel")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.caption)


    def buildToast(self) -> None:
        """
        Creates self.toast, the drop-down banner. Starts hidden.
        """
        self.toast = QLabel()
        self.toast.setObjectName("toast")
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.hide()
        self.layout.addWidget(self.toast)


    def buildFooter(self) -> None:
        """
        Creates self.footerRow, the row the two buttons sit in.
        """
        self.footerRow = QHBoxLayout()
        self.footerRow.setSpacing(8)
        self.layout.addLayout(self.footerRow)


    def buildMuteButton(self) -> None:
        """
        Creates the audio toggle, only enabled while a clip is on the card.
        """
        self.muteButton = QPushButton("Unmute")
        self.muteButton.setEnabled(False)
        self.footerRow.addWidget(self.muteButton)
        self.footerRow.addStretch()
        self.muteButton.clicked.connect(self.onMuteClicked)


    def buildSkipButton(self) -> None:
        """
        Creates the left button, wired to onSkipClicked.
        """
        self.skipButton = QPushButton("Skip")
        self.skipButton.setObjectName("skipButton")
        self.footerRow.addWidget(self.skipButton)
        self.skipButton.clicked.connect(self.onSkipClicked)


    def buildKeepButton(self) -> None:
        """
        Creates the right button, wired to onKeepClicked.
        """
        self.keepButton = QPushButton("Keep")
        self.keepButton.setObjectName("confirmButton")
        self.footerRow.addWidget(self.keepButton)
        self.keepButton.clicked.connect(self.onKeepClicked)


    # handlers - respond to a click (run every time the user acts)
    def onKeepClicked(self) -> None:
        """
        Appends currentFile() to self.approved, toasts, then advances.
        """
        fileName = self.currentFile()
        if fileName is None:
            return # Normally dont want to return nothing but this seems fair with how self.currentFile() is
        self.approved.append(fileName)
        self.showToast(f"Kept {fileName}")
        self.advance()


    def onSkipClicked(self) -> None:
        """
        Drops currentFile() and advances.
        """
        fileName = self.currentFile()
        if fileName is None:
            return # Normally dont want to return nothing but this seems fair with how self.currentFile() is
        self.showToast(f"Skipped {fileName}")
        self.advance()


    def onMuteClicked(self) -> None:
        """
        Flips the sound on or off. The choice sticks for the rest of the deck.
        """
        self.audio.setMuted(not self.audio.isMuted())
        self.muteButton.setText("Unmute" if self.audio.isMuted() else "Mute")


    def onPlayerError(self, error, message: str) -> None:
        """
        Falls back to the cv2 poster frame when Qt will not decode a clip, HEVC on a machine without the Windows extension being the usual cause.
        """
        fileName = self.currentFile()
        log.warning("Could not play %s (%s): %s, falling back to a still", fileName, error, message)
        if self.poster is not None and not self.poster.isNull():
            self.showStill(self.poster)
        elif fileName is not None:
            self.showStill(None, self.placeholderText(fileName))


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Maps the left and right arrow keys onto the two buttons.
        """
        if event.key() == Qt.Key.Key_Left:
            self.onSkipClicked()
        elif event.key() == Qt.Key.Key_Right:
            self.onKeepClicked()
        else:
            super().keyPressEvent(event)


    def onReviewFinished(self) -> None:
        """
        Runs once the deck is empty - commits the keepers and emits reviewFinished.
        """
        self.releasePlayer() # let go of the file before the loader deletes it
        self.loader.stop()   # nothing left to preview, and saveAll wants adb to itself
        self.commitToBackup()
        self.updateCounter()
        self.showCard()
        self.skipButton.setEnabled(False)
        self.keepButton.setEnabled(False)
        self.reviewFinished.emit()


    # shared - the work both of the above lean on
    def startBackup(self, path: str) -> None:
        """
        Loads the deduped files for path and draws the first card. The PC destination is expected to already be set on self.saving.local by the destination screen before this runs.
        """
        self.skipButton.setEnabled(True)
        self.keepButton.setEnabled(True)
        self.saving.loadDeviceFolderContent(path)
        self.saving.local.loadPCFolderContent()
        self.saving.buildBackupList()
        self.loadQueue()
        self.loader.start(self.saving.devicePath, self.queue, self.saving.deviceFileContent)
        self.updateCounter()
        self.showCard()


    def loadQueue(self) -> None:
        """
        Copies self.saving.toBackup into self.queue and resets self.index.
        """
        self.queue = list(self.saving.toBackup)
        self.approved = []
        self.index = 0


    def currentFile(self) -> str | None:
        """
        The file on the card now, or None once the deck is empty.
        """
        if self.index < len(self.queue):
            return self.queue[self.index]
        return None


    def advance(self) -> None:
        """
        Steps to the next file and redraws, or finishes if there is none.
        """
        self.index += 1
        self.releasePlayer() # let go before prefetch evicts the file we were playing
        if self.currentFile() is None:
            self.onReviewFinished()
        else:
            self.loader.prefetch(self.index)
            self.updateCounter()
            self.showCard()


    def showCard(self) -> None:
        """
        Draws the preview for currentFile(), or says it is loading until the pull lands.
        """
        fileName = self.currentFile()
        if fileName is None:
            self.caption.clear()
            self.showStill(None, "All files reviewed.")
            return
        preview = self.loader.preview(fileName)
        if preview is None:
            self.caption.setText(fileName)
            self.showStill(None, f"Loading {fileName}...")
        else:
            self.drawPreview(fileName, preview)


    def onPreviewReady(self, fileName: str) -> None:
        """
        Draws a preview that landed after its card was already up, ignoring the ones the user has swiped past.
        """
        if fileName == self.currentFile():
            self.drawPreview(fileName, self.loader.preview(fileName))


    def drawPreview(self, fileName: str, preview: tuple[QImage, str, float]) -> None:
        """
        Puts the preview on the card - a clip plays, a still is drawn, and anything we could not read falls back to the placeholder.
        """
        image, videoPath, seconds = preview
        self.poster = image
        self.caption.setText(self.captionText(fileName, seconds))
        if videoPath:
            self.playVideo(videoPath)
        elif not image.isNull():
            self.showStill(image)
        else:
            self.showStill(None, self.placeholderText(fileName))


    def playVideo(self, videoPath: str) -> None:
        """
        Points the player at the pulled copy and loops it while the card is up.
        """
        self.cardStack.setCurrentWidget(self.videoCard)
        self.muteButton.setEnabled(True)
        self.player.setSource(QUrl.fromLocalFile(videoPath))
        self.player.play()


    def showStill(self, image: QImage | None, message: str = "") -> None:
        """
        Brings the label forward with either a picture or a line of text on it.
        """
        self.releasePlayer()
        self.cardStack.setCurrentWidget(self.card)
        if image is None or image.isNull():
            self.cardPixmap = None
            self.card.setText(message)
        else:
            self.cardPixmap = QPixmap.fromImage(image)
            self.scaleCard()


    def releasePlayer(self) -> None:
        """
        Stops playback and lets go of the file, or Windows will not let the loader delete it.
        """
        self.muteButton.setEnabled(False)
        if self.player.source().isEmpty():
            return
        self.player.stop()
        self.player.setSource(QUrl())


    def scaleCard(self) -> None:
        """
        Redraws self.cardPixmap at the card's current size.
        """
        if self.cardPixmap is None:
            return
        self.card.setPixmap(self.cardPixmap.scaled(self.card.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Keeps the preview filling the card as the window changes size.
        """
        super().resizeEvent(event)
        self.scaleCard()


    def placeholderText(self, fileName: str) -> str:
        """
        What the card shows for a file we cannot preview - a clip over the size cap, or a format nothing will decode.
        """
        size = self.saving.deviceFileContent.get(fileName, 0)
        if isVideo(fileName) and size > PreviewLoader.MAX_VIDEO_BYTES:
            reason = "Too large to preview"
        else:
            reason = "No preview available"
        return f"{fileName}\n{size / (1024 * 1024):.1f} MB\n\n{reason}"


    def captionText(self, fileName: str, seconds: float) -> str:
        """
        The line under the card - the file name, plus a clip's length once we know it.
        """
        if seconds > 0:
            return f"{fileName}   {int(seconds) // 60}:{int(seconds) % 60:02d}"
        return fileName


    def showToast(self, message: str) -> None:
        """
        Drops the banner down with message, then hides it again.
        """
        self.toast.setText(message)
        self.toast.show()
        QTimer.singleShot(1200, self.toast.hide)


    def updateCounter(self) -> None:
        """
        Refreshes self.counterLabel from approvedCount() and mediaRemaining().
        """
        self.filesRemaining.setText(f"{self.approvedCount()} kept, {self.mediaRemaining()} to go")


    def approvedCount(self) -> int:
        """
        How many files the user has kept so far.
        """
        return len(self.approved)


    def mediaRemaining(self) -> int:
        """
        Returns the number of files still to be reviewed.
        """
        return max(len(self.queue) - self.index, 0)


    def commitToBackup(self) -> None:
        """
        Replaces self.saving.toBackup with self.approved, so saveAll only pulls the keepers.
        """
        self.saving.toBackup = list(self.approved)


    @staticmethod
    def formatProgress(transferred: int, total: int) -> str:
        """
        Turns raw byte counts into a line to put on screen, e.g. "12.8 MB of 240 MB".
        Takes its numbers as arguments so it stays testable without a device attached.
        """
        def toMB(value: int) -> str:
            return f"{value / (1024 * 1024):.1f} MB"
        return f"{toMB(transferred)} of {toMB(total)}"
