import random
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFrame
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QPropertyAnimation, QParallelAnimationGroup,
    QEasingCurve, QAbstractAnimation, Signal
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics

CARD_COLORS = [
    "#FF6B6B", "#FF8E53", "#FFC842", "#2ECC71", "#1ABC9C",
    "#3498DB", "#9B59B6", "#E74C3C", "#F39C12", "#27AE60",
    "#16A085", "#2980B9", "#8E44AD", "#E91E63", "#00BCD4",
    "#FF5722", "#795548", "#607D8B", "#4CAF50", "#03A9F4",
    "#FF4081", "#7C4DFF", "#00E676", "#FFAB40", "#40C4FF",
    "#EA80FC", "#69F0AE", "#FFD740", "#FF6D00", "#B9F6CA",
    "#80D8FF", "#CE93D8", "#FFCC80", "#90CAF9", "#A5D6A7",
    "#F48FB1", "#80CBC4", "#FFE082", "#EF9A9A", "#B39DDB",
    "#81D4FA", "#C5E1A5", "#FFAB91", "#80DEEA", "#F8BBD0",
    "#DCEDC8", "#B3E5FC", "#E1BEE7", "#FFF9C4", "#FFCCBC",
]

CARD_W = 280
CARD_H = 390


def generate_cards(count=50):
    return [{"id": i + 1, "color": CARD_COLORS[i % len(CARD_COLORS)]} for i in range(count)]


from PySide6.QtWidgets import QGraphicsObject


class CardItem(QGraphicsObject):
    dismissed = Signal(bool)  # True = right (backup), False = left (skip)
    drag_updated = Signal(float)  # -1.0 to 1.0

    def __init__(self, card_data, parent=None):
        super().__init__(parent)
        self.card_data = card_data
        self.is_top = False
        self._drag_start = None
        self._start_pos = QPointF(0, 0)
        self._drag_ratio = 0.0
        self._animating = False
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return QRectF(-CARD_W / 2, -CARD_H / 2, CARD_W, CARD_H)

    def paint(self, painter, option, widget=None):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)

        # Card background
        painter.setBrush(QBrush(QColor(self.card_data["color"])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 18, 18)

        # Subtle inner shadow / gradient top strip
        painter.setBrush(QBrush(QColor(255, 255, 255, 25)))
        painter.drawRoundedRect(QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.4), 18, 18)

        # Direction overlay
        if abs(self._drag_ratio) > 0.05:
            alpha = int(min(abs(self._drag_ratio) * 160, 140))
            if self._drag_ratio > 0:
                overlay = QColor(40, 220, 120, alpha)
            else:
                overlay = QColor(255, 60, 60, alpha)
            painter.setBrush(QBrush(overlay))
            painter.drawRoundedRect(rect, 18, 18)

        # Card number
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        font = QFont("Segoe UI", 36, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, -30, 0, 0), Qt.AlignCenter, f"#{self.card_data['id']}")

        # Label text below number
        painter.setPen(QPen(QColor(255, 255, 255, 160)))
        small_font = QFont("Segoe UI", 13)
        painter.setFont(small_font)
        painter.drawText(rect.adjusted(0, 40, 0, 0), Qt.AlignCenter, "Photo")

        # BACKUP / SKIP stamp
        if abs(self._drag_ratio) > 0.25:
            stamp = "BACKUP" if self._drag_ratio > 0 else "SKIP"
            stamp_color = QColor(40, 230, 120) if self._drag_ratio > 0 else QColor(255, 60, 60)
            stamp_x = rect.left() + 20 if self._drag_ratio < 0 else rect.right() - 130
            stamp_rect = QRectF(stamp_x, rect.top() + 24, 120, 44)
            painter.setPen(QPen(stamp_color, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(stamp_rect, 6, 6)
            stamp_font = QFont("Segoe UI", 15, QFont.Bold)
            painter.setFont(stamp_font)
            painter.drawText(stamp_rect, Qt.AlignCenter, stamp)

    def make_top(self):
        self.is_top = True
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if self._animating:
            return
        self._drag_start = event.pos()
        self._start_pos = self.pos()
        self.setCursor(Qt.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_start is None or self._animating:
            return
        delta = event.pos() - self._drag_start
        new_pos = self._start_pos + QPointF(delta.x(), delta.y() * 0.25)
        self.setPos(new_pos)
        self.setRotation(delta.x() * 0.06)
        self._drag_ratio = max(-1.0, min(1.0, delta.x() / 160.0))
        self.drag_updated.emit(self._drag_ratio)
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_start is None:
            return
        self.setCursor(Qt.OpenHandCursor)
        if abs(self._drag_ratio) >= 0.55:
            self.animate_dismiss(self._drag_ratio > 0)
        else:
            self._animate_return()
        self._drag_start = None
        event.accept()

    def animate_dismiss(self, to_right):
        self._animating = True
        direction = 1 if to_right else -1
        target_x = direction * 700
        target_y = self.pos().y() + 60

        anim_pos = QPropertyAnimation(self, b"pos")
        anim_pos.setDuration(320)
        anim_pos.setEndValue(QPointF(target_x, target_y))
        anim_pos.setEasingCurve(QEasingCurve.OutQuad)

        anim_rot = QPropertyAnimation(self, b"rotation")
        anim_rot.setDuration(320)
        anim_rot.setEndValue(direction * 28.0)

        self._dismiss_group = QParallelAnimationGroup()
        self._dismiss_group.addAnimation(anim_pos)
        self._dismiss_group.addAnimation(anim_rot)
        self._dismiss_group.finished.connect(lambda: self.dismissed.emit(to_right))
        self._dismiss_group.start()

    def _animate_return(self):
        self._drag_ratio = 0.0
        self.drag_updated.emit(0.0)

        anim_pos = QPropertyAnimation(self, b"pos")
        anim_pos.setDuration(220)
        anim_pos.setEndValue(self._start_pos)
        anim_pos.setEasingCurve(QEasingCurve.OutBack)

        anim_rot = QPropertyAnimation(self, b"rotation")
        anim_rot.setDuration(220)
        anim_rot.setEndValue(0.0)
        anim_rot.setEasingCurve(QEasingCurve.OutBack)

        grp = QParallelAnimationGroup(self)
        grp.addAnimation(anim_pos)
        grp.addAnimation(anim_rot)
        grp.finished.connect(self.update)
        grp.start(QAbstractAnimation.DeleteWhenStopped)
        self.update()


# Stack visual config: (x, y, scale, z-value) per position index (0=top)
_STACK_POS = [
    (0, 0,  1.00, 10),
    (0, 18, 0.95,  9),
    (0, 34, 0.90,  8),
]


class CardStackView(QGraphicsView):
    card_dismissed = Signal(dict, bool)  # card_data, to_right (True=backup)
    drag_ratio_changed = Signal(float)
    deck_empty = Signal()

    def __init__(self, cards, parent=None):
        super().__init__(parent)
        self._all_cards = cards
        self._deck_index = 0
        self._items = []  # index 0 = top card

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.setSceneRect(-320, -260, 640, 560)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(Qt.transparent))
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._build_stack()

    def _build_stack(self):
        count = min(len(_STACK_POS), len(self._all_cards) - self._deck_index)
        for slot in range(count - 1, -1, -1):
            card_data = self._all_cards[self._deck_index + slot]
            item = CardItem(card_data)
            self._apply_slot(item, slot)
            self._scene.addItem(item)
            self._items.insert(0, item)
        if self._items:
            self._items[0].make_top()
            self._items[0].dismissed.connect(self._on_dismissed)
            self._items[0].drag_updated.connect(self.drag_ratio_changed)

    def _apply_slot(self, item, slot):
        x, y, scale, z = _STACK_POS[slot]
        item.setPos(x, y)
        item.setScale(scale)
        item.setZValue(z)

    def _on_dismissed(self, to_right):
        top = self._items.pop(0)
        card_data = top.card_data
        self._scene.removeItem(top)
        self._deck_index += 1

        # Animate remaining cards up to new slots
        for new_slot, item in enumerate(self._items):
            x, y, scale, z = _STACK_POS[new_slot]
            item.setZValue(z)
            for prop, val in ((b"pos", QPointF(x, y)), (b"scale", scale)):
                anim = QPropertyAnimation(item, prop)
                anim.setDuration(240)
                anim.setEndValue(val)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start(QAbstractAnimation.DeleteWhenStopped)

        # Bring in the next card at the back slot
        next_idx = self._deck_index + len(self._items)
        if next_idx < len(self._all_cards):
            new_item = CardItem(self._all_cards[next_idx])
            back_slot = len(self._items)
            if back_slot < len(_STACK_POS):
                self._apply_slot(new_item, back_slot)
                self._scene.addItem(new_item)
                self._items.append(new_item)

        # Wire up new top card
        if self._items:
            self._items[0].make_top()
            self._items[0].dismissed.connect(self._on_dismissed)
            self._items[0].drag_updated.connect(self.drag_ratio_changed)
        else:
            self.deck_empty.emit()

        self.card_dismissed.emit(card_data, to_right)

    def swipe_left(self):
        if self._items and not self._items[0]._animating:
            self._items[0].animate_dismiss(False)

    def swipe_right(self):
        if self._items and not self._items[0]._animating:
            self._items[0].animate_dismiss(True)

    def cards_remaining(self):
        return len(self._all_cards) - self._deck_index
