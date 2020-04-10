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
