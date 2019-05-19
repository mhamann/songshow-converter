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
"""
The :mod:`songshowplus` module provides the functionality for importing SongShow Plus songs into the OpenLP
database.
"""
import logging
import re
import struct

from songimport import SongImport


TITLE = 1
AUTHOR = 2
COPYRIGHT = 3
CCLI_NO = 5
VERSE = 12
CHORUS = 20
BRIDGE = 24
TOPIC = 29
COMMENTS = 30
VERSE_ORDER = 31
SONG_BOOK = 35
SONG_NUMBER = 36
CUSTOM_VERSE = 37

log = logging.getLogger(__name__)


class SongShowPlusImport(SongImport):
    """
    The :class:`SongShowPlusImport` class provides the ability to import song files from SongShow Plus.

    **SongShow Plus Song File Format:**

    The SongShow Plus song file format is as follows:

    * Each piece of data in the song file has some information that precedes it.
    * The general format of this data is as follows:
        | 4 Bytes, forming a 32 bit number, a key if you will, this describes what the data is (see blockKey below)
        | 4 Bytes, forming a 32 bit number, which is the number of bytes until the next block starts
        | 1 Byte, which tells how many bytes follows
        | 1 or 4 Bytes, describes how long the string is, if its 1 byte, the string is less than 255
        | The next bytes are the actual data.
        | The next block of data follows on.

        This description does differ for verses. Which includes extra bytes stating the verse type or number. In some
        cases a "custom" verse is used, in that case, this block will in include 2 strings, with the associated string
        length descriptors. The first string is the name of the verse, the second is the verse content.

        The file is ended with four null bytes.

        Valid extensions for a SongShow Plus song file are:

        * .sbsong
    """

    other_count = 0
    other_list = {}
    import_source = []

    def __init__(self, **kwargs):
        """
        Initialise the SongShow Plus importer.
        """
        super(SongShowPlusImport, self).__init__(**kwargs)

    def do_import(self):
        """
        Receive a single file or a list of files to import.
        """
        if not isinstance(self.import_source, list):
            log.debug('import_source is not an instance of <list>')
            return
        for file_path in self.import_source:

            self.ssp_verse_order_list = []
            self.other_count = 0
            self.other_list = {}

            print('Now importing: ' + str(file_path))

            with file_path.open('rb') as song_file:
                while True:
                    block_key, = struct.unpack("I", song_file.read(4))
                    log.debug('block_key: %d' % block_key)
                    # The file ends with 4 NULL's
                    if block_key == 0:
                        break
                    next_block_starts, = struct.unpack("I", song_file.read(4))
                    next_block_starts += song_file.tell()
                    if block_key in (VERSE, CHORUS, BRIDGE):
                        null, verse_no, = struct.unpack("BB", song_file.read(2))
                    elif block_key == CUSTOM_VERSE:
                        null, verse_name_length, = struct.unpack("BB", song_file.read(2))
                        verse_name = self.decode(song_file.read(verse_name_length))
                    length_descriptor_size, = struct.unpack("B", song_file.read(1))
                    log.debug('length_descriptor_size: %d' % length_descriptor_size)
                    # In the case of song_numbers the number is in the data from the
                    # current position to the next block starts
                    if block_key == SONG_NUMBER:
                        sn_bytes = song_file.read(length_descriptor_size - 1)
                        self.song_number = int.from_bytes(sn_bytes, byteorder='little')
                        continue
                    # Detect if/how long the length descriptor is
                    if length_descriptor_size == 12 or length_descriptor_size == 20:
                        length_descriptor, = struct.unpack("I", song_file.read(4))
                    elif length_descriptor_size == 2:
                        length_descriptor = 1
                    elif length_descriptor_size == 9:
                        length_descriptor = 0
                    else:
                        length_descriptor, = struct.unpack("B", song_file.read(1))
                    log.debug('length_descriptor: %d' % length_descriptor)
                    data = song_file.read(length_descriptor)
                    log.debug(data)
                    if block_key == TITLE:
                        self.title = self.decode(data)
                    elif block_key == AUTHOR:
                        authors = self.decode(data).split(" / ")
                        for author in authors:
                            if author.find(",") != -1:
                                author_parts = author.split(", ")
                                try:
                                    author = author_parts[1] + " " + author_parts[0]
                                except Exception:
                                    author = author_parts[0]
                            self.parse_author(author)
                    elif block_key == COPYRIGHT:
                        self.add_copyright(self.decode(data))
                    elif block_key == CCLI_NO:
                        # Try to get the CCLI number even if the field contains additional text
                        match = re.search(r'\d+', self.decode(data))
                        if match:
                            self.ccli_number = int(match.group())
                        else:
                            log.warning("Can't parse CCLI Number from string: {text}".format(text=self.decode(data)))
                    elif block_key == VERSE:
                        self.add_verse(self.decode(data), "{tag}{number}".format(tag='v',
                                                                                 number=verse_no))
                    elif block_key == CHORUS:
                        self.add_verse(self.decode(data), "{tag}{number}".format(tag='c',
                                                                                 number=verse_no))
                    elif block_key == BRIDGE:
                        self.add_verse(self.decode(data), "{tag}{number}".format(tag='b',
                                                                                 number=verse_no))
                    elif block_key == TOPIC:
                        self.topics.append(self.decode(data))
                    elif block_key == COMMENTS:
                        self.comments = self.decode(data)
                    elif block_key == VERSE_ORDER:
                        verse_tag = self.to_openlp_verse_tag(self.decode(data), True)
                        if verse_tag:
                            if not isinstance(verse_tag, str):
                                verse_tag = self.decode(verse_tag)
                            self.ssp_verse_order_list.append(verse_tag)
                    elif block_key == SONG_BOOK:
                        self.song_book_name = self.decode(data)
                    elif block_key == CUSTOM_VERSE:
                        verse_tag = self.to_openlp_verse_tag(verse_name)
                        self.add_verse(self.decode(data), verse_tag)
                    else:
                        log.debug("Unrecognised blockKey: {key}, data: {data}".format(key=block_key, data=data))
                        song_file.seek(next_block_starts)
                self.verse_order_list = self.ssp_verse_order_list
                if not self.finish():
                    self.log_error(file_path)

    def to_openlp_verse_tag(self, verse_name, ignore_unique=False):
        """
        Handle OpenLP verse tags

        :param verse_name: The verse name
        :param ignore_unique: Ignore if unique
        :return: The verse tags and verse number concatenated
        """
        # Have we got any digits? If so, verse number is everything from the digits to the end (OpenLP does not have
        # concept of part verses, so just ignore any non integers on the end (including floats))
        match = re.match(r'(\D*)(\d+)', verse_name)
        if match:
            verse_type = match.group(1).strip()
            verse_number = match.group(2)
        else:
            # otherwise we assume number 1 and take the whole prefix as the verse tag
            verse_type = verse_name
            verse_number = '1'
        verse_type = verse_type.lower()
        if verse_type == "verse":
            verse_tag = 'v'
        elif verse_type == "chorus":
            verse_tag = 'c'
        elif verse_type == "bridge":
            verse_tag = 'b'
        elif verse_type == "pre-chorus":
            verse_tag = 'p'
        else:
            if verse_name not in self.other_list:
                if ignore_unique:
                    return None
                self.other_count += 1
                self.other_list[verse_name] = str(self.other_count)
            verse_tag = 'o'
            verse_number = self.other_list[verse_name]
        return verse_tag + verse_number

    def decode(self, data):
        try:
            # Don't question this, it works...
            return data.decode('utf-8').encode('cp1251').decode('cp1251')
        except Exception:
            return data.decode('utf-8')
