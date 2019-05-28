import os, fnmatch
import logging
import re
from pprint import pprint
import codecs
from itertools import islice

from songshowplus import SongShowPlusImport
from openlyricsxml import OpenLyrics

from pathlib import Path
from lxml import etree
from openlyricsxml import SongXML

'''
BEGIN CONFIGURATION
'''

IMPORT_DIR = '../Songs'
EXPORT_DIR = '../songs_exported'
OUTPUT_MODE = 'text'    # Can be `text` or `xml`

'''
END CONFIGURATION
'''

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)

CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]')
INVALID_FILE_CHARS = re.compile(r'[\\/:\*\?"<>\|\+\[\]%]')
def clean_filename(filename):
    """
    Removes invalid characters from the given ``filename``.

    :param str filename:  The "dirty" file name to clean.
    :return: The cleaned string
    :rtype: str
    """
    return INVALID_FILE_CHARS.sub('_', CONTROL_CHARS.sub('', filename)).strip()

search_dir = Path(IMPORT_DIR)
export_dir = Path(EXPORT_DIR)
file_list = os.listdir(search_dir)
file_list.sort()

pattern = "*.sbsong"
song_list = []
for entry in file_list:  
    if fnmatch.fnmatch(entry, pattern):
            song_list.append(search_dir / entry)


song_store = []
importer = SongShowPlusImport(file_paths=song_list, store=song_store)

importer.do_import()

#pprint(song_store)

# Assert export dir
if not os.path.exists(export_dir):
    os.makedirs(export_dir)

verse_def_map = {
    'v': 'Verse',
    'c': 'Chorus',
    'b': 'Bridge',
    't': 'Tag',
    'o': 'Other',
    'p': 'Pre-Chorus'
}
def compute_verse_name(verse_def):
    prefix = verse_def[0:1]
    suffix = verse_def[1:]

    try:
        verse_type = verse_def_map[prefix]
    except Exception:
        verse_type = verse_def_map['o']

    return '{prefix} {suffix}'.format(prefix=verse_type, suffix=suffix)

def get_value(str, default_value = ''):
    if not str:
        return default_value
    
    return str

def export_songs_txt(song_list):
    logger.debug('started text export')

    sxml = SongXML()

    for song in song_list:
        # Remove text in parens from titles. SongShow doesn't display text in parenthesis,
        # but other apps do, so this should not be present in the export.
        paren_start_idx = song.title.find('(')
        if paren_start_idx > 0:
            song.title = song.title[0:paren_start_idx]

        filename = '{title}'.format(title=song.title)

        if song.authors:
            filename = filename + ' ({author})'.format(author=', '.join([author for author in song.authors]))

        if song.song_book_name:
            filename = '{songbook} - '.format(songbook=song.song_book_name) + filename

        filename = clean_filename(filename)
        
        print('Now exporting song: {filename}'.format(filename=filename))
        # Ensure the filename isn't too long for some filesystems
        path_length = len(str(export_dir))
        filename_with_ext = '{name}.txt'.format(name=filename[0:250 - path_length])
        # Make sure we're not overwriting an existing file
        conflicts = 0
        while (export_dir / filename_with_ext).exists():
            conflicts += 1
            filename_with_ext = '{name}-{extra}.txt'.format(name=filename[0:247 - path_length], extra=conflicts)

        # Compute verse order
        verse_order_list = song.verse_order.split(' ')
        unique_verse_order_list = []
        duplicate_verse_count = 0
        for num, verse_def in enumerate(verse_order_list):
            previous_value = None
            next_value = None

            if verse_def == '':
                continue

            if num > 0:
                previous_value = verse_order_list[num - 1]

            if num < len(verse_order_list) - 1:
                next_value = verse_order_list[num + 1]

            if previous_value and not previous_value.startswith(verse_def):
                duplicate_verse_count = 0

            if (next_value == verse_def) or (previous_value == verse_def):
                suffix = chr(97 + (duplicate_verse_count % 26))
                unique_verse_order_list.append(compute_verse_name(verse_def + suffix))
                duplicate_verse_count += 1
            else:
                unique_verse_order_list.append(compute_verse_name(verse_def))
                duplicate_verse_count = 0
        
        song_file = codecs.open(export_dir / filename_with_ext, "w", "utf-8")
        print('Title: {value}'.format(value=song.title), file=song_file)
        print('Author: {value}'.format(value=', '.join(song.authors)), file=song_file)
        print('Copyright: {value}'.format(value=get_value(song.copyright)), file=song_file)
        print('CCLI: {value}'.format(value=get_value(song.ccli_number)), file=song_file)
        print('Hymnal: {value}'.format(value=get_value(song.song_number)), file=song_file)
        print('Groups: {value}'.format(value=get_value(song.song_book_name, 'None')), file=song_file)

        if len(unique_verse_order_list) > 0:
            print('PlayOrder: {value}'.format(value=', '.join(unique_verse_order_list)), file=song_file)
        
        song_file.write('\n')

        # Print lyrics
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
            print(compute_verse_name(verse_def), file=song_file)

            # Use file.write() here since lyrics already have newlines chars included
            song_file.write(verse[1])
            song_file.write('\n\n')
        
        song_file.close()


def export_songs_xml(song_list):
    logger.debug('started OpenLyricsExport')
    open_lyrics = OpenLyrics()

    for song in song_list:
        xml = open_lyrics.song_to_xml(song)
        tree = etree.ElementTree(etree.fromstring(xml.encode()))

        filename = '{title} ({author})'.format(title=song.title,
                                            author=', '.join([author for author in song.authors]))
        filename = clean_filename(filename)
        
        print('Now exporting song: {filename}'.format(filename=filename))
        # Ensure the filename isn't too long for some filesystems
        path_length = len(str(export_dir))
        filename_with_ext = '{name}.xml'.format(name=filename[0:250 - path_length])
        # Make sure we're not overwriting an existing file
        conflicts = 0
        while (export_dir / filename_with_ext).exists():
            conflicts += 1
            filename_with_ext = '{name}-{extra}.xml'.format(name=filename[0:247 - path_length], extra=conflicts)
        # Pass a file object, because lxml does not cope with some special
        # characters in the path (see lp:757673 and lp:744337).
        with (export_dir / filename_with_ext).open('wb') as out_file:
            tree.write(out_file, encoding='utf-8', xml_declaration=True, pretty_print=True)

        #pprint(xml)

if OUTPUT_MODE == 'xml':
    export_songs_xml(song_store)
else:
    export_songs_txt(song_store)