# !/usr/bin/env python
"""
Usage: python gui_export.py

===GUI version of lingualeo.export===
"""

import sys
import os
import sqlite3
import time
from PyQt4 import QtCore, QtGui
from requests.exceptions import ConnectionError as NoConnection, Timeout

from collections import Counter
from word import Kindle, Text
from service import Lingualeo
'''
from pydub import AudioSegment
from pydub.playback import play
'''

# CONSTANTS
DEFAULT_NAME = "src.ini"
TESTS_NAME = "tests/"
MAIN_ICO = os.path.join("src", "pics", "lingualeo.ico")
EXPORT_ICO = os.path.join("src", "pics", "export.ico")
STAT_ICO = os.path.join("src", "pics", "statistics.ico")
EXIT_ICO = os.path.join("src", "pics", "exit.ico")
WARN_ICO = os.path.join("src", "pics", "warning.ico")
WARN_ICO = "warning.ico"


def centerUI(self):
    """place UI in the middle of the screen"""
    qr = self.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())


def playSound(name):
    pass


class AreYouSure(QtGui.QDialog):
    """exit dialog"""
    saved = QtCore.pyqtSignal()

    def __init__(self):
        super(AreYouSure, self).__init__()
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        layout = QtGui.QVBoxLayout()
        hor_lay = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel()
        self.check_item = QtGui.QCheckBox()
        self.yes_button = QtGui.QPushButton()
        self.no_button = QtGui.QPushButton()
        hor_lay.addWidget(self.yes_button)
        hor_lay.addWidget(self.no_button)
        layout.addWidget(self.check_item)
        layout.addWidget(self.label)
        layout.addLayout(hor_lay)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowTitle("Exit")
        self.setWindowIcon(QtGui.QIcon(EXIT_ICO))
        self.label.setText("Are you sure to quit?")
        self.yes_button.setText("Yes")
        self.no_button.setText("No")
        self.check_item.setText("Save e-mail/password")

    def exit(self):
        """handle correct exit"""
        if self.check_item.isChecked():
            self.saved.emit()
        QtGui.QApplication.quit()

    def initActions(self):
        self.yes_button.clicked.connect(self.exit)
        self.no_button.clicked.connect(self.close)


class NotificationDialog(QtGui.QDialog):
    """dialog for notifications - 'Connection Lost' etc"""

    def __init__(self, text):
        super(NotificationDialog, self).__init__()
        self.text = text
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel()
        self.ok_button = QtGui.QPushButton()
        layout.addWidget(self.label)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowIcon(QtGui.QIcon(WARN_ICO))
        self.label.setText(self.text)
        self.ok_button.setText("OK")

    def initActions(self):
        self.ok_button.clicked.connect(self.close)


class MainWindow(QtGui.QMainWindow):
    """main window"""

    def __init__(self, source='input'):
        super(MainWindow, self).__init__()
        self.source = source
        self.file_name = None
        self.table = None
        self.initUI()
        self.setSizeUI()
        self.retranslateUI()
        centerUI(self)
        self.checkState()
        self.initActions()
        self.loadDefaults()

    def initUI(self):
        self.main_widget = QtGui.QWidget(self)
        self.main_layout = QtGui.QVBoxLayout()
        self.auth_layout = QtGui.QGridLayout()
        self.auth_label = QtGui.QLabel()
        self.email_label = QtGui.QLabel()
        self.email_edit = QtGui.QLineEdit()
        self.email_edit.setObjectName('email')
        self.pass_label = QtGui.QLabel()
        self.pass_edit = QtGui.QLineEdit()
        self.pass_edit.setObjectName('pass')
        self.auth_layout.addWidget(self.email_label, 0, 0, 1, 1)
        self.auth_layout.addWidget(self.email_edit, 0, 1, 1, 1)
        self.auth_layout.addWidget(self.pass_label, 1, 0, 1, 1)
        self.auth_layout.addWidget(self.pass_edit, 1, 1, 1, 1)

        self.main_label = QtGui.QLabel()

        self.input_radio = QtGui.QRadioButton()
        self.input_radio.setChecked(True)
        self.input_word_label = QtGui.QLabel()
        self.input_context_label = QtGui.QLabel()
        self.input_word_edit = QtGui.QLineEdit()
        self.input_context_edit = QtGui.QLineEdit()
        self.input_layout = QtGui.QGridLayout()
        self.input_layout.addWidget(self.input_word_label, 0, 0, 1, 1)
        self.input_layout.addWidget(self.input_word_edit, 0, 1, 1, 1)
        self.input_layout.addWidget(self.input_context_label, 1, 0, 1, 1)
        self.input_layout.addWidget(self.input_context_edit, 1, 1, 1, 1)
        self.text_radio = QtGui.QRadioButton()
        self.text_push = QtGui.QPushButton()
        self.text_path = QtGui.QLineEdit()
        self.text_path.setReadOnly(True)
        self.text_layout = QtGui.QHBoxLayout()
        self.text_layout.addWidget(self.text_push)
        self.text_layout.addWidget(self.text_path)

        self.kindle_radio = QtGui.QRadioButton()
        self.kindle_push = QtGui.QPushButton()
        self.kindle_path = QtGui.QLineEdit()
        self.kindle_path.setReadOnly(True)
        self.kindle_layout = QtGui.QHBoxLayout()
        self.kindle_layout.addWidget(self.kindle_push)
        self.kindle_layout.addWidget(self.kindle_path)

        self.export_push = QtGui.QPushButton()
        self.truncate_push = QtGui.QPushButton()
        self.bottom_layout = QtGui.QHBoxLayout()
        self.bottom_layout.addWidget(self.export_push)
        self.bottom_layout.addWidget(self.truncate_push)

        self.main_layout.addLayout(self.auth_layout)
        self.main_layout.addWidget(self.main_label)
        self.main_layout.addWidget(self.input_radio)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.text_radio)
        self.main_layout.addLayout(self.text_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.kindle_radio)
        self.main_layout.addLayout(self.kindle_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.bottom_layout)
        self.status_bar = QtGui.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    def setSizeUI(self):
        """prevents growing edit field"""
        self.input_word_edit.setFixedHeight(
            self.input_word_edit.sizeHint().height()
            )

    def retranslateUI(self):
        self.setWindowTitle(self.tr("Export to Lingualeo"))
        self.setWindowIcon(QtGui.QIcon(MAIN_ICO))
        self.email_label.setText("e-mail")
        self.pass_label.setText('password')
        self.main_label.setText(self.tr("<center>Choose the source</center>"))
        self.input_radio.setText(self.tr("Input"))
        self.input_word_label.setText(self.tr("word"))
        self.input_context_label.setText(self.tr("context"))

        self.text_radio.setText(self.tr("Text"))
        self.text_push.setText(self.tr("Path"))

        self.kindle_radio.setText(self.tr("Kindle"))
        self.kindle_push.setText(self.tr("Path"))

        self.export_push.setText(self.tr("Export"))
        self.truncate_push.setText(self.tr("Truncate"))

    def checkState(self):
        input_state = self.input_radio.isChecked()
        text = self.text_radio.isChecked()
        kindle = self.kindle_radio.isChecked()

        self.input_word_edit.setEnabled(input_state)
        self.input_context_edit.setEnabled(input_state)
        self.input_word_label.setEnabled(input_state)
        self.input_context_label.setEnabled(input_state)
        self.text_push.setEnabled(text)
        self.text_path.setEnabled(text)
        self.kindle_push.setEnabled(kindle)
        self.kindle_path.setEnabled(kindle)

    def TextWrongFile(self):
        """handler for text file"""
        _, ext = os.path.splitext(self.file_name)
        if ext != '.txt':
            return True

    def kindleEmpty(self):
        """handler for empty kindle database"""
        database = sqlite3.connect(self.file_name)
        cursor = database.cursor()
        data = cursor.execute("SELECT * FROM WORDS").fetchall()
        return len(data) == 0

    def kindleWrongDatabase(self):
        _, ext = os.path.splitext(self.file_name)
        if ext != ".db":
            return True
        conn = sqlite3.connect(self.file_name)
        try:
            conn.execute("SELECT * FROM WORDS")
            return False
        except Exception:
            return True

    def getSource(self):
        source = self.sender().text().lower()
        if 'kindle' not in source:
            self.truncate_push.setEnabled(False)
        else:
            self.truncate_push.setEnabled(True)
        self.source = source
        self.checkState()

    def clearMessage(self):
        self.status_bar.showMessage("")

    def export(self):
        """kidle/input/word"""
        kindle = self.kindle_radio.isChecked()
        text = self.text_radio.isChecked()
        email = self.email_edit.text().strip(" ")
        password = self.pass_edit.text().strip(" ")
        lingualeo = Lingualeo(email, password)

        try:
            lingualeo.auth()
        # Handle no internet connection/no site connection
        except (NoConnection, Timeout):
            self.status_bar.showMessage(self.tr("No connection"))
            return
        # Handle wrong email/password
        except KeyError:
            self.status_bar.showMessage(self.tr("Email or password is incorrect"))
            return

        if kindle:
            self.file_name = self.kindle_path.text()
            # Handle empty Kindle path
            if not self.kindle_path.text():
                self.status_bar.showMessage(self.tr("No file"))
                return

            # Handle not valid given file
            if self.kindleWrongDatabase():
                self.status_bar.showMessage(self.tr("Not valid database"))
                return

            # Handle empty database
            if self.kindleEmpty():
                self.status_bar.showMessage(self.tr("Base is empty"))
                return
            # Handle 0 meatballs
            if lingualeo.meatballs == 0:
                self.status_bar.showMessage(self.tr("No meatballs"))
                return
            self.status_bar.showMessage(self.tr("Kindle > Lingualeo"))
            handler = Kindle(self.file_name)
            handler.read()
            self.table = handler.get()

        elif text:
            self.file_name = self.text_path.text()
            if self.TextWrongFile():
                self.status_bar.showMessage(self.tr("Not txt file"))
                return
            self.status_bar.showMessage(self.tr("Txt > Lingualeo"))
            self.file_name = self.text_path.text()
            handler = Text(self.file_name)
            handler.read()
            self.table = handler.get()
        else:
            self.status_bar.showMessage(self.tr("Input > Lingualeo"))
            word = self.input_word_edit.text().lower()
            context = self.input_context_edit.text()
            if not word:
                self.status_bar.showMessage(self.tr("No word"))
                return
            self.table = [{'word': word, 'context': context}]

        dialog = ExportDialog(self.table, lingualeo)
        dialog.closed.connect(self.clearMessage)
        dialog.exec_()

    def truncate(self):
        """truncate kindle database"""
        self.file_name = self.kindle_path.text()
        if self.kindleEmpty():
            self.status_bar.showMessage(self.tr("File is empty"))
            return
        reply = QtGui.QMessageBox.question(
                    self, 'Message', 'Are you sure to truncate?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            conn = sqlite3.connect(self.file_name)
            with conn:
                conn.execute("DELETE FROM WORDS;")
                conn.execute("DELETE FROM LOOKUPS;")
                conn.execute("UPDATE METADATA SET sscnt = 0\
                                WHERE id in ('WORDS', 'LOOKUPS');")
                conn.commit()
            self.status_bar.showMessage("Kindle database is empty")
        else:
            return

    def setPath(self):

        name = QtGui.QFileDialog.getOpenFileName(self, "Select File", "",)
        if self.kindle_radio.isChecked():
            self.kindle_path.setText(name)
        else:
            self.text_path.setText(name)

    def changeEditWidth(self):
        if 'email' in self.sender().objectName():
            width_e = self.email_edit.fontMetrics().boundingRect(
                self.email_edit.text()).width() + 10
            self.email_edit.setMinimumWidth(width_e)
        else:
            width_p = self.pass_edit.fontMetrics().boundingRect(
                self.pass_edit.text()).width() + 10
            self.pass_edit.setMinimumWidth(width_p)

    def initActions(self):
        self.input_radio.clicked.connect(self.getSource)
        self.text_radio.clicked.connect(self.getSource)
        self.kindle_radio.clicked.connect(self.getSource)
        self.export_push.clicked.connect(self.export)
        self.truncate_push.clicked.connect(self.truncate)
        self.kindle_push.clicked.connect(self.setPath)
        self.text_push.clicked.connect(self.setPath)
        self.email_edit.textChanged.connect(self.changeEditWidth)
        self.pass_edit.textChanged.connect(self.changeEditWidth)

    def closeEvent(self, event):
        a = AreYouSure()
        a.saved.connect(self.saveDefaults)
        a.exec_()
        event.ignore()

    def saveDefaults(self):
        '''save default email and password'''
        self.settings = QtCore.QSettings(
            DEFAULT_NAME, QtCore.QSettings.IniFormat
            )
        self.settings.setValue("email", self.email_edit.text())
        self.settings.setValue("password", self.pass_edit.text())

    def loadDefaults(self):
        '''load default email and password'''
        try:
            self.settings = QtCore.QSettings(
                "src.ini", QtCore.QSettings.IniFormat
                )
            email = self.settings.value("email")
            password = self.settings.value("password")
            self.email_edit.setText(email)
            self.pass_edit.setText(password)
        except Exception:
            pass


class WorkThread(QtCore.QThread):

    punched = QtCore.pyqtSignal(dict)

    def __init__(self, lingualeo):
        super(WorkThread, self).__init__()
        self.lingualeo = lingualeo

    def __del__(self):
        self.wait()

    def run(self):
        result = None
        row = None
        data = None
        for index, i in enumerate(self.table):
            try:
                word = i.get('word').lower()
                context = i.get('context', '')
                response = self.lingualeo.get_translate(word)
                translate = response['tword']
                exist = response['is_exist']
                if exist:
                    result = 'exist'
                else:
                    if translate == 'no translation':
                        result = "no translation"
                        row = {"word": word,
                               "result": result,
                               "tword": translate}
                    else:
                        result = "new"
                        self.lingualeo.add_word(word,
                                                translate,
                                                context)
                row = {"word": word,
                       "result": result,
                       "tword": translate}
                data = {"sent": True,
                        "row": row,
                        "index": index+1}
            except (NoConnection, Timeout):
                data = {"sent": False,
                        "row": None,
                        "index": None}
            finally:
                self.punched.emit(data)
            time.sleep(0.1)

    def stop(self):
        self.terminate()

    def getData(self, table, index=0):
        self.table = table[index:]


class ExportDialog(QtGui.QDialog):

    closed = QtCore.pyqtSignal()

    def __init__(self, table, lingualeo):

        super(ExportDialog, self).__init__()
        self.table = table
        self.stat = list()
        self.value = 0
        self.task = WorkThread(lingualeo)
        self.task.getData(table)
        self.length = len(self.table)
        self.lingualeo = lingualeo
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):

        self.setWindowIcon(QtGui.QIcon(EXPORT_ICO))
        layout = QtGui.QVBoxLayout()

        info_layout = QtGui.QVBoxLayout()
        self.avatar_label = QtGui.QLabel()
        self.fname_label = QtGui.QLabel()
        self.lvl_label = QtGui.QLabel()
        self.meatballs_label = QtGui.QLabel()

        info_layout.addWidget(self.avatar_label)
        info_layout.addWidget(self.fname_label)
        info_layout.addWidget(self.lvl_label)
        info_layout.addWidget(self.meatballs_label)

        warning_layout = QtGui.QHBoxLayout()
        self.warning_info_label = QtGui.QLabel()
        warning_layout.addWidget(self.warning_info_label)

        progress_layout = QtGui.QVBoxLayout()
        hor_layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel()
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0, self.length)
        self.startButton = QtGui.QPushButton()
        self.breakButton = QtGui.QPushButton()

        progress_layout.addWidget(self.label)
        progress_layout.addWidget(self.progressBar)
        hor_layout.addWidget(self.startButton)
        hor_layout.addWidget(self.breakButton)
        progress_layout.addLayout(hor_layout)

        layout.addLayout(info_layout)
        layout.addLayout(warning_layout)
        layout.addLayout(progress_layout)

        self.setLayout(layout)
        self.breakButton.hide()

    def retranslateUI(self):

        self.setWindowIcon(QtGui.QIcon(EXPORT_ICO))
        avatar = QtGui.QPixmap()
        avatar.loadFromData(self.lingualeo.avatar)
        self.avatar_label.setPixmap(avatar)
        self.avatar_label.setScaledContents(True)

        fname = "Name: {}".format(self.lingualeo.fname)
        self.fname_label.setText(fname)

        lvl = "Lvl: {}".format(self.lingualeo.lvl)
        self.lvl_label.setText(lvl)

        meatballs = "Meatballs: {}".format(self.lingualeo.meatballs)
        self.meatballs_label.setText(meatballs)

        if self.lingualeo.meatballs < self.length:
            self.warning_info_label.setText("WARNING: Meatballs < Words")
            self.warning_info_label.setStyleSheet("color:red")
        self.setWindowTitle(self.tr("Preparing to export"))
        self.startButton.setText(self.tr("Start"))
        self.breakButton.setText(self.tr("Break"))

    def initActions(self):
        self.startButton.clicked.connect(self.changeTask)
        self.breakButton.clicked.connect(self.task.stop)
        self.breakButton.clicked.connect(self.close)
        self.task.punched.connect(self.onProgress)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.task.stop()
            self.close()

    def closeEvent(self, event):
        event.accept()
        self.task.stop()
        s = StatisticsWindow(self.stat)
        s.exec_()
        self.closed.emit()

    def changeTask(self):
        if self.sender().text() == "Start":
            self.startButton.setText(self.tr("Stop"))
            self.breakButton.show()
            self.setWindowTitle(self.tr("Processing..."))
            if self.value > 0:
                self.task.getData(self.table, self.value)
            self.task.start()
        else:
            self.task.stop()
            self.startButton.setText(self.tr("Start"))
            self.breakButton.hide()

    def finish(self):
        self.label.setText(self.tr("Finished"))
        self.breakButton.setText(self.tr("Close"))
        self.startButton.hide()

    def onProgress(self, data):

        if data['sent']:
            row = data['row']
            if row['result'] != 'exist':
                self.lingualeo.substractMeatballs()
                meatballs = "Meatballs: {}".format(
                                self.lingualeo.meatballs
                                )
                self.meatballs_label.setText(meatballs)
        else:
            self.startButton.click()
            #playSound(os.path.join("src", "sounds", "warning.mp3"))
            warning = NotificationDialog(self.tr("No Internet Connection"))
            warning.exec_()
            return

        self.stat.append(data['row'])
        self.value += 1
        self.label.setText("{} words processed out of {}".format(self.value,
                                                                 self.length))
        # initial value of progressBar is -1
        self.progressBar.setValue(self.value)
        if self.lingualeo.meatballs == 0:
            self.task.stop()
            self.progressBar.setValue(self.progressBar.maximum())
            self.warning_info_label.setText(
                self.tr("No meatballs. Upload stopd")
                )
            self.finish()
            for i in self.table[self.value:]:
                self.stat.append({"word": i['word'],
                                  "result": "not added",
                                  "tword": ""})
            return

        if (self.progressBar.value() == self.progressBar.maximum()):
            self.finish()


class StatisticsWindow(QtGui.QDialog):

    def __init__(self, stat):
        super(QtGui.QDialog, self).__init__()
        self.stat = stat
        self.initUI()
        self.retranslateUI()

    def initUI(self):

        self.list_view = QtGui.QListWidget()
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(2)
        for item in self.stat:
            if item.get("result") == "new":
                brush = QtCore.Qt.green
            elif item.get("result") == "no translation":
                brush = QtCore.Qt.darkYellow
            elif item.get("result") == "not added":
                brush = QtCore.Qt.white
            else:
                brush = QtCore.Qt.red
            word = QtGui.QTableWidgetItem(item.get("word"))
            translate = QtGui.QTableWidgetItem(item.get("tword"))
            word.setBackground(brush)
            translate.setBackgroundColor(brush)
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, word)
            self.table.setItem(row_position, 1, translate)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        # self.table.resizeColumnsToContents()
        total = len(self.stat)
        result = Counter(i["result"] for i in self.stat)
        added = result["new"]
        not_added = result["not added"]
        wrong = result["no translation"]
        exist = len(self.stat) - (added+not_added) - wrong

        self.label = QtGui.QLabel("""
            <center>Total: {}<br>
             Added: {}<br>
             Not added: {}<br>
             No translation: {}<br>
             Exist: {}</center>
            """.format(total, added, not_added, wrong, exist))
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def retranslateUI(self):
        self.setWindowTitle(self.tr("Statistics"))


def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
