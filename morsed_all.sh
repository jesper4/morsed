#!/bin/bash

for f in $(basename -s .wav lektion[0-9][0-9].wav); do time PYTHONIOENCODING=iso-8859-1 ~/git/morsed/morsed.py $f.wav | tee $f.stdout; done
