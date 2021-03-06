"""
The module with classes to match messages before the parsing step
"""

import re
from abc import ABCMeta, abstractmethod


class Matcher(object):
    """
    Abstract matcher class
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, text):
        """
        Abstract method to match input text.
        :param text: Input text line.
        :return: True if the line matched to the conditions and False if not.
        """


class SubstringMatcher(Matcher):
    """
    Class to match input text line with a substring.
    """

    def __init__(self, substring):
        """
        Matcher constructor.
        :param substring: String to match.
        """
        self.__substring = substring

    def match(self, text):
        return self.__substring in text


class RegexpMatcher(Matcher):
    """
    Class to match input text line with a pattern.
    """

    def __init__(self, pattern):
        """
        Matcher constructor.
        :param pattern: String with a pattern to match.
        """
        self.__pattern = re.compile(pattern)

    def match(self, text):
        return self.__pattern.match(text)
