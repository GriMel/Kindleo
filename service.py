#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===Description===
Module for configuring Lingualeo API
"""

import requests
from requests.exceptions import ConnectionError as NoConnection, Timeout
from operator import itemgetter
from collections import Counter


class Lingualeo(object):
    """Lingualeo.com API class"""
    TIMEOUT = 5
    LOGIN = "http://api.lingualeo.com/api/login"
    ADD_WORD = "http://api.lingualeo.com/addword"
    ADD_WORD_MULTI = "http://api.lingualeo.com/addwords"
    GET_TRANSLATE = "http://api.lingualeo.com/gettranslates?word="
    # added for test purposes
    NO_MEATBALLS = 0
    PREMIUM = 0

    def __init__(self, email, password):
        """
        Initializing API.
        Given email and password.
        All info about user - None.
        """
        self.email = email
        self.password = password
        self.auth_info = None
        self.cookies = None
        self.premium = None
        self.meatballs = None
        self.avatar = None
        self.fname = None
        self.lvl = None

    def initUser(self):
        """
        Retrieve information about user
        from server's response.
        """
        self.premium = self.auth_info['premium_type'] or self.PREMIUM
        self.fname = self.auth_info['fullname']
        self.lvl = self.auth_info['xp_level']
        if not self.premium:
            self.meatballs = self.auth_info['meatballs']
        else:
            self.meatballs = "∞"
        try:
            self.avatar = requests.get(self.auth_info['avatar_mini'],
                                       timeout=self.TIMEOUT).content
        except (NoConnection, Timeout):
            self.avatar = None

    def auth(self):
        """
        Authorization on lingualeo.com with given email/pass.
        """
        url = self.LOGIN
        values = {
            "email": self.email,
            "password": self.password
        }
        r = requests.get(url, values, timeout=self.TIMEOUT)
        self.cookies = r.cookies
        self.auth_info = r.json()['user']

    def get_translate(self, word):
        """
        Get translation from lingualeo's API
        """
        url = self.GET_TRANSLATE + word
        try:
            response = requests.get(url,
                                    cookies=self.cookies,
                                    timeout=self.TIMEOUT)
            translate_list = response.json()['translate']
            # sort by votes
            translate_list = sorted(translate_list,
                                    key=itemgetter('votes'),
                                    reverse=True)
            # and pick the most voted word
            translate = translate_list[0]
            tword = translate['value']
            is_exist = bool(translate['is_user'])
            # @TEMP
            # The main idea is to check if another
            # translation is already present in
            # Lingualeo dictionary
            # For example if top-voted translation
            # for word book is = 'книга'
            # and we have book-'бронировать' in our dictionary
            # For now in this case I don't add 'книга'
            if not is_exist:
                counter = Counter(i['is_user'] for i in translate_list)
                if counter.get(1, 0) > 0:
                    is_exist = True
            return {
                "is_exist": is_exist,
                "word": word,
                "tword": tword
            }
        except (IndexError, KeyError):
            return {"is_exist": False,
                    "word": word,
                    "tword": ""}

    def add_word(self, word, tword, context=""):
        """
        Add new word to Lingualeo vocabulary
        """
        url = self.ADD_WORD
        values = {
            "word": word,
            "tword": tword,
            "context": context
        }
        return requests.post(url,
                             values,
                             cookies=self.cookies,
                             timeout=self.TIMEOUT)

    # def add_word_multiple(self, array):
    #     """
    #     Add the array of words to Lingualeo vocabulary.
    #    """
    #     url = self.ADD_WORD_MULTI
    #     data = dict()
    #     for index, i in enumerate(array):
    #         data["words["+index+"][word]"] = i['word']
    #         data["words["+index+"][tword]"] = i['tword']
    #         data["words["+index+"][context]"] = i['context']
    #
    #     return requests.post(url,
    #                          data,
    #                          cookies=self.cookies)

    def isEnoughMeatballs(self, words):
        """
        Check if meatballs > words
        """
        if not self.premium and self.meatballs < words:
            return False
        else:
            return True
