#!/usr/bin/python3

from PyQt5 import (QtWidgets, QtGui, QtCore, uic)
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox,
                            QDesktopWidget, QInputDialog, QTableWidgetItem, QFileDialog,
                            QSystemTrayIcon, QAction, QStyle, QMenu, qApp,
                            QLineEdit)
from PyQt5.QtCore import (Qt, QUrl, QSize, QFile, QDir, QTimer)
from PyQt5.QtGui import (QPixmap, QIcon, QFont, QPalette, QColor)

import sys
import os
import pyotp
import pyperclip as pc

DIR_APP = '{0}'.format(os.path.dirname(os.path.realpath(__file__)))

from src.database import *
from src.git import *
from src.icons import *
from src.new import *

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

        initial_sqlite(DIR_APP)

        self.CONNECTED = False
        self.CONNECTED_index = -1

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

        self.twSaved = self.findChild(QtWidgets.QTableWidget, 'twSaved')
        self.twSaved.itemSelectionChanged.connect(self.twSavedSelectedClick)
        self.twSaved.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.twSaved.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.twSaved.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.twSaved.verticalHeader().setVisible(False)
        self.twSaved.horizontalHeader().setVisible(False)
        self.twSaved.setIconSize(QSize(44,44))
        self.twSaved.verticalHeader().setDefaultSectionSize(48)

        try:
            rows = sqlite_query(DIR_APP, 'SELECT * FROM auth ORDER BY myorder ASC')
            self.twSaved.clearContents()
            if not debug:
                self.twSaved.setColumnHidden(0, True)
                self.twSaved.setColumnHidden(1, True)
            for row in rows:
                inx = rows.index(row)
                self.twSaved.insertRow(inx)

                ICON_RPC = icon_none(DIR_APP)

                URI_TOTP = pyotp.totp.TOTP(row['secret']).provisioning_uri(name=row['account'], issuer_name=row['issuer'])
                TOTP = pyotp.parse_uri(URI_TOTP)

                btnUpdate = QtWidgets.QPushButton('Update', self)
                btnUpdate.clicked.connect(self.__update)
                #btn.setIcon(icon_up(DIR_APP))
                #btn.setToolTip("Up item selected")

                btnCopy = QtWidgets.QPushButton('Copy', self)
                btnCopy.clicked.connect(self.__copy)
                #btn.setIcon(icon_up(DIR_APP))
                #btn.setToolTip("Up item selected")

                self.twSaved.setItem(inx, 0, QtWidgets.QTableWidgetItem('{0}'.format(row['id'])))
                self.twSaved.setItem(inx, 1, QtWidgets.QTableWidgetItem('{0}'.format(row['myorder'])))
                self.twSaved.setCellWidget(inx, 2, btnUpdate)
                self.twSaved.setCellWidget(inx, 3, btnCopy)
                self.twSaved.setItem(inx, 4, QtWidgets.QTableWidgetItem(TOTP.now()))
                self.twSaved.setItem(inx, 5, QtWidgets.QTableWidgetItem('{0}'.format(row['issuer'])))
                self.twSaved.setItem(inx, 6, QtWidgets.QTableWidgetItem('{0}'.format(row['account'])))

                self.twSaved.selectRow(0)

                hSaved = self.twSaved.horizontalHeader()
                hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
                hSaved.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)
        except:
            pass

        self.btnNew = self.findChild(QtWidgets.QToolButton, 'btnNew')
        self.btnNew.clicked.connect(self.__new)
        self.btnNew.setIcon(icon_plus(DIR_APP))
        self.btnNew.setToolTip("New register 2FA")

        self.btnUp = self.findChild(QtWidgets.QToolButton, 'btnUp')
        self.btnUp.clicked.connect(self.btnUpVulnerabilityClicked)
        self.btnUp.setIcon(icon_up(DIR_APP))
        self.btnUp.setToolTip("Up item selected")

        self.btnDown = self.findChild(QtWidgets.QToolButton, 'btnDown')
        self.btnDown.clicked.connect(self.btnDownVulnerabilityClicked)
        self.btnDown.setIcon(icon_down(DIR_APP))
        self.btnDown.setToolTip("Down item selected")

        self.pbTimeOut = self.findChild(QtWidgets.QProgressBar, 'pbTimeOut')
        self.pbTimeOut.setMinimum(0)
        self.pbTimeOut.setMaximum(30)

        self.step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_func)
        self.timer.start(1000)

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

        width = 661
        height = 504

        self.setWindowIcon(icon_app(DIR_APP))
        self.setWindowTitle('{0} ( {1} )'.format(APP_TITLE, APP_VERSION))

        self.setFixedWidth(width)
        self.setFixedHeight(height)

        self.center()
        self.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint, False)
        #self.__app_hide()
        self.show()

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

    def __new(self):       
        result = frmNew(self, DIR_APP, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION))
        if result.exec_() == QtWidgets.QDialog.Accepted:
            RPC_DATA = result.roiGroups

            row, status = db_insertRPC(DIR_APP, RPC_DATA)

            inx = self.twSaved.rowCount()
            
            self.twSaved.insertRow(inx)

            URI_TOTP = pyotp.totp.TOTP(RPC_DATA['secret']).provisioning_uri(name=RPC_DATA['account'], issuer_name=RPC_DATA['issuer'])
            TOTP = pyotp.parse_uri(URI_TOTP)

            btnUpdate = QtWidgets.QPushButton('Update', self)
            btnUpdate.clicked.connect(self.__update)
            #btn.setIcon(icon_up(DIR_APP))
            #btn.setToolTip("Up item selected")

            btnCopy = QtWidgets.QPushButton('Copy', self)
            btnCopy.clicked.connect(self.__copy)
            #btn.setIcon(icon_up(DIR_APP))
            #btn.setToolTip("Up item selected")

            self.twSaved.setItem(inx, 0, QtWidgets.QTableWidgetItem('{0}'.format(row['id'])))
            self.twSaved.setItem(inx, 1, QtWidgets.QTableWidgetItem('{0}'.format(row['myorder'])))
            self.twSaved.setCellWidget(inx, 2, btnUpdate)
            self.twSaved.setCellWidget(inx, 3, btnCopy)
            self.twSaved.setItem(inx, 4, QtWidgets.QTableWidgetItem(TOTP.now()))
            self.twSaved.setItem(inx, 5, QtWidgets.QTableWidgetItem('{0}'.format(RPC_DATA['issuer'])))
            self.twSaved.setItem(inx, 6, QtWidgets.QTableWidgetItem('{0}'.format(RPC_DATA['account'])))

            self.twSaved.selectRow(inx)

            hSaved = self.twSaved.horizontalHeader()
            hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
            hSaved.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)

    def update_func(self):
        self.step += 1
        self.pbTimeOut.setValue(self.step)
        if self.step >= 30:
            self.pbTimeOut.setValue(0)
            self.step = 0

    def __copy(self):
        index = (self.twSaved.selectionModel().currentIndex())
        value = index.sibling(index.row(),0).data()
        row = db_selectoneRPC(DIR_APP, value)
        URI_TOTP = pyotp.totp.TOTP(row['secret']).provisioning_uri(name=row['account'], issuer_name=row['issuer'])
        TOTP = pyotp.parse_uri(URI_TOTP)
        pc.copy(TOTP.now())
        
    
    def __update(self):
        index = (self.twSaved.selectionModel().currentIndex())
        value = index.sibling(index.row(),0).data()
        
        row = db_selectoneRPC(DIR_APP, value)
        inx = self.twSaved.currentRow()

        __DATA_ID = '{0}'.format(row['id'])
        __DATA_01 = '{0}'.format(row['myorder'])
        
        btnUpdate = QtWidgets.QPushButton('Update', self)
        btnUpdate.clicked.connect(self.__update)
        #btn.setIcon(icon_up(DIR_APP))
        #btn.setToolTip("Up item selected")

        btnCopy = QtWidgets.QPushButton('Copy', self)
        btnCopy.clicked.connect(self.__copy)
        #btn.setIcon(icon_up(DIR_APP))
        #btn.setToolTip("Up item selected")

        URI_TOTP = pyotp.totp.TOTP(row['secret']).provisioning_uri(name=row['account'], issuer_name=row['issuer'])

        __DATA_03 = pyotp.parse_uri(URI_TOTP)
        __DATA_04 = '{0}'.format(row['issuer'])
        __DATA_05 = '{0}'.format(row['account'])

        self.twSaved.setItem(inx, 0, QtWidgets.QTableWidgetItem(__DATA_ID))
        self.twSaved.setItem(inx, 1, QtWidgets.QTableWidgetItem(__DATA_01))
        self.twSaved.setCellWidget(inx, 2, btnUpdate)
        self.twSaved.setCellWidget(inx, 3, btnCopy)
        self.twSaved.setItem(inx, 4, QtWidgets.QTableWidgetItem(__DATA_03.now()))
        self.twSaved.setItem(inx, 5, QtWidgets.QTableWidgetItem(__DATA_04))
        self.twSaved.setItem(inx, 6, QtWidgets.QTableWidgetItem(__DATA_05))

        self.twSaved.selectRow(inx)   

        hSaved = self.twSaved.horizontalHeader()
        hSaved.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        hSaved.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)


    def btnDeleteClicked(self):
        index=(self.twSaved.selectionModel().currentIndex())
        value_id = index.sibling(index.row(),0).data()
        __data = { 'id': value_id }

        reply = QMessageBox.question(self, '{0} ( {1} )'.format(APP_TITLE, APP_VERSION), "Do you really want to delete it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_removeRPC(DIR_APP, __data)
            self.twSaved.removeRow(self.twSaved.currentRow())

    def btnUpVulnerabilityClicked(self):
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

                updown_data(DIR_APP, value)
                self.twSaved.setItem(inx_old, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_new)))
                self.twSaved.setItem(inx_new, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_old)))

            self.twSaved.insertRow(row-1)
            for i in range(self.twSaved.columnCount()):
               self.twSaved.setItem(row-1,i,self.twSaved.takeItem(row+1,i))
               self.twSaved.setCurrentCell(row-1,column)
            self.twSaved.removeRow(row+1)

    def btnDownVulnerabilityClicked(self):
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

                updown_data(DIR_APP, value)
                self.twSaved.setItem(inx_old, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_new)))
                self.twSaved.setItem(inx_new, 1, QtWidgets.QTableWidgetItem('{0}'.format(myorder_old)))

            self.twSaved.insertRow(row+2)
            for i in range(self.twSaved.columnCount()):
               self.twSaved.setItem(row+2,i,self.twSaved.takeItem(row,i))
               self.twSaved.setCurrentCell(row+2,column)
            self.twSaved.removeRow(row)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = frmMain()
    app.exec_()