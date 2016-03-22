#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E731
"""
===Description===
Module for tests

Recommended to run with nosetests as:
nosetests --exe --with-coverage --cover-erase --cover-html
--cover-package=gui_export.py,service.py,handler.py

E731 - use def instead of lambda. To the hell it.
"""

import unittest
import logging
import os
import json
import sqlite3
from PyQt4.QtTest import QTest
from PyQt4 import QtGui, QtCore
from gui_export import MainWindow, ExportDialog, StatisticsDialog,\
                       AboutDialog, NotificationDialog, ExceptionDialog,\
                       Results, AreYouSure
from handler import Kindle
from service import Lingualeo

TEST_DB = 'test.db'
REPAIR_DB = 'test2.db'
TEST_TXT = 'test.txt'
TEST_SRC = 'test.ini'


def leftMouseClick(widget):
    """
    Imitate left click on widget
    """
    QTest.mouseClick(widget, QtCore.Qt.LeftButton)


def createClickTimer(element):
    """
    Create timer for closing widgets
    """
    timer = QtCore.QTimer()
    if type(element) == QtGui.QPushButton:
        action = lambda: leftMouseClick(element)
    else:
        action = element.close
    timer.timeout.connect(action)
    return timer


def createTxtFile(empty=False, array=None):
    """
    Creates test.txt with two words
    """
    if empty:
        open(TEST_TXT, 'a').close()
    else:
        with open(TEST_TXT, 'w') as f:
            if array:
                for i in array:
                    f.write(i+"\n")
            else:
                f.write("test"+"\n")
                f.write("testimony"+"\n")


def createSrcFile(email, password, language=None):
    """
    Creates src.ini with default email and password
    """
    settings = QtCore.QSettings(TEST_SRC, QtCore.QSettings.IniFormat)
    settings.setValue("email", email)
    settings.setValue("password", password)
    if language:
        settings.setValue("language", language)


def createSqlBase(db_name=TEST_DB,
                  malformed=False,
                  valid=True,
                  array=None,
                  new=0):
    """
    Create test SQL base with name test.db
    """
    words_create_command = """
        CREATE TABLE WORDS
        (id TEXT PRIMARY KEY NOT NULL,
            word TEXT,
            stem TEXT,
            lang TEXT,
            category INTEGER DEFAULT 0,
            timestamp INTEGER DEFAULT 0,
            profileid TEXT);
        """
    lookups_create_command = """
        CREATE TABLE LOOKUPS
        (id TEXT PRIMARY KEY NOT NULL,
            word_key TEXT,
            book_key TEXT,
            dict_key TEXT,
            pos TEXT,
            usage TEXT,
            timestamp INTEGER DEFAULT 0);
        """
    words_insert_command = """
        INSERT INTO "WORDS" VALUES
            (:id,
             :word,
             :stem,
             'en',
             :category,
             0,
             '')
        """
    lookups_insert_command = """
        INSERT INTO "LOOKUPS" VALUES
            (:id,
             :word_key,
             'book_key',
             '',
             'pos',
             :usage,
             0)
        """
    if valid:
        with sqlite3.connect(db_name) as conn:
            conn.execute(words_create_command)
            conn.execute(lookups_create_command)
    if valid and array:
        assert new <= len(array)
        new_array = []
        for index, word in enumerate(array):
            row = {}
            #    {
            #     'word_id': "en:doing", 'lookups_id': 'DO',
            #     'word': "doing", 'stem': "do",
            #     'category': 100, 'usage': "He enjoyed doing this"
            #    }
            row['word_id'] = 'en:' + word
            row['lookups_id'] = word[:2].upper()
            row['word'] = word
            row['stem'] = word
            row['category'] = 0 if index < new else 100
            row['usage'] = "Test test " + word
            new_array.append(row)
        with sqlite3.connect(db_name) as conn:
            for row in new_array:
                conn.execute(words_insert_command,
                             {
                              'id': row['word_id'],
                              'word': row['word'],
                              'stem': row['stem'],
                              'category': row['category']
                             })
                conn.execute(lookups_insert_command,
                             {
                              'id': row['lookups_id'],
                              'word_key': row['word_id'],
                              'usage': row['usage']
                             })
    if malformed:
        with open(TEST_DB, 'wb') as f:
            f.write(b'tt')


def createLingualeoUser(premium=False):
    """
    Return test Lingualeo user
    """
    return {"premium_type": +premium,
            "fullname": "Bob Gubko",
            "meatballs": 1500,
            "avatar_mini": 'https://d144fqpiyasmrr'
                           '.cloudfront.net/uploads'
                           '/avatar/0s100.png',
            "xp_level": 34}


class BaseTest(unittest.TestCase):
    """
    Base class for tests
    """

    def setUp(self):
        """
        Construct QApplication
        """
        self.app = QtGui.QApplication([])

    def tearDown(self):
        """
        Prevent gtk-Critical messages.
        Remove app
        """
        self.app.quit()
        self.app.processEvents()
        self.app.sendPostedEvents(self.app, 0)
        self.app.flush()
        self.app.deleteLater()


class TestMainWindow(BaseTest):
    """
    Class for testing MainWindow
    """

    def setUp(self):
        """
        Turn off logger
        Set english language
        Set credentials from json file
        """
        super(TestMainWindow, self).setUp()
        logging.disable(logging.CRITICAL)
        self.ui = MainWindow()
        self.ui.language = 'en'
        self.ui.loadTranslation()
        self.ui.email_edit.setText('b346059@trbvn.com')
        self.ui.pass_edit.setText('1234567890')

    def tearDown(self):
        """
        Prevent gtk-Critical messages
        Remove test.db in case if it's present
        """
        super(TestMainWindow, self).tearDown()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_TXT):
            os.remove(TEST_TXT)
        if os.path.exists(TEST_SRC):
            os.remove(TEST_SRC)
        if os.path.exists(REPAIR_DB):
            os.remove(REPAIR_DB)

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
        self.assertEqual(self.ui.kindle_all_words_radio.isEnabled(), False)
        self.assertEqual(self.ui.kindle_new_words_radio.isEnabled(), False)

    def test_kindle_radio_only_one_checked(self):
        """
        Checking new_words should uncheck all_words
        """
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_new_words_radio.setChecked(True)
        self.assertEqual(self.ui.kindle_all_words_radio.isChecked(), False)

    def test_input_validator(self):
        """
        No non-Unicode is allowed in input
        """

        validator = self.ui.input_word_edit.validator()
        text = "work раве"
        state, word, pos = validator.validate(text, 0)
        self.assertEqual(state == QtGui.QValidator.Acceptable, False)

    def test_empty_login_pass(self):
        """
        No email/password is specified - show an error in statusbar.
        """
        self.ui.email_edit.setText("")
        self.ui.pass_edit.setText("")
        self.ui.input_word_edit.setText("test")
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Email or password are incorrect")

    def test_input_not_run(self):
        """
        No word in input - show an error in statusbar.
        """
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No input")

    def test_text_no_file_not_run(self):
        """
        No text file is selected - show an error in statusbar.
        """
        self.ui.text_radio.setChecked(True)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No txt file")

    def test_text_wrong_format_not_run(self):
        """
        No '.txt' in text extension - show an error in statusbar
        """
        self.ui.text_radio.setChecked(True)
        self.ui.text_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(), "Not txt file")

    def test_text_empty_file_not_run(self):
        """
        Text file empty - show an error in statusbar
        """
        createTxtFile(empty=True)
        self.ui.text_radio.setChecked(True)
        self.ui.text_path.setText(TEST_TXT)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Txt file is empty")

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
        createSqlBase()
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Kindle database is empty")

    def test_kindle_malformed_not_run(self):
        """
        Kindle database malformed - show 'Repair' and error in statusbar.
        """
        array = ['tast', 'test', 'tist']
        createSqlBase(malformed=True, array=array, new=3)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.kindle_repair_button.isHidden(), False)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Database is malformed. Click 'Repair'")

    def test_kindle_repair_tool(self):
        """
        Repaired database is accessable
        New name is set to Kindle's path
        """
        array = ['tast', 'test', 'tist']
        createSqlBase(malformed=True, array=array, new=3)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        timer = createClickTimer(self.ui.notif)
        timer.start(10)
        leftMouseClick(self.ui.kindle_repair_button)
        self.assertIn("Repair was", self.ui.notif.text_label.text())
        self.assertIn(REPAIR_DB, self.ui.kindle_path.text())
        self.assertTrue(self.ui.kindle_repair_button.isHidden())

    def test_kindle_truncate_empty_not_run(self):
        """
        Kindleo refuses to truncate empty Kindle database
        """
        createSqlBase()
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.kindle_truncate_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Kindle database is empty")

    def test_kindle_truncate_tool(self):
        """
        After truncate Kindleo won't let export to start
        """
        array = ['tast', 'test', 'tist', 'tost']
        createSqlBase(array=array, new=1)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        timer_1 = createClickTimer(self.ui.truncate_sure_window.yes_button)
        timer_2 = createClickTimer(self.ui.notif.ok_button)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.kindle_truncate_button)
        leftMouseClick(self.ui.kindle_truncate_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Kindle database is empty")

    def test_lingualeo_no_connection(self):
        """
        No connection - statusbar shows an error
        """
        timeout = Lingualeo.TIMEOUT
        Lingualeo.TIMEOUT = 0.01
        self.ui.input_word_edit.setText("test")
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(), "No connection")
        Lingualeo.TIMEOUT = timeout

    def test_lingualeo_no_meatballs(self):
        """
        No meatballs - statusbar shows an error
        """
        self.ui.input_word_edit.setText("test")
        # we use 200 as zero just for test
        Lingualeo.NO_MEATBALLS = 200
        Lingualeo.PREMIUM = 0
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(), "No meatballs")

    def test_russian_translation(self):
        """
        Selecting RU from Language menu - russian translation is loaded
        """
        lang_item = self.ui.language_menu.actions()[1]
        lang_item.trigger()
        self.assertEqual(self.ui.export_button.text(), "ПОЕХАЛИ!")

    def test_close_event(self):
        """
        On close event triggered 'AreYouSure' appears
        """
        timer = QtCore.QTimer()
        timer.timeout.connect(self.ui.close_window.close)
        timer.start(10)
        self.ui.close()
        self.assertIn("Are you", self.ui.close_window.sure_label.text())
        self.assertFalse(self.ui.close_window.check_item.isChecked())

    def test_load_defaults(self):
        """
        The app loads saved e-mail and password
        """
        self.ui.SRC_FILE = TEST_SRC
        email = "test@gmail.com"
        password = "1234567890"
        createSrcFile(email=email, password=password)
        self.ui.loadDefaults()
        self.assertEqual(email, self.ui.email_edit.text())
        self.assertEqual(password, self.ui.pass_edit.text())

    def test_save_defaults(self):
        """
        The app saves entered email and password to src.ini
        """
        email = "test@gmail.com"
        password = "1234567890"
        self.ui.SRC_FILE = TEST_SRC
        self.ui.email_edit.setText(email)
        self.ui.pass_edit.setText(password)
        self.ui.close()
        self.ui.close_window.check_item.setChecked(True)
        leftMouseClick(self.ui.close_window.yes_button)
        settings = QtCore.QSettings(TEST_SRC, QtCore.QSettings.IniFormat)
        new_email = settings.value("email")
        new_password = settings.value("password")
        self.assertEqual(email, new_email)
        self.assertEqual(password, new_password)

    def test_about_dialog(self):
        """
        About dialog has authors name in it
        """
        about_item = self.ui.help_menu.actions()[0]
        timer = createClickTimer(self.ui.about)
        timer.start(10)
        about_item.trigger()
        self.assertEqual("<a href='mailto:GriefMontana@gmail.com'>Send E-mail</a>",
                         self.ui.about.email_label.text())


class TestExportDialog(TestMainWindow):
    """
    Class for testing ExportDialog
    """

    def setUp(self):
        """
        Set up initial condition:
        -special lingualeo user
        """
        super(TestExportDialog, self).setUp()

    def tearDown(self):
        """
        Prevent gtk-Critical messages.
        Remove test.db and test.txt in case if they're present.
        """
        super(TestExportDialog, self).tearDown()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_TXT):
            os.remove(TEST_TXT)

    def test_export_kindle_premium(self):
        """
        User is premium - count of meatballs is ∞
        """
        array = ['test']
        createSqlBase(array=array, new=0)
        self.ui.kindle_path.setText(TEST_DB)
        self.ui.kindle_radio.setChecked(True)
        Lingualeo.PREMIUM = 1
        timer_1 = createClickTimer(self.ui.dialog)
        timer_2 = createClickTimer(self.ui.dialog.stat_window)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.export_button)
        self.assertEqual("∞", self.ui.dialog.meatballs_value_label.text())

    def test_good_input_export_run(self):
        """
        Word 'test' passed to Input - ExportDialog is shown
        """
        self.ui.input_word_edit.setText('test')
        timer_1 = createClickTimer(self.ui.dialog)
        timer_2 = createClickTimer(self.ui.dialog.stat_window)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.export_button)
        self.assertEqual("1", self.ui.dialog.total_words_value_label.text())

    def test_good_text_export_run(self):
        """
        Valid text file selected - ExportDialog is shown
        """
        duplicates = 2
        array = ['test'] + ['test']*duplicates
        total = len(array)
        prepared = total - duplicates
        createTxtFile(array=array)
        self.ui.text_radio.setChecked(True)
        self.ui.text_path.setText(TEST_TXT)
        timer_1 = createClickTimer(self.ui.dialog)
        timer_2 = createClickTimer(self.ui.dialog.stat_window)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(str(total),
                         self.ui.dialog.total_words_value_label.text())
        self.assertEqual(str(prepared),
                         self.ui.dialog.prepared_words_value_label.text())
        self.assertEqual(str(duplicates),
                         self.ui.dialog.duplicate_words_value_label.text())

    def test_good_kindle_all_words_export_run(self):
        """
        Valid Kindle + all words - ExportDialog shows all words
        """
        new = 3
        duplicates = 0
        array = ['tast', 'test', 'tist', 'tost']
        total = len(array)
        createSqlBase(array=array, new=new)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        timer_1 = createClickTimer(self.ui.dialog)
        timer_2 = createClickTimer(self.ui.dialog.stat_window)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(str(total),
                         self.ui.dialog.total_words_value_label.text())
        self.assertEqual(str(duplicates),
                         self.ui.dialog.duplicate_words_value_label.text())
        self.assertEqual(str(total),
                         self.ui.dialog.prepared_words_value_label.text())

    def test_good_kindle_only_new_words_export_run(self):
        """
        Valid Kindle + only new words - ExportDialog shows only new words
        """
        new = 3
        duplicates = 0
        array = ['tast', 'test', 'tist', 'tost']
        createSqlBase(array=array, new=new)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_new_words_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        timer_1 = createClickTimer(self.ui.dialog)
        timer_2 = createClickTimer(self.ui.dialog.stat_window)
        timer_1.start(10)
        timer_2.start(12)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(str(new),
                         self.ui.dialog.total_words_value_label.text())
        self.assertEqual(str(duplicates),
                         self.ui.dialog.duplicate_words_value_label.text())
        self.assertEqual(str(new),
                         self.ui.dialog.prepared_words_value_label.text())


class TestStatisticsDialog(BaseTest, Results):
    """
    Class for testing StatisticsDialog
    """

    def setUp(self):
        """
        Set up initial condition:
        -prepared list of dictionaries with results
        """
        self.array = []
        row = {}
        words = ["cat", "dog", "cockatoo", "smile"]
        contexts = ["I have a cat.",
                    "I have a dog.",
                    "",
                    "Let's smile."
                    ]
        translations = ["кот", "cобака", "какаду", "улыбка"]
        results = sorted(self.RESULTS.values())
        for index, (word, tword, context)\
                in enumerate(zip(words, translations, contexts)):
            row = {
                   "word": word,
                   "result": results[index],
                   "tword": tword,
                   "context": context
                }
            self.array.append(row)
        super(TestStatisticsDialog, self).setUp()
        self.stat_dialog = StatisticsDialog()
        self.stat_dialog.setVariables(self.array)

    def test_correct_counts(self):
        """
        Every label has its own count of words
        Total = 4
        Not added = 1
        Added = 1
        No translation = 1
        Exist = 1
        """
        self.assertEqual('4', self.stat_dialog.values[0].text())
        self.assertEqual('1', self.stat_dialog.values[1].text())
        self.assertEqual('1', self.stat_dialog.values[2].text())
        self.assertEqual('1', self.stat_dialog.values[3].text())
        self.assertEqual('1', self.stat_dialog.values[4].text())

    def test_correct_table_colors(self):
        """
        Every row in table has its own color
        1) added - green.
        2) exists - red.
        3) no translation - yellow.
        4) not added - white.
        """
        self.assertEqual(self.stat_dialog.table.item(0, 0).backgroundColor(),
                         QtCore.Qt.green)
        self.assertEqual(self.stat_dialog.table.item(1, 0).backgroundColor(),
                         QtCore.Qt.red)
        self.assertEqual(self.stat_dialog.table.item(2, 0).backgroundColor(),
                         QtCore.Qt.yellow)
        self.assertEqual(self.stat_dialog.table.item(3, 0).backgroundColor(),
                         QtCore.Qt.white)

    def test_correct_table_row_counts(self):
        """
        Table has four rows
        """
        self.assertEqual(self.stat_dialog.table.rowCount(), 4)


class TestAboutDialog(BaseTest):
    """
    Class for testing 'About' dialog.
    """
    JSON_FILE = os.path.join("src", "data", "data.json")

    def setUp(self):
        """
        Set up initial condition:
        -prepared json file
        -version, author, idea, email loaded
        """
        super(TestAboutDialog, self).setUp()
        with open(self.JSON_FILE) as f:
            data_info = json.loads(f.read())
        self.version = data_info['version']
        self.author = data_info['author']
        self.idea = data_info['idea']
        self.email = data_info['e-mail']
        self.about = AboutDialog()

    def tearDown(self):

        super(TestAboutDialog, self).tearDown()

    def test_version_present(self):
        """
        Data in json == data in 'About'
        """
        text = self.about.about_label.text()
        version_text = self.about.version_label.text()
        email_text = self.about.email_label.text()
        self.assertIn(self.author, text)
        self.assertIn(self.idea, text)
        self.assertIn(self.email, email_text)
        self.assertIn(self.version, version_text)


class TestNotificationDialog(BaseTest):
    """
    Class to test notifications
    """

    def setUp(self):
        """
        Prepare title and text for notification
        """
        super(TestNotificationDialog, self).setUp()
        self.title = "Warning!"
        self.text = "Something happened"
        self.ui = NotificationDialog()
        self.ui.setVariables(title=self.title, text=self.text)

    def test_correct_title_and_text(self):
        """
        Texts passed to constructor should be correct in GUI
        """
        self.assertEqual(self.ui.windowTitle(), self.title)
        self.assertEqual(self.ui.text_label.text(), self.text)

if __name__ == "__main__":
    unittest.main()
