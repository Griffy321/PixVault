from PySide6 import QtCore, QtWidgets, QtGui
import sys
import random

class NavigationScreen(QtWidgets.QWidget):

    def __init__(self):
        super().__init__() # a way to refer to the super class without calling 
        self.folders = []

        self.button = QtWidgets.QPushButton("Click Here!")
        self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    def magic(self):
        return [folder for folder in self.folders]