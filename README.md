# morsed
Re-codes morse code in an audio file

It makes it possible to leave non-morse parts untouched (typically
an instructor voice in a morse course), but will replace the detected
morse code. The replacement morse code will be played back according
to the settings provided to the script:

 * Word speed
 * Character speed
 * Symbol speed
 * Tone frequency
 * Tone amplitude

It is so far limited to handle only a few lessons of the [morse course
by SK4SQ](http://www.sk4sq.net/cwkurs.shtm).

Lessons 1-50, except for 35 and 36, are expected to be handle nicely,
with only a few exceptions.

## How to re-code the SK4SQ course

Download the course. This can be done automatically by the included
helper script:

```bash
./download_lessons.sh
```

It will download episodes 1-50.

The morsed.py script can only read .wav files, so the downloaded
.mp3 files need to be converted to .wav files first. There is another
helper script which uses the lame program for the conversion:

```bash
./mp3_to_wav.sh
```

And finally, the conversion can be done by using another helper script:

```bash
./morsed_all.sh
```

This will leave the original files untouched, but create two new
files for each episode:

```
lektion01_out.wav
lektion01.stdout
```

The first file is the resulting audo file and the second one
is a file containing the decoded text.

## Re-coding an individual audio file
Use the morsed.py script and provide the input .wav file to it.
Use the --help option to the script to find the available options
and arguments to be used with the script.

## Pre-requisites
The script uses a few different python libraries, which might
therefore need to be installed before running the script.
These libraries are however commonly available in the
various Linux package systems.

```
numpy
matplotlib
pandas
scipy
```

The helper scripts also use some common tools:

```
wget
lame
```
