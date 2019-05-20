import os, fnmatch
import logging
from pprint import pprint

from songshowplus import SongShowPlusImport
from openlyricsxml import OpenLyrics

from pathlib import Path
from lxml import etree

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)

search_dir = './Songs'
file_list = os.listdir('./Songs')
file_list.sort()

pattern = "*.sbsong"
song_list = []
for entry in file_list:  
    if fnmatch.fnmatch(entry, pattern):
            song_list.append(Path(search_dir + '/' + entry))


song_store = []
importer = SongShowPlusImport(file_paths=song_list, store=song_store)

importer.do_import()

pprint(song_store)

logger.debug('started OpenLyricsExport')
open_lyrics = OpenLyrics()

for song in song_store:
    xml = open_lyrics.song_to_xml(song)
    tree = etree.ElementTree(etree.fromstring(xml.encode()))

    pprint(xml)
