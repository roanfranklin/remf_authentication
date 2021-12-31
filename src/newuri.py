from PyQt5 import (QtWidgets, QtGui, QtCore, uic)
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QInputDialog, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import (Qt, QUrl, QSize, QDir, QDate)
from PyQt5.QtGui import (QPixmap, QIcon, QFont, QPalette, QColor)

from src.icons import *

class frmNewURI(QtWidgets.QDialog):
    def __init__(self, parent=None, dir_project=None, __data=None):
        super(frmNewURI, self).__init__(parent)
        uic.loadUi('{0}/ui/frmNewURI.ui'.format(dir_project), self)

        global CURRENT_DIR_APP
        global CURRENT_DATA

        CURRENT_DIR_APP = dir_project
        CURRENT_DATA = __data

        self.edtURI = self.findChild(QtWidgets.QLineEdit, 'edtURI')
  
        self.btnCancel = self.findChild(QtWidgets.QPushButton, 'btnCancel')
        self.btnCancel.clicked.connect(self.btnCancelClicked) 
        self.btnCancel.setIcon(icon_close(CURRENT_DIR_APP))

        self.btnOK = self.findChild(QtWidgets.QPushButton, 'btnOK')
        self.btnOK.clicked.connect(self.btnOKClicked) 
        self.btnOK.setIcon(icon_save(CURRENT_DIR_APP))

        self.roiGroups = ''

        self.setWindowTitle(CURRENT_DATA)
       
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.center()
        self.setWindowModality(Qt.ApplicationModal)
        self.show()

    def closeEvent(self, event):
        event.accept()
        #self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.roiGroups = ''
            self.close()

    def center(self):
       qr = self.frameGeometry()
       cp = QDesktopWidget().availableGeometry().center()
       qr.moveCenter(cp)
       self.move(qr.topLeft())

    def btnOKClicked(self):
       self.roiGroups = self.edtURI.text()
       self.accept()

    def btnCancelClicked(self):
        self.roiGroups = ''
        self.close()
