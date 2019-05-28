# -*- coding: utf-8 -*-
# vim: autoindent shiftwidth=4 expandtab textwidth=120 tabstop=4 softtabstop=4

##########################################################################
# OpenLP - Open Source Lyrics Projection                                 #
# ---------------------------------------------------------------------- #
# Copyright (c) 2008-2019 OpenLP Developers                              #
# ---------------------------------------------------------------------- #
# This program is free software: you can redistribute it and/or modify   #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
# (at your option) any later version.                                    #
#                                                                        #
# This program is distributed in the hope that it will be useful,        #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <https://www.gnu.org/licenses/>. #
##########################################################################

import re
from datetime import datetime
from pprint import pprint

class VerseType(object):
    """
    VerseType provides an enumeration for the tags that may be associated with verses in songs.
    """
    Verse = 0
    Chorus = 1
    Bridge = 2
    PreChorus = 3
    Intro = 4
    Ending = 5
    Other = 6

    names = ['Verse', 'Chorus', 'Bridge', 'Pre-Chorus', 'Intro', 'Ending', 'Other']
    tags = [name[0].lower() for name in names]

CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]')
REPLACMENT_CHARS_MAP = str.maketrans({'\u2018': '\'', '\u2019': '\'', '\u201c': '"', '\u201d': '"', '\u2026': '...',
                                      '\u2013': '-', '\u2014': '-', '\v': '\n\n', '\f': '\n\n'})
NEW_LINE_REGEX = re.compile(r' ?(\r\n?|\n) ?')
WHITESPACE_REGEX = re.compile(r'[ \t]+')

def normalize_str(irregular_string):
    """
    Normalize the supplied string. Remove unicode control chars and tidy up white space.

    :param str irregular_string: The string to normalize.
    :return: The normalized string
    :rtype: str
    """
    irregular_string = irregular_string.translate(REPLACMENT_CHARS_MAP)
    irregular_string = CONTROL_CHARS.sub('', irregular_string)
    irregular_string = NEW_LINE_REGEX.sub('\n', irregular_string)
    return WHITESPACE_REGEX.sub(' ', irregular_string)

class Song():
    title = ''
    alternate_title = ''
    search_title = ''
    search_lyrics = ''
    verse_order = ''
    song_number = ''
    lyrics = ''
    copyright = ''
    comments = ''
    theme_name = ''
    ccli_number = ''
    authors = []
    topics = []
    song_book_name = ''

    last_modified = str(datetime.now())

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()