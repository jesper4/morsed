for f in $(basename -s .mp3 lektion[0-9][0-9].mp3); do lame --decode $f.mp3; done
