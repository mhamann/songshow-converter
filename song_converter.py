import os, fnmatch
from pprint import pprint

from songshowplus import SongShowPlusImport

from pathlib import Path

search_dir = './Songs'
file_list = os.listdir('./Songs')
file_list.sort()

pattern = "*.sbsong"
song_list = []
for entry in file_list:  
    if fnmatch.fnmatch(entry, pattern):
            song_list.append(Path(search_dir + '/' + entry))



importer = SongShowPlusImport(file_paths=song_list)

importer.do_import()