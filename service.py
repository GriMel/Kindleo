#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from operator import itemgetter
from collections import Counter


class Lingualeo(object):
    """Lingualeo.com API class"""

    TIMEOUT = 5
    LOGIN = "http://api.lingualeo.com/api/login"
    ADD_WORD = "http://api.lingualeo.com/addword"
    ADD_WORD_MULTI = "http://api.lingualeo.com/addwords"
    GET_TRANSLATE = "http://api.lingualeo.com/gettranslates?word="

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.initUser()

    def initUser(self):
        self.cookies = None
        self.premium = None
        self.meatballs = None
        self.avatar = None
        self.fname = None
        self.lvl = None

    def auth(self):
        """authorization on lingualeo.com"""
        url = self.LOGIN
        values = {
            "email": self.email,
            "password": self.password
        }
        r = requests.get(url, values, timeout=self.TIMEOUT)
        self.cookies = r.cookies
        content = r.json()['user']
        self.premium = bool(content['premium_type'])
        if not self.premium:
            self.meatballs = content['meatballs']
        else:
            self.meatballs = "Unlimited"
        self.fname = content['fullname']
        self.avatar = requests.get(content['avatar_mini']).content
        self.lvl = content['xp_level']

    def get_translate(self, word):
        """get translation from lingualeo's API"""
        url = self.GET_TRANSLATE + word
        try:
            response = requests.get(url,
                                    cookies=self.cookies,
                                    timeout=self.TIMEOUT)
            translate_list = response.json()['translate']
            translate_list = sorted(translate_list,
                                    key=itemgetter('votes'),
                                    reverse=True)
            translate = translate_list[0]
            tword = translate['value']
            is_exist = bool(translate['is_user'])
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
                    "tword": "no translation"}

    def add_word(self, word, tword, context=""):
        """add new word"""
        url = self.ADD_WORD
        values = {
            "word": word,
            "tword": tword,
            "context": context
        }
        requests.post(url, values, cookies=self.cookies, timeout=self.TIMEOUT)

    def add_word_multiple(self, array):
        """add the array of words"""
        url = self.ADD_WORD_MULTI
        data = dict()
        for index, i in enumerate(array):
            data["words["+index+"][word]"] = array['word']
            data["words["+index+"][tword]"] = array['tword']
            data["words["+index+"][context]"] = array['context']

        requests.post(url, data, cookies=self.cookies)

    def isPremium(self):
        """tells if user has a premium status"""
        return self.premium

    def substractMeatballs(self):
        """method for substracting meatballs"""
        self.meatballs -= 1
