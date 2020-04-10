#!/bin/bash

dir=`dirname $0`

for f in $(basename -s .wav lektion[0-9][0-9].wav); do
  $dir/morsed.py $f.wav | tee ${f}_morsed.txt || exit 1
  if [ $PIPESTATUS[0] != 0 ]; then
    exit 1
  fi
done
