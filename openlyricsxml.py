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
The :mod:`xml` module provides the XML functionality.

The basic XML for storing the lyrics in the song database looks like this::

    <?xml version="1.0" encoding="UTF-8"?>
    <song version="1.0">
        <lyrics>
            <verse type="c" label="1" lang="en">
                <![CDATA[Chorus optional split 1[---]Chorus optional split 2]]>
            </verse>
        </lyrics>
    </song>


The XML of an `OpenLyrics <http://openlyrics.info/>`_  song looks like this::

    <song xmlns="http://openlyrics.info/namespace/2009/song"
        version="0.7"
        createdIn="OpenLP 1.9.0"
        modifiedIn="ChangingSong 0.0.1"
        modifiedDate="2010-01-28T13:15:30+01:00">
    <properties>
        <titles>
            <title>Amazing Grace</title>
        </titles>
    </properties>
        <lyrics>
            <verse name="v1">
                <lines>
                    <line>Amazing grace how sweet the sound</line>
                </lines>
            </verse>
        </lyrics>
    </song>
"""
import html
import logging
import re

from lxml import etree, objectify

from utils import VerseType


log = logging.getLogger(__name__)

NAMESPACE = 'http://openlyrics.info/namespace/2009/song'
NSMAP = '{{' + NAMESPACE + '}}{tag}'
NEWPAGETAG = '<p style="page-break-after: always;"/>'


class SongXML(object):
    """
    This class builds and parses the XML used to describe songs.
    """
    log.info('SongXML Loaded')

    def __init__(self):
        """
        Set up the default variables.
        """
        self.song_xml = objectify.fromstring('<song version="1.0" />')
        self.lyrics = etree.SubElement(self.song_xml, 'lyrics')

    def add_verse_to_lyrics(self, type, number, content, lang=None):
        """
        Add a verse to the ``<lyrics>`` tag.

        :param type:  A string denoting the type of verse. Possible values are *v*, *c*, *b*, *p*, *i*, *e* and *o*.
            Any other type is **not** allowed, this also includes translated types.
        :param number: An integer denoting the number of the item, for example: verse 1.
        :param content: The actual text of the verse to be stored.
        :param lang:  The verse's language code (ISO-639). This is not required, but should be added if available.
        """
        verse = etree.Element('verse', type=str(type), label=str(number))
        if lang:
            verse.set('lang', lang)
        verse.text = etree.CDATA(content)
        self.lyrics.append(verse)

    def extract_xml(self):
        """
        Extract our newly created XML song.
        """
        return etree.tostring(self.song_xml, encoding='UTF-8', xml_declaration=True)

    def get_verses(self, xml):
        """
        Iterates through the verses in the XML and returns a list of verses and their attributes.

        :param xml: The XML of the song to be parsed.

        The returned list has the following format::

            [[{'type': 'v', 'label': '1'}, u"optional slide split 1[---]optional slide split 2"],
            [{'lang': 'en', 'type': 'c', 'label': '1'}, u"English chorus"]]
        """
        self.song_xml = None
        verse_list = []
        if xml.startswith('<?xml'):
            xml = xml[38:]
        try:
            self.song_xml = objectify.fromstring(xml)
        except etree.XMLSyntaxError:
            log.exception('Invalid xml {text}'.format(text=xml))
        xml_iter = self.song_xml.getiterator()
        for element in xml_iter:
            if element.tag == 'verse':
                if element.text is None:
                    element.text = ''
                verse_list.append([element.attrib, str(element.text)])
        return verse_list

    def dump_xml(self):
        """
        Debugging aid to dump XML so that we can see what we have.
        """
        return etree.dump(self.song_xml)


class OpenLyrics(object):
    """
    This class represents the converter for OpenLyrics XML (version 0.8) to/from a song.

    As OpenLyrics has a rich set of different features, we cannot support them all. The following features are
    supported by the :class:`OpenLyrics` class:

    ``<authors>``
        OpenLP does not support the attribute *lang*.

    ``<chord>``
        This property is fully supported.

    ``<comments>``
        The ``<comments>`` property is fully supported. But comments in lyrics are not supported.

    ``<copyright>``
        This property is fully supported.

    ``<customVersion>``
        This property is not supported.

    ``<key>``
        This property is not supported.

    ``<format>``
        The custom formatting tags are fully supported.

    ``<keywords>``
        This property is not supported.

    ``<lines>``
        The attribute *part* is not supported. The *break* attribute is supported.

    ``<publisher>``
        This property is not supported.

    ``<songbooks>``
        As OpenLP does only support one songbook, we cannot consider more than one songbook.

    ``<tempo>``
        This property is not supported.

    ``<themes>``
        Topics, as they are called in OpenLP, are fully supported, whereby only the topic text (e. g. Grace) is
        considered, but neither the *id* nor *lang*.

    ``<transposition>``
        This property is not supported.

    ``<variant>``
        This property is not supported.

    ``<verse name="v1a" lang="he" translit="en">``
        The attribute *translit* is not supported. Note, the attribute *lang* is considered, but there is not further
        functionality implemented yet. The following verse "types" are supported by OpenLP:

            * v
            * c
            * b
            * p
            * i
            * e
            * o

        The verse "types" stand for *Verse*, *Chorus*, *Bridge*, *Pre-Chorus*, *Intro*, *Ending* and *Other*. Any
        numeric value is allowed after the verse type. The complete verse name in OpenLP always consists of the verse
        type and the verse number. If not number is present *1* is assumed. OpenLP will merge verses which are split
        up by appending a letter to the verse name, such as *v1a*.

    ``<verseOrder>``
        OpenLP supports this property.

    """
    IMPLEMENTED_VERSION = '0.8'
    START_TAGS_REGEX = re.compile(r'\{(\w+)\}')
    END_TAGS_REGEX = re.compile(r'\{\/(\w+)\}')
    VERSE_TAG_SPLITTER = re.compile('([a-zA-Z]+)([0-9]*)([a-zA-Z]?)')

    def song_to_xml(self, song):
        """
        Convert the song to OpenLyrics Format.
        """
        sxml = SongXML()
        song_xml = objectify.fromstring('<song/>')
        # Append the necessary meta data to the song.
        song_xml.set('xmlns', NAMESPACE)
        song_xml.set('version', OpenLyrics.IMPLEMENTED_VERSION)
        application_name = 'SongShowPlus -> OpenLP Converter v1'
        song_xml.set('createdIn', application_name)
        song_xml.set('modifiedIn', application_name)
        # "Convert" 2012-08-27 11:49:15 to 2012-08-27T11:49:15.
        song_xml.set('modifiedDate', str(song.last_modified).replace(' ', 'T'))
        properties = etree.SubElement(song_xml, 'properties')
        titles = etree.SubElement(properties, 'titles')
        self._add_text_to_element('title', titles, song.title)
        if song.alternate_title:
            self._add_text_to_element('title', titles, song.alternate_title)
        if song.comments:
            comments = etree.SubElement(properties, 'comments')
            self._add_text_to_element('comment', comments, song.comments)
        if song.copyright:
            self._add_text_to_element('copyright', properties, song.copyright)
        if song.verse_order:
            self._add_text_to_element(
                'verseOrder', properties, song.verse_order.lower())
        if song.ccli_number:
            self._add_text_to_element('ccliNo', properties, song.ccli_number)
        if song.authors:
            authors = etree.SubElement(properties, 'authors')
            for author in song.authors:
                element = self._add_text_to_element('author', authors, author)
                element.set('type', 'words')
        if song.song_book_name:
            songbooks = etree.SubElement(properties, 'songbooks')
            element = self._add_text_to_element('songbook', songbooks, None, song.song_book_name)
        if song.topics:
            themes = etree.SubElement(properties, 'themes')
            for topic in song.topics:
                self._add_text_to_element('theme', themes, topic)
        # Process the formatting tags.
        # Have we any tags in song lyrics?
        tags_element = None
        match = re.search(r'\{/?\w+\}', song.lyrics)
        if match:
            # Named 'format_' - 'format' is built-in function in Python.
            format_ = etree.SubElement(song_xml, 'format')
            tags_element = etree.SubElement(format_, 'tags')
            tags_element.set('application', 'OpenLP')
        # Process the song's lyrics.
        lyrics = etree.SubElement(song_xml, 'lyrics')
        verse_list = sxml.get_verses(song.lyrics)
        # Add a suffix letter to each verse
        verse_tags = []
        for verse in verse_list:
            verse_tag = verse[0]['type'][0].lower()
            verse_number = verse[0]['label']
            verse_def = verse_tag + verse_number
            # Create the letter from the number of duplicates
            verse[0][u'suffix'] = chr(97 + (verse_tags.count(verse_def) % 26))
            verse_tags.append(verse_def)
        # If the verse tag is a duplicate use the suffix letter
        for verse in verse_list:
            verse_tag = verse[0]['type'][0].lower()
            verse_number = verse[0]['label']
            verse_def = verse_tag + verse_number
            if verse_tags.count(verse_def) > 1:
                verse_def += verse[0]['suffix']
            verse_element = self._add_text_to_element('verse', lyrics, None, verse_def)
            if 'lang' in verse[0]:
                verse_element.set('lang', verse[0]['lang'])
            # Create a list with all "optional" verses.
            optional_verses = html.escape(verse[1])
            optional_verses = optional_verses.split('\n[---]\n')
            start_tags = ''
            end_tags = ''
            """
            for index, optional_verse in enumerate(optional_verses):
                # Fix up missing end and start tags such as {r} or {/r}.
                optional_verse = start_tags + optional_verse
                start_tags, end_tags = self._get_missing_tags(optional_verse)
                optional_verse += end_tags
                # Add formatting tags to text
                lines_element = self._add_text_with_tags_to_lines(verse_element, optional_verse, tags_element)
                # Do not add the break attribute to the last lines element.
                if index < len(optional_verses) - 1:
                    lines_element.set('break', 'optional')
                    """
        xml_text = self._extract_xml(song_xml).decode()
        return self._chordpro_to_openlyrics(xml_text)

    def _chordpro_to_openlyrics(self, text):
        """
        Convert chords from Chord Pro format to Open Lyrics format

        :param text: the lyric with chords
        :return: the lyrics with the converted chords
        """
        # Process chords.
        new_text = re.sub(r'\[(\w.*?)\]', r'<chord name="\1"/>', text)
        return new_text

    def _add_text_to_element(self, tag, parent, text=None, label=None):
        """
        Build an element

        :param tag: A Tag
        :param parent: Its parent
        :param text: Some text to be added
        :param label: And a label
        :return:
        """
        if label:
            element = etree.Element(tag, name=str(label))
        else:
            element = etree.Element(tag)
        if text:
            element.text = str(text)
        parent.append(element)
        return element

    def _extract_xml(self, xml):
        """
        Extract our newly created XML song.

        :param xml: The XML
        """
        return etree.tostring(xml, encoding='UTF-8', xml_declaration=True)

    def _text(self, element):
        """
        This returns the text of an element as unicode string.

        :param element: The element.
        """
        if element.text is not None:
            return str(element.text)
        return ''

    def _process_cclinumber(self, properties, song):
        """
        Adds the CCLI number to the song.

        :param properties: The property object (lxml.objectify.ObjectifiedElement).
        :param song: The song object.
        """
        if hasattr(properties, 'ccliNo'):
            song.ccli_number = self._text(properties.ccliNo)

    def _process_comments(self, properties, song):
        """
        Joins the comments specified in the XML and add it to the song.

        :param properties: The property object (lxml.objectify.ObjectifiedElement).
        :param song: The song object.
        """
        if hasattr(properties, 'comments'):
            comments_list = []
            for comment in properties.comments.comment:
                comment_text = self._text(comment)
                if comment_text:
                    comments_list.append(comment_text)
            song.comments = '\n'.join(comments_list)

    def _process_copyright(self, properties, song):
        """
        Adds the copyright to the song.

        :param properties: The property object (lxml.objectify.ObjectifiedElement).
        :param song: The song object.
        """
        if hasattr(properties, 'copyright'):
            song.copyright = self._text(properties.copyright)

    def _process_titles(self, properties, song):
        """
        Processes the titles specified in the song's XML.

        :param properties: The property object (lxml.objectify.ObjectifiedElement).
        :param song: The song object.
        """
        for title in properties.titles.title:
            if not song.title:
                song.title = self._text(title)
                song.alternate_title = ''
            else:
                song.alternate_title = self._text(title)

    def _dump_xml(self, xml):
        """
        Debugging aid to dump XML so that we can see what we have.
        """
        return etree.tostring(xml, encoding='UTF-8', xml_declaration=True, pretty_print=True)


class OpenLyricsError(Exception):
    # XML tree is missing the lyrics tag
    LyricsError = 1
    # XML tree has no verse tags
    VerseError = 2

    def __init__(self, type, log_message, display_message):
        super(OpenLyricsError, self).__init__()
        self.type = type
        self.log_message = log_message
        self.display_message = display_message
