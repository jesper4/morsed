#!/bin/bash

for f in $(basename -s .wav lektion[0-9][0-9].wav); do
  time ./morsed.py $f.wav | tee ${f}_morsed.txt;
done
