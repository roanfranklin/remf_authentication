from PyQt5 import (QtWidgets, QtGui, QtCore, uic)
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QInputDialog, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import (Qt, QUrl, QSize, QDir, QDate)
from PyQt5.QtGui import (QPixmap, QIcon, QFont, QPalette, QColor)

from src.icons import *

class frmNewAccount(QtWidgets.QDialog):
    def __init__(self, parent=None, dir_project=None, __data=None):
        super(frmNewAccount, self).__init__(parent)
        uic.loadUi('{0}/ui/frmNewAccount.ui'.format(dir_project), self)

        global CURRENT_DIR_APP
        global CURRENT_DATA

        CURRENT_DIR_APP = dir_project
        CURRENT_DATA = __data

        self.edtIssuer = self.findChild(QtWidgets.QLineEdit, 'edtIssuer')
        self.edtAccount = self.findChild(QtWidgets.QLineEdit, 'edtAccount')

        self.edtSecret = self.findChild(QtWidgets.QLineEdit, 'edtSecret')
        self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Password)

        self.cbTypeKey = self.findChild(QtWidgets.QComboBox, 'cbTypeKey')
        self.cbTypeKey.setEnabled(False)

        self.btnViewSecret = self.findChild(QtWidgets.QToolButton, 'btnViewSecret')
        self.btnViewSecret.clicked.connect(self.btnViewSecretClicked) 
        self.btnViewSecret.setIcon(icon_eye(CURRENT_DIR_APP))

        self.btnCancel = self.findChild(QtWidgets.QPushButton, 'btnCancel')
        self.btnCancel.clicked.connect(self.btnCancelClicked) 
        self.btnCancel.setIcon(icon_close(CURRENT_DIR_APP))

        self.btnOK = self.findChild(QtWidgets.QPushButton, 'btnOK')
        self.btnOK.clicked.connect(self.btnOKClicked) 
        self.btnOK.setIcon(icon_save(CURRENT_DIR_APP))

        self.roiGroups = {'basekey': '', 'issuer': '', 'account': '', 'secret': '', 'status': 1}

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
            self.roiGroups = {'basekey': '', 'account': '', 'issuer': '', 'secret': '', 'status': 1}
            self.close()

    def center(self):
       qr = self.frameGeometry()
       cp = QDesktopWidget().availableGeometry().center()
       qr.moveCenter(cp)
       self.move(qr.topLeft())

    def btnOKClicked(self):
        SECRET = str(self.edtSecret.text()).replace(" ","")
        self.roiGroups = {'basekey': self.cbTypeKey.currentText(), 'issuer': self.edtIssuer.text(), 'account': self.edtAccount.text(), 'secret': SECRET, 'status': 1}
        self.accept()

    def btnCancelClicked(self):
        self.roiGroups = {'basekey': '', 'account': '', 'issuer': '', 'secret': '', 'status': 1}
        self.close()

    def btnViewSecretClicked(self):
        if self.edtSecret.echoMode() == QtWidgets.QLineEdit.Normal:
            self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Password)
            self.btnViewSecret.setIcon(icon_eye(CURRENT_DIR_APP))
        else:
            self.edtSecret.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.btnViewSecret.setIcon(icon_eye_slash(CURRENT_DIR_APP))