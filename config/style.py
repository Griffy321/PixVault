"""
The stylesheet shared by every screen in the app.
"""

STYLESHEET = """
QWidget {
    background-color: #f4f5f7;
    color: #1f2430;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QLabel#pathLabel {
    color: #5a6270;
    font-size: 12px;
    padding-bottom: 2px;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 7px 10px;
}
QLineEdit:focus {
    border-color: #3d7eff;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 7px 8px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: #eef1f6;
}
QListWidget::item:selected {
    background-color: #3d7eff;
    color: #ffffff;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #d2d6dd;
    border-radius: 6px;
    padding: 7px 16px;
}
QPushButton:hover {
    background-color: #eaecf1;
}
QPushButton:pressed {
    background-color: #dee1e8;
}

QPushButton#confirmButton {
    background-color: #3d7eff;
    border-color: #3d7eff;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#confirmButton:hover {
    background-color: #2f6cea;
}
QPushButton#confirmButton:disabled {
    background-color: #dfe2e8;
    border-color: #dfe2e8;
    color: #9aa1ad;
}

QMessageBox {
    background-color: #ffffff;
}

/* Internal object names Qt gives the two lines of a message box. */
QMessageBox QLabel#qt_msgbox_label {
    color: #1f2430;
    font-size: 15px;
    font-weight: 600;
    min-width: 320px;           /* stops one-word errors making a tiny box */
    padding-bottom: 4px;
}
QMessageBox QLabel#qt_msgbox_informativelabel {
    color: #5a6270;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 78px;
    padding: 7px 18px;
}
"""
