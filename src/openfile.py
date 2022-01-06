from PyQt5 import (QtWidgets, QtGui, QtCore, uic)
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QInputDialog, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import (Qt, QUrl, QSize, QDir, QDate, QSettings)
from PyQt5.QtGui import (QPixmap, QIcon, QFont, QPalette, QColor)

from src.icons import *
from src.database import *

import os

class frmOpenFile(QtWidgets.QDialog):
    def __init__(self, parent=None, dir_project=None, __data=None):
        super(frmOpenFile, self).__init__(parent)
        uic.loadUi('{0}/ui/frmOpenFile.ui'.format(dir_project), self)

        self.settings = QSettings("remf", "remfauth")

        print(QSettings.fileName(self.settings))

        global CURRENT_DIR_APP
        global CURRENT_DATA

        CURRENT_DIR_APP = dir_project
        CURRENT_DATA = __data

        self.edtFile = self.findChild(QtWidgets.QLineEdit, 'edtFile')
        self.edtFile.setText(self.settings.value("lastfile"))
        self.edtSecret = self.findChild(QtWidgets.QLineEdit, 'edtSecret')
        self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Password)        

        self.btnSelectFile = self.findChild(QtWidgets.QToolButton, 'btnSelectFile')
        self.btnSelectFile.clicked.connect(self.btnSelectFileClicked) 
        self.btnSelectFile.setIcon(icon_open(CURRENT_DIR_APP))

        self.btnTestConnection = self.findChild(QtWidgets.QToolButton, 'btnTestConnection')
        self.btnTestConnection.clicked.connect(self.btnTestConnectionFileClicked) 
        self.btnTestConnection.setIcon(icon_none(CURRENT_DIR_APP))

        self.btnViewSecret = self.findChild(QtWidgets.QToolButton, 'btnViewSecret')
        self.btnViewSecret.clicked.connect(self.btnViewSecretClicked) 
        self.btnViewSecret.setIcon(icon_eye(CURRENT_DIR_APP))

        self.btnCancel = self.findChild(QtWidgets.QPushButton, 'btnCancel')
        self.btnCancel.clicked.connect(self.btnCancelClicked) 
        self.btnCancel.setIcon(icon_close(CURRENT_DIR_APP))

        self.btnOK = self.findChild(QtWidgets.QPushButton, 'btnOK')
        self.btnOK.clicked.connect(self.btnOKClicked) 
        self.btnOK.setIcon(icon_save(CURRENT_DIR_APP))

        self.roiGroups = {'file': '', 'secret': ''}

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
            self.roiGroups = {'file': '', 'secret': ''}
            self.close()

    def center(self):
       qr = self.frameGeometry()
       cp = QDesktopWidget().availableGeometry().center()
       qr.moveCenter(cp)
       self.move(qr.topLeft())

    def __msg_error(self, TXT):
        QtWidgets.QMessageBox.warning(self, 'Error/Warning', TXT)

    def btnOKClicked(self):
        if self.btnTestConnectionFileClicked():
            self.settings.setValue("lastfile", self.edtFile.text())
            self.roiGroups = {'file': self.edtFile.text(), 'secret': self.edtSecret.text()}
            self.accept()
        else:
            self.__msg_error('Check your password!')

    def btnCancelClicked(self):
        self.roiGroups = {'file': '', 'secret': ''}
        self.close()

    def btnViewSecretClicked(self):
        if self.edtSecret.echoMode() == QtWidgets.QLineEdit.Normal:
            self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Password)
            self.btnViewSecret.setIcon(icon_eye(CURRENT_DIR_APP))
        else:
            self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.btnViewSecret.setIcon(icon_eye_slash(CURRENT_DIR_APP))

    def btnSelectFileClicked(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open file DB 2FA", "" ,"All Files (*);;SQLite3 Files (*.sqlite3)", options=options)
        if fileName:
            self.edtFile.setText(fileName)

    def btnTestConnectionFileClicked(self):
        __DATA = {'file': self.edtFile.text(), 'secret': self.edtSecret.text()}
        results = teste_connection(__DATA)
        if results is None:
            self.btnTestConnection.setIcon(icon_offline(CURRENT_DIR_APP))
            return False
        else:
            self.btnTestConnection.setIcon(icon_online(CURRENT_DIR_APP))
            return True
