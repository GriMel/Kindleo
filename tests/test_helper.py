"""
===Description===
Module for testing all modules, except gui_export
-service - to test Lingualeo API for changes
-handler - to test handlers for correct work
-
"""
import unittest
from handler import Base, Kindle, Text, Input
from service import Lingualeo
from collections import Counter
from tests.test_gui import createSqlBase
import sqlite3
import os
import json

def createTxtFile(txt_name):
    """
    Text file with 5 rows
    """
    array = ['even', 'watched', 'nervous', 'guests', 'doing']
    with open(txt_name, 'w') as f:
        for i in array:
            f.write(i+'\n')
    return array


class TestLingualeo(unittest.TestCase):
    """
    Ensure that Lingualeo API is still the same
    """

    EMAIL = "b346059@trbvn.com"
    PASSWORD = "1234567890"
    TEST_WORD_EXISTS = "book"
    TEST_TWORD_EXISTS = "книга"
    TEST_TWORD_EXISTS_TWO = "бронировать"
    TEST_WORD_NON_EXISTS = "zecrvt"

    def setUp(self):
        """
        Authenticate test user
        """
        Lingualeo.PREMIUM = 0
        self.lingualeo = Lingualeo(self.EMAIL, self.PASSWORD)
        self.lingualeo.auth()
        self.maxDiff = None

    def test_typical_get_translation_info(self):
        """
        Function get_translate returns predicted results
        """
        result = self.lingualeo.get_translate(self.TEST_WORD_EXISTS)
        # Dictionary on Lingualeo has 'бронировать' for 'book'
        # The most popular translation, though, is 'книга'
        self.assertEqual(result,
                         {'is_exist': True,
                          'word': "book",
                          'tword': self.TEST_TWORD_EXISTS})
        result = self.lingualeo.get_translate(self.TEST_WORD_NON_EXISTS)
        self.assertEqual(result,
                         {'is_exist': False,
                          'word': "zecrvt",
                          'tword': ""})

    def test_typical_add_word_info(self):
        """
        Function add_word returns predicted results
        """
        response = self.lingualeo.add_word(self.TEST_WORD_EXISTS,
                                           self.TEST_TWORD_EXISTS)
        add_word_info = response.json()['is_new']
        self.assertEqual(0, add_word_info)

    def test_init_info(self):
        """
        Test user has no premium status
        """
        self.lingualeo.initUser()
        self.assertEqual(self.lingualeo.premium, 0)
        self.assertEqual(self.lingualeo.fname, 'b346059')
        self.assertEqual(self.lingualeo.lvl, 1)
        self.assertEqual(self.lingualeo.meatballs, 200)

    def test_enough_meatballs(self):
        """
        Meatballs < words returns False
        """
        self.lingualeo.initUser()
        result = self.lingualeo.isEnoughMeatballs(201)
        self.assertEqual(result, False)

    def test_avatar_exception(self):
        """
        If no avatar - avatar is set to None
        """
        self.lingualeo.TIMEOUT = 0.01
        self.lingualeo.initUser()
        self.assertEqual(self.lingualeo.avatar, None)


class TestKindleHandler(unittest.TestCase):
    """
    Ensure that Kindle handler returns expected result
    """
    TEST_DB = 'test.db'

    def setUp(self):
        """
        Create test database
        """
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        self.handler = Kindle(source=self.TEST_DB)
        self.array = ['tast', 'test', 'tist', 'tost']
        self.new_words = 3
        self.all_words = len(self.array)
        createSqlBase(array=self.array, new=self.new_words)

    def tearDown(self):
        """
        Remove unneeded db
        """
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

    def test_read_not_implemented(self):
        """
        Not overridden read() throws exception
        """
        b = Base(source='')
        with self.assertRaises(NotImplementedError):
            b.read()

    def test_only_new_words(self):
        """
        Reading test Kindle database with 'only_new_words' returns new_words
        """
        self.handler.read(only_new_words=True)
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.new_words)

    def test_all_words(self):
        """
        Reading test Kindle database by default returns self.all_words
        """
        self.handler.read()
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.all_words)


class TestTextHandler(unittest.TestCase):
    """
    Ensure that Text handler returns expected result
    """
    TEST_TXT = 'test.txt'

    def setUp(self):
        """
        Create txt file
        """
        if os.path.exists(self.TEST_TXT):
            os.remove(self.TEST_TXT)
        self.handler = Text(source=self.TEST_TXT)
        self.array = createTxtFile(self.TEST_TXT)
        self.words = len(self.array)

    def tearDown(self):
        """
        Remove test.txt
        """
        if os.path.exists(self.TEST_TXT):
            os.remove(self.TEST_TXT)

    def test_correct_count_of_text_words(self):
        """
        Reading tes.txt returns self.words_count
        """
        self.handler.read()
        words_count = len(self.handler.data)
        self.assertEqual(words_count, self.words)


class TestInputHandler(unittest.TestCase):
    """
    Ensure that Input handler returns expected result
    """
    TEST_WORD = 'test'

    def setUp(self):
        """
        Just for convention
        """
        self.handler = Input(source=self.TEST_WORD)

    def test_correct_word(self):
        """
        Data should have test word in it
        """
        self.handler.read()
        self.assertIn(self.handler.data, self.TEST_WORD)
