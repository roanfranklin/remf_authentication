#!/usr/bin/python3

from PyQt5 import (QtWidgets, QtGui, QtCore, uic)
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox,
                            QDesktopWidget, QInputDialog, QTableWidgetItem, QFileDialog,
                            QSystemTrayIcon, QAction, QStyle, QMenu, qApp,
                            QLineEdit)
from PyQt5.QtCore import (Qt, QUrl, QSize, QFile, QDir, QTimer, QStandardPaths)
from PyQt5.QtGui import (QPixmap, QIcon, QFont, QPalette, QColor)

import sys
import os
import pyotp
import pyperclip as pc
import qrcode
import datetime as dt

DIR_APP = '{0}'.format(os.path.dirname(os.path.realpath(__file__)))
DIR_CFG = '{0}/remf_auth/'.format(QStandardPaths.writableLocation(QStandardPaths.ConfigLocation))
# APP_DATA = {'file': '{0}/data/database.sqlite3'.format(DIR_APP), 'secret': ''}
APP_DATA = {'file': '', 'secret': ''}

from src.database import *
from src.git import *
from src.icons import *
from src.newaccount import *
from src.newuri import *
from src.openfile import *
from src.qrcode import *

APP_TITLE = 'REMF 2FA'
APP_TITLE_COMPLETE = 'REMF 2 Factor Authentication'
APP_MSG = 'Simple application client of 2FA.'
APP_AUTHOR = 'Roan Franklin'
APP_EMAIL =  'roanfranklin@gmail.com'
APP_SITE = 'https://www.remf.com.br/'
APP_VERSION = git_version(DIR_APP)
APP_GIT_STATUS = git_status(DIR_APP)
status_quit = False
debug = False


class frmMain(QtWidgets.QMainWindow):
    check_box = None
    tray_icon = None

    def __init__(self):
        super(frmMain, self).__init__()
        uic.loadUi('{0}/ui/frmMain.ui'.format(DIR_APP), self)

        #initial_sqlite(APP_DATA)

        self.CONNECTED = False
        self.CONNECTED_index = -1

        self.view_secrets = False

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon_app(DIR_APP))

        show_action = QAction("Show", self)
        hide_action = QAction("Hide", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.__app_hide)
        quit_action.triggered.connect(self.__app_quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        tray_menu2 = QMenu()
        tray_menu2.addAction(hide_action)
        tray_menu2.addAction(quit_action)

        add_account_action = QAction("Account", self)
        add_uri_action = QAction("URI/Text", self)
        add_qrcode_action = QAction("QR Code", self)
        add_account_action.triggered.connect(self.__add_account)
        add_uri_action.triggered.connect(self.__add_uri)
        add_qrcode_action.triggered.connect(self.__add_qrcode)
        popup_menu_add = QMenu()
        popup_menu_add.addAction(add_account_action)
        popup_menu_add.addAction(add_uri_action)
        popup_menu_add.addAction(add_qrcode_action)

        self.twSaved = self.findChild(QtWidgets.QTableWidget, 'twSaved')
        self.twSaved.itemSelectionChanged.connect(self.twSavedSelectedClick)
        self.twSaved.itemDoubleClicked.connect(self.btnCopyClicked)
        self.twSaved.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.twSaved.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.twSaved.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.twSaved.verticalHeader().setVisible(False)
        self.twSaved.horizontalHeader().setVisible(False)
        self.twSaved.setIconSize(QSize(44,44))
        self.twSaved.verticalHeader().setDefaultSectionSize(48)

        # self.twSaved.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.twSaved.customContextMenuRequested.connect(self.twSavedPopupMenu)
        # self.twSaved.viewport().installEventFilter(self)
        
        self.btnOpen = self.findChild(QtWidgets.QToolButton, 'btnOpen')
        self.btnOpen.clicked.connect(self.btnOpenClicked)
        self.btnOpen.setIcon(icon_open(DIR_APP))
        self.btnOpen.setToolTip("Open file DB-2FA")

        self.btnNew = self.findChild(QtWidgets.QToolButton, 'btnNew')
        self.btnNew.setMenu(popup_menu_add)
        self.btnNew.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btnNew.setIcon(icon_plus(DIR_APP))
        self.btnNew.setToolTip("New register 2FA")

        self.btnViewSecret = self.findChild(QtWidgets.QToolButton, 'btnViewSecret')
        self.btnViewSecret.clicked.connect(self.btnViewSecretClicked) 
        self.btnViewSecret.setIcon(icon_eye_slash(DIR_APP))
        self.btnViewSecret.setToolTip("View Secrets 2FA")

        self.btnUp = self.findChild(QtWidgets.QToolButton, 'btnUp')
        self.btnUp.clicked.connect(self.btnUpClicked)
        self.btnUp.setIcon(icon_up(DIR_APP))
        self.btnUp.setToolTip("Up item selected")

        self.btnDown = self.findChild(QtWidgets.QToolButton, 'btnDown')
        self.btnDown.clicked.connect(self.btnDownClicked)
        self.btnDown.setIcon(icon_down(DIR_APP))
        self.btnDown.setToolTip("Down item selected")

        self.btnCfg = self.findChild(QtWidgets.QToolButton, 'btnCfg')
        self.btnCfg.clicked.connect(self.btnCfgClicked)
        self.btnCfg.setIcon(icon_cogs(DIR_APP))
        self.btnCfg.setToolTip("Configuration")

        self.lbStatus = self.findChild(QtWidgets.QLabel, 'lbStatus')
        self.lbStatus.setText("")

        self.pbTimeOut = self.findChild(QtWidgets.QProgressBar, 'pbTimeOut')
        self.pbTimeOut.setMinimum(0)
        self.pbTimeOut.setMaximum(30)
        self.pbTimeOut.setValue(30)
        self.pbTimeOut.setFormat("Update in %v of %m seconds")

        self.time_notify = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_func)

        self.btnCopy = self.findChild(QtWidgets.QToolButton, 'btnCopy')
        self.btnCopy.clicked.connect(self.btnCopyClicked)
        self.btnCopy.setIcon(icon_copy(DIR_APP))
        self.btnCopy.setToolTip("Copy Key")

        self.btnQRCode = self.findChild(QtWidgets.QToolButton, 'btnQRCode')
        self.btnQRCode.clicked.connect(self.btnQRCodeClicked)
        self.btnQRCode.setIcon(icon_qrcode(DIR_APP))
        self.btnQRCode.setToolTip("View QRCode")

        self.btnDelete = self.findChild(QtWidgets.QToolButton, 'btnDelete')
        self.btnDelete.clicked.connect(self.btnDeleteClicked)
        self.btnDelete.setIcon(icon_trash(DIR_APP))
        self.btnDelete.setToolTip("Delete saved")

        self.btnAboutQt = self.findChild(QtWidgets.QToolButton, 'btnAboutQt')
        self.btnAboutQt.clicked.connect(self.__action_about_qt) 
        self.btnAboutQt.setIcon(icon_qt(DIR_APP))
        self.btnAboutQt.setToolTip("About Qt")

        self.btnAbout = self.findChild(QtWidgets.QToolButton, 'btnAbout')
        self.btnAbout.clicked.connect(self.__action_about) 
        self.btnAbout.setIcon(icon_question(DIR_APP))
        self.btnAbout.setToolTip("About App")

        self.btnClose = self.findChild(QtWidgets.QToolButton, 'btnClose')
        self.btnClose.setMenu(tray_menu2)
        self.btnClose.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.btnClose.setIcon(icon_quit(DIR_APP))
        self.btnClose.setToolTip("Hide/Exit")

        self.btnNew.setEnabled(False)
        self.btnCopy.setEnabled(False)
        self.btnQRCode.setEnabled(False)
        self.btnDelete.setEnabled(False)
        self.btnUp.setEnabled(False)
        self.btnDown.setEnabled(False)

        width = 661
        height = 504

        self.setWindowIcon(icon_app(DIR_APP))
        self.setWindowTitle('{0} ( {1} )'.format(APP_TITLE, APP_VERSION))

        self.setFixedWidth(width)
        self.setFixedHeight(height)

        self.center()
        self.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint, False)
        self.__app_hide()
        self.btnOpenClicked()      

    def closeEvent(self, event):
        if status_quit == False:
            event.ignore()
            self.__app_hide()
        else:
            event.accept()

    def center(self):
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        new_left = int((screen.width() - size.width()) / 2)
        new_top = int((screen.height() - size.height()) / 2)
        self.move(new_left, new_top)

    def __msg_error(self, TXT):
        QtWidgets.QMessageBox.warning(self, 'Error/Warning', TXT)

    def __action_about(self):
        QtWidgets.QMessageBox.about(self, 'About', f'<b>{APP_TITLE} - <i>{APP_TITLE_COMPLETE}</i></b><br><i>Version {APP_VERSION} {APP_GIT_STATUS}</i><br><br>{APP_MSG}<br><br><b>Author:</b> {APP_AUTHOR} - <i>{APP_EMAIL}</i><br><b>Web:</b> {APP_SITE}<br>')

    def __action_about_qt(self):
        QtWidgets.QMessageBox.aboutQt(self)
    
    def __app_hide(self):
        status_quit = False
        self.hide()
    
    def __app_quit(self):
        reply = QMessageBox.question(self, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION), "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            status_quit = True
            qApp.quit()
  
    def twSavedSelectedClick(self):
        index=(self.twSaved.selectionModel().currentIndex())
        value=index.sibling(index.row(),0).data()

    def btnOpenClicked(self):
        result = frmOpenFile(self, DIR_APP, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION))
        if result.exec_() == QtWidgets.QDialog.Accepted:
            self.__load(result.roiGroups)
            self.show()
    
    def btnViewSecretClicked(self):
        if self.view_secrets == True:
            self.view_secrets = False
            self.btnViewSecret.setIcon(icon_eye_slash(DIR_APP))
            self.__update()
        else:
            self.view_secrets = True
            self.btnViewSecret.setIcon(icon_eye(DIR_APP))
            self.__update()

    def __load(self, DATA):
        global APP_DATA
        APP_DATA = DATA
        self.time_notify = 0
        self.timer.start(1000)

        self.twSaved.setRowCount(0)

        try:
            rows = sqlite_query(APP_DATA, 'SELECT * FROM auth ORDER BY myorder ASC')
            self.twSaved.clearContents()
            if not debug:
                self.twSaved.setColumnHidden(0, True)
                self.twSaved.setColumnHidden(1, True)
                self.twSaved.setColumnHidden(2, True)
            for row in rows:
                inx = rows.index(row)
                self.twSaved.insertRow(inx)

                ICON_RPC = icon_none(DIR_APP)

                self.twSaved.setItem(inx, 0, QtWidgets.QTableWidgetItem('{0}'.format(row['id'])))
                self.twSaved.setItem(inx, 1, QtWidgets.QTableWidgetItem('{0}'.format(row['myorder'])))
                #self.twSaved.setCellWidget(inx, 2, self.btnCopy())
                self.twSaved.setItem(inx, 3, QtWidgets.QTableWidgetItem(''))
                self.twSaved.setItem(inx, 4, QtWidgets.QTableWidgetItem('{0}'.format(row['issuer'])))
                self.twSaved.setItem(inx, 5, QtWidgets.QTableWidgetItem('{0}'.format(row['account'])))

                self.twSaved.selectRow(0)

                hSaved = self.twSaved.horizontalHeader()
                hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)

                self.btnNew.setEnabled(True)
                self.btnCopy.setEnabled(True)
                self.btnQRCode.setEnabled(True)
                self.btnDelete.setEnabled(True)
                self.btnUp.setEnabled(True)
                self.btnDown.setEnabled(True)

            self.__update()
        except:
            pass

    def __new(self, RPC_DATA):
        try:
            row, status = db_insertRPC(APP_DATA, RPC_DATA)
            inx = self.twSaved.rowCount()
        
            self.twSaved.insertRow(inx)

            self.twSaved.setItem(inx, 0, QtWidgets.QTableWidgetItem('{0}'.format(row['id'])))
            self.twSaved.setItem(inx, 1, QtWidgets.QTableWidgetItem('{0}'.format(row['myorder'])))
            #self.twSaved.setCellWidget(inx, 2, self.btnCopy())
            #self.twSaved.setItem(inx, 3, QtWidgets.QTableWidgetItem(''))
            self.twSaved.setItem(inx, 4, QtWidgets.QTableWidgetItem('{0}'.format(RPC_DATA['issuer'])))
            self.twSaved.setItem(inx, 5, QtWidgets.QTableWidgetItem('{0}'.format(RPC_DATA['account'])))

            self.twSaved.selectRow(inx)

            hSaved = self.twSaved.horizontalHeader()
            hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)

            self.__update()
        except:
            self.__msg_error('Error!')

    def __add_account(self):
        try:      
            result = frmNewAccount(self, DIR_APP, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION))
            if result.exec_() == QtWidgets.QDialog.Accepted:
                self.__new(result.roiGroups)
        except:
            self.__msg_error('Error!')

    def __add_uri(self):
        try:
            result = frmNewURI(self, DIR_APP, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION))
            if result.exec_() == QtWidgets.QDialog.Accepted:
                DATA_TOTP = pyotp.parse_uri(result.roiGroups)
                RPC_DATA = {'basekey': 'totp', 'account': DATA_TOTP.name, 'issuer': DATA_TOTP.issuer, 'secret': DATA_TOTP.secret, 'status': 1}
                self.__new(RPC_DATA)
        except:
            self.__msg_error('Error!')

    def btnQRCodeClicked(self):
        index = self.twSaved.selectionModel().currentIndex()
        value = index.sibling(index.row(),0).data()
        row = db_selectoneRPC(APP_DATA, value)
        try:
            URI_TOTP = pyotp.totp.TOTP(row['secret']).provisioning_uri(name=row['account'], issuer_name=row['issuer'])
            img = qrcode.make(URI_TOTP)
            img.save('{0}/data/qrcode.png'.format(DIR_APP))
            frmQRCode(self, DIR_APP, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION))
        except:
            self.__msg_error('Error')

    def __add_qrcode(self):
        self.__msg_error('Add QR Code Not Configured!')

    def update_func(self):
        totp = pyotp.TOTP('LG27KXRFVIZX3BSQ') # Valor base32 aleatório para criar um temporizador padrão!
        time_remaining = totp.interval - dt.datetime.now().timestamp() % totp.interval
        self.pbTimeOut.setValue(int(time_remaining))
        if int(time_remaining) == 29:
            self.__update()

        self.time_notify -= 1
        if self.time_notify == 0:
            self.lbStatus.setText('')

    def btnCopyClicked(self):
        index = self.twSaved.selectionModel().currentIndex()
        value = index.sibling(index.row(),0).data()
        row = db_selectoneRPC(APP_DATA, value)
        #vkey = index.sibling(index.row(),3).data()
        vissuer = index.sibling(index.row(),4).data()
        try:
            TOTP_X = pyotp.TOTP(row['secret'])
            URI_TOTP = TOTP_X.provisioning_uri(name=row['account'], issuer_name=row['issuer'])
            __DATA = pyotp.parse_uri(URI_TOTP)
            vkey = __DATA.now()
            pc.copy(vkey)
            MSG = 'copied <b>{0}</b>'.format(row['issuer'])
        except:
            MSG = 'ERROR: Not copied <b>{0}</b>'.format(vissuer)
        finally:        
            self.lbStatus.setText(MSG)
            self.time_notify = 8
    
    def __update(self):
        maxRow = maxCol = -1
        for inx in range(self.twSaved.rowCount()):
            value = self.twSaved.item(inx,0).text()
            row = db_selectoneRPC(APP_DATA, value)

            try:
                TOTP_X = pyotp.TOTP(row['secret'])
                URI_TOTP = TOTP_X.provisioning_uri(name=row['account'], issuer_name=row['issuer'])
                __DATA = pyotp.parse_uri(URI_TOTP)
                __DATA_03 = __DATA.now()
            except:
                __DATA_03 = 'ERROR'

            if self.view_secrets == True:
                self.twSaved.setItem(inx, 3, QtWidgets.QTableWidgetItem(__DATA_03))
            else:
                self.twSaved.setItem(inx, 3, QtWidgets.QTableWidgetItem('******'))

            hSaved = self.twSaved.horizontalHeader()
            hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)

    def btnCfgClicked(self):
        self.__msg_error('Global configuration form under construction!')

    def btnDeleteClicked(self):
        index=(self.twSaved.selectionModel().currentIndex())
        value_id = index.sibling(index.row(),0).data()
        __data = { 'id': value_id }

        reply = QMessageBox.question(self, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION), "Do you really want to delete it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_removeRPC(APP_DATA, __data)
            self.twSaved.removeRow(self.twSaved.currentRow())

    def btnUpClicked(self):
        row = self.twSaved.currentRow()
        column = self.twSaved.currentColumn();
        if row > 0:
            if row < self.twSaved.rowCount():
                index_sel = self.twSaved.selectionModel().currentIndex()
                inx_old = self.twSaved.currentRow() -1                          # row table
                id_old = index_sel.sibling(index_sel.row() -1,0).data()         # id
                myorder_old = index_sel.sibling(index_sel.row() -1,1).data()    # myorder

                inx_new = self.twSaved.currentRow()                             # row table
                id_new = index_sel.sibling(index_sel.row(),0).data()            # id
                myorder_new = index_sel.sibling(index_sel.row(),1).data()       # myorder

                value = { 'table': 'auth', 'idold': id_old, 'myorderold': myorder_old, 'idnew': id_new, 'myordernew': myorder_new }

                updown_data(APP_DATA, value)
                self.twSaved.setItem(inx_old, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_new)))
                self.twSaved.setItem(inx_new, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_old)))

            self.twSaved.insertRow(row-1)
            for i in range(self.twSaved.columnCount()):
                self.twSaved.setItem(row-1,i,self.twSaved.takeItem(row+1,i))
                #self.twSaved.setCellWidget(row-1, 2, self.btnCopy())
                self.twSaved.setCurrentCell(row-1,column)
            self.twSaved.removeRow(row+1)

    def btnDownClicked(self):
        row = self.twSaved.currentRow()
        column = self.twSaved.currentColumn();
        if row < self.twSaved.rowCount()-1:
            if row >= 0:
                index_sel = self.twSaved.selectionModel().currentIndex()
                inx_old = self.twSaved.currentRow() +1                          # row table
                id_old = index_sel.sibling(index_sel.row() +1,0).data()         # id
                myorder_old = index_sel.sibling(index_sel.row() +1,1).data()    # myorder

                inx_new = self.twSaved.currentRow()                             # row table
                id_new = index_sel.sibling(index_sel.row(),0).data()            # id
                myorder_new = index_sel.sibling(index_sel.row(),1).data()       # myorder

                value = { 'table': 'auth', 'idold': id_old, 'myorderold': myorder_old, 'idnew': id_new, 'myordernew': myorder_new }

                updown_data(APP_DATA, value)
                self.twSaved.setItem(inx_old, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_new)))
                self.twSaved.setItem(inx_new, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_old)))

            self.twSaved.insertRow(row+2)
            for i in range(self.twSaved.columnCount()):
                self.twSaved.setItem(row+2,i,self.twSaved.takeItem(row,i))
                #self.twSaved.setCellWidget(row+2, 2, self.btnCopy())               
                self.twSaved.setCurrentCell(row+2,column)
            self.twSaved.removeRow(row)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = frmMain()
    app.exec_()