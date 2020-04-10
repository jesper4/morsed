#!/bin/bash

for i in {01..50}; do
  wget http://tomth.se/sk4sq/cwkurs/lektion$i.mp3 || exit 1
done
