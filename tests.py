import unittest
import logging
import sys
import os
import json
import sqlite3
from PyQt4.QtTest import QTest
from PyQt4 import QtGui, QtCore
from gui_export import MainWindow
from word import *
from service import *
from time import sleep

TEST_DB = 'test.db'
TEST_TXT = 'test.txt'
def leftMouseClick(widget):
    QTest.mouseClick(widget, QtCore.Qt.LeftButton)

def createTxtFile():
    with open(TEST_TXT, 'w') as f:
        f.write('bacon')
        f.write('simple')

def createSqlBase(malformed=False, empty=False, valid=True):
    
    conn = sqlite3.connect('test.db')
    if valid:
        conn.execute("""
            CREATE TABLE WORDS 
            (id TEXT PRIMARY KEY NOT NULL,
                word TEXT, stem TEXT, lang TEXT,
                category INTEGER DEFAULT 0,
                timestamp INTEGER DEFAULT 0,
                profileid TEXT);
             """)
    if valid and not empty:
        conn.execute("""
            INSERT INTO "WORDS"
            VALUES('en:intending',
                   'intending',
                   'intend',
                   'en',
                   0,1450067334997,
                   '')
        """)
    conn.commit()
    if malformed:
        with open(TEST_DB, 'wb') as f:
            f.write(b'tt')




class TestMainWindow(unittest.TestCase):
    
    def setUp(self):
        """
        Turn off logger
        Set english language
        Set credentials from json file
        credentials.json structure:
        {
            "email":"example@gmail.com",
            "password":"123456789"
        }
        """
        logging.disable(logging.CRITICAL)
        with open('credentials.json') as f:
            credentials = json.loads(f.read())
        self.app = QtGui.QApplication([])
        self.ui = MainWindow()
        self.ui.language = 'en'
        self.ui.loadTranslation()
        self.ui.email_edit.setText(credentials['email'])
        self.ui.pass_edit.setText(credentials['password'])

    def tearDown(self):
        """
        Prevent gtk-Critical messages
        Remove test.db in case if it's present
        """
        self.app.deleteLater()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_TXT):
            os.remove(TEST_TXT)

    def test_only_input_checked(self):
        """
        Initial state of GUI: Only input_radio is checked
        """
        self.assertEqual(self.ui.input_radio.isChecked(), True)
        self.assertEqual(self.ui.text_radio.isChecked(), False)
        self.assertEqual(self.ui.kindle_radio.isChecked(), False)

    def test_kindle_radios_disabled(self):
        """
        All_words and new_words should be disabled
        """
        self.assertEqual(self.ui.all_words_radio.isEnabled(), False)
        self.assertEqual(self.ui.new_words_radio.isEnabled(), False)

    def test_kindle_radio_only_one_checked(self):
        """
        Checking new_words should uncheck all_words
        """
        self.ui.kindle_radio.setChecked(True)
        self.ui.new_words_radio.setChecked(True)
        self.assertEqual(self.ui.all_words_radio.isChecked(), False)

    def test_input_validator(self):
        """
        No non-Unicode is allowed in input
        """

        validator = self.ui.input_word_edit.validator()
        text = "work раве"
        state, word, pos = validator.validate(text, 0)
        self.assertEqual(state==QtGui.QValidator.Acceptable, False)

    def test_empty_login_pass(self):
        """
        No email/password is specified - show an error in statusbar.
        """
        self.ui.email_edit.setText("")
        self.ui.pass_edit.setText("")
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Email or password are incorrect")

    def test_dialog_not_run(self):
        """
        Nothing is selected - ExportDialog shouldn't be constructed.
        """
        leftMouseClick(self.ui.export_button)
        with self.assertRaises(AttributeError):
            self.ui.dialog

    def test_input_not_run(self):
        """
        No word in input - show an error in statusbar.
        """
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No input")

    def test_text_no_file_not_run(self):
        """
        If no text file is selected - show an error in statusbar.
        """
        self.ui.text_radio.setChecked(True)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No txt file")

    def test_kindle_no_base_not_run(self):
        """
        No Kindle database is selected - show an error in statusbar.
        """
        self.ui.kindle_radio.setChecked(True)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No Kindle database")

    def test_kindle_wrong_format_not_run(self):
        """
        No '.db' in file extension for Kindle - show an error in statusbar.
        """
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_TXT)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Not database")

    def test_kindle_not_valid_base_not_run(self):
        """
        No WORDS in Kindle table - show an error in statusbar.
        """
        createSqlBase(valid=False)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Not valid database")

    def test_kindle_empty_base_not_run(self):
        """
        Table WORDS in Kindle database is empty - show an error in statusbar
        """
        createSqlBase(empty=True)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Kindle database is empty")

    def test_kindle_malformed_not_run(self):
        """
        Kindle database malformed - show 'Repair' button and an error in statusbar.
        """
        createSqlBase(malformed=True)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.repair_button.isHidden(),False)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Database is malformed. Click 'Repair'")
    '''
    def test_input_run(self):
        """
        If Input is set - construct ExportDialog
        """
        self.ui.input_word_edit.setText("base")
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
            "Input > Lingualeo")
    
    def test_word_run(self):
        """
        If 
        """
        createTxtFile()
        txt = TEST_TXT
        self.ui.text_radio.setChecked(True)
        self.ui.text_path.setText(txt)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
            "Txt > Lingualeo")
    '''
    def test_russian_translation(self):
        """
        Test if russian translation is loaded
        """
        self.ui.language = 'ru'
        self.ui.loadTranslation()
        self.assertEqual(self.ui.export_button.text(), "Экспорт")

#uncomment to run with unittest
'''
if __name__ == "__main__":
    unittest.main()
'''