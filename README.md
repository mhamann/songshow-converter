# SongShow Plus (SSP) exporter

## Background
SongShow Plus (SSP) is a presentation tool designed for churches that want to run their visuals from a single pane of glass. While it was a good solution over a decade ago, it has largely failed to keep up with modern software architecture, user experience, and performance needs.

Unfortunately, SSP stores its song / lyric files in a binary format that most competing products can't read natively. At worst, this results in a bit of vendor lock-in. At best, you'll have to manually re-create your song database in an alternative product.

Fortunately, OpenLP _does_ support importing songs from SongShow, so often the recommendation is to import into OpenLP and then export into the OpenSong XML format. I tried this method, but found numerous issues when songs contained certain characters or weren't totally "clean" from a data perspective (e.g. textual copy/paste issues, etc). OpenLP tended to crash during the import phase.


## Overview
This project uses the underlying import code from OpenLP, but adds some additional logic to (hopefully) ensure a clean, error-free process. Any read/parse failures won't halt the entire procedure, but will instead log the failure and move on to the next song.

Output is available either in OpenLP's native OpenSong XML format or in a plain-text format based largely on MediaShout 6.x.

The code first reads a specified directory of `.sbsong` files into memory. It then dumps all of the songs into a second directory into whichever output format was specified (`.xml` or `.txt`).

From there, it's hopefully just a matter of importing the resulting files into the target application of your choosing.

This flow was tested on Mac with a set of ~1,900 SongShow Plus files and the resulting output was imported into Faithlife Proclaim in one batch with zero errors.

The code is a bit "thrown together," since I needed it for a very specific and time-sensitive project, but given the sample size, it should be fairly robust for anyone else who needs a similar ability.

Please open an issue if you find a bug. I can't promise I'll have time to fix it, but at least it'll be documented. :-)

### Requirements / dependencies
- Python 3.x (I used 3.7.0)

## Usage
- Clone this repo to your local machine
- Extract your SongShow Plus database into a folder somewhere 
    (SongShow stores its files on disk somewhere - usually `C:\Users\Public\Public Documents\R-Technics\SongShow Plus\Songs`, so it's just a matter of copying them around to the right place. I recommend you work with a copy just in case.)
- Create a folder where you want the exported files to be stored
- Edit the section in `song_converter.py` marked **BEGIN CONFIGURATION** as follows:
  - Set `IMPORT_DIR` to the path where your SongShow files are stored.
  - Set `EXPORT_DIR` to the path where the converted files should be created.
  - Set `OUTPUT_MODE` to either `text` or `xml` depending on which format you need.

- Now, just run the script from a terminal like this:
    ```
    python ./song_converter.py
    ```

    You should see some output that looks similar to this:
    ```
    Now importing: ../Songs/via dolorosa.sbsong
    Now importing: ../Songs/we wish you a merry christmas.sbsong
    Now importing: ../Songs/what a friend we have in jesus & give me jesus.sbsong
    Now importing: ../Songs/what do we want for our children.sbsong

    Now exporting song: Via Dolorosa
    Now exporting song: We Wish You a Merry Christmas
    Now exporting song: What a Friend We Have in Jesus & Give Me Jesus
    Now exporting song: What do we want for our children (Bette Sloat_Ruth Anderson)
    ```

That's it!

Depending on the size of your song database and the speed of your computer, it may take a few minutes to complete the process. When done, you should have a much more useful database of songs that you can easily import into other church media sofware. (By the way, [Faithlife's Proclaim](https://proclaim.faithlife.com/) is pretty awesome, so check it out if you haven't already!)

Hope this is useful to someone who had the same issue that I did.