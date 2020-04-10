#!/usr/bin/env -S python3 -u


# morsed - Re-codes morse code in an audio file
# Copyright (C) 2020 Jesper Dahlberg
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.io.wavfile import read, write
import re
import argparse

def main():
  args = get_args()
  convert_file(args)

def get_args():
  parser = argparse.ArgumentParser(description='Re-codes morse code in a .wav file')
  parser.add_argument('file', nargs=1)

  parser.add_argument('--attack', type=float, nargs='?', default=0.008,
    help='Time in seconds for ramping up and down the transmission')
  parser.add_argument('--frequency', type=int, nargs='?', default=700,
                      help='Transmission frequency in Hz')
  parser.add_argument('--speed', type=int, nargs='?',
    help='Overrides the --speed_char/sym/word options [cpm/PARIS]')
  parser.add_argument('--speed_char', type=int, nargs='?', default=18)
  parser.add_argument('--speed_sym', type=int, nargs='?', default=100)
  parser.add_argument('--speed_word', type=int, nargs='?', default=18,
    help='Controls word spacing as if --speed_char/sym would have used the same setting')
  parser.add_argument('--volume', type=float, nargs='?', default=0.6,
    help='Volume of transmitted tone in the range [0-1]')
  args = parser.parse_args()
  if args.speed:
    args.speed_sym = args.speed_char = args.speed_word = args.speed
  if not 0 <= args.volume <= 1:
    print('Volume need to be in range zero to one')
    exit(1)

  return args

def convert_file(args):
  file = args.file[0]
  file_out = file.replace(".wav", "_out.wav")
  if file_out == file:
    print("The file need to be a .wav file")
    exit(1)

  print('Will re-code with symbol speed ' + str(args.speed_sym) +
        ', character speed ' + str(args.speed_char) +
        ', word speed ' + str(args.speed_word))

  print('Reading file ' + file)
  sample, content, Fs = read_wav(file)

  print_content(content)

  print('Writing file ' + file_out)
  timing = calc_full_timing(Fs, args.speed_sym, args.speed_char, args.speed_word)
  f = args.frequency
  tone = {"freq": args.frequency,
          "attack": args.attack,
          "release": args.attack,
          "volume": args.volume}
  sender = {"timing": timing, "tone": tone}
  write_wav(file_out, Fs, f, content, sample, sender)

def read_wav(file):
  Fs, data = read(file)
  sample = data
#  print('len(data)=' + str(len(data)))
#  sample = data[58955375 - 100000:]
#  sample = data[100000:10000000]
#  sample = data[100000:500000]
#  sample = data[290000:315000]
#  sample = data[10000:10100]
#  sample = data[5000000:10000000]
#  sample = data[0:5000000]
#  sample = data[0:500000]
#  sample = data[0:50000]
#  print(sample)
#  plot([sample])
  sample_abs = np.absolute(sample)
  write('sample.wav', Fs, sample)
  N = 20
#  conv = np.convolve(sample_abs, np.ones((N,))/N, mode='same')
  # Really large chunks of data seems to crash the rolling max calculation,
  # so split it in smaller parts
  M = 1000000
  offset = 0
  sample_max = [0] * (N - 1)
  while offset < len(sample_abs):
    start = offset
    end = offset + M
    if end >= len(sample_abs):
      end = len(sample_abs)
    sample_max += pd.Series(sample_abs[start:end]).rolling(N).max().dropna().tolist()
    offset += M - (N - 1)
  sample_bin = [1 if int(x) > 10000 else 0 for x in sample_max]
  points = trigger(sample_bin, N)
  content = decode(points)
#  print(content)
  return sample, content, Fs

def write_wav(file, Fs, f, content, sample, sender):
  out = []
#  for part in content:
  for i in range(len(content)):
    part = content[i]
    if part['type'] == 'other':
      point = part['point']
      start = point[0]
      end = point[1]
      stuff = sample[start:end].tolist()
      fade_len = 0.005
      if i + 1 < len(content) and content[i + 1]['type'] == 'str':
        stuff = fade_out(stuff, Fs, fade_len)
      if i > 0 and content[i - 1]['type'] == 'str':
        stuff = fade_in(stuff, Fs, fade_len)
      out += list(stuff)
    elif part['type'] == 'str':
      stuff = gen_morse_str(Fs, f, sender, part['str'])
      out += stuff

  out = np.asarray(out, dtype=np.int16)
#  plot([out])
  write(file, Fs, out)

def fade_out(samples, Fs, t_release):
  len_release = int(t_release * Fs)
  if len_release > len(samples):
    len_release = len(samples)
  release = np.linspace(1, 0, len_release)
  len_hold = len(samples) - len_release
  if len_hold < 0:
    len_hold = 0
  hold = np.linspace(1, 1, len_hold)
  envelope = np.concatenate([hold, release])
  result = samples * envelope
  return result

def fade_in(samples, Fs, t_attack):
  len_attack = int(t_attack * Fs)
  if len_attack > len(samples):
    len_attack = len(samples)
  attack = np.linspace(0, 1, len_attack)
  len_hold = len(samples) - len_attack
  if len_hold < 0:
    len_hold = 0
  hold = np.linspace(1, 1, len_hold)
  envelope = np.concatenate([attack, hold])
  result = samples * envelope
  return result

def gen_morse_str(Fs, f, sender, str):
  out = []
  chars = split_str(str)
  for i in range(0, len(chars)):
    c = chars[i]
    out += gen_morse_c(Fs, f, sender, c)
    if i < len(chars) - 1 and chars[i] != ' ' and chars[i + 1] != ' ':
      out += gen_morse_c(Fs, f, sender, '')
  return out

def split_str(str):
  list = []
  while len(str) > 0:
    if str[0] != '<':
      list.append(str[0])
      str = str[1:]
    else:
      head, tail = re.match("(<.*?>)(.*)", str).groups()
      list.append(head)
      str = tail
  return list

def gen_morse_c(Fs, f, sender, c):
  out = []
  if c == ' ':
    out += gen_word_spc(sender["timing"])
  elif c == '':
    out += gen_char_spc(sender["timing"])
  else:
    sym = letter_to_sym(c)
    out += gen_morse_syms(Fs, f, sender, sym)
  return out

def gen_word_spc(timing):
  out = int(timing['word_spc']) * [0]
  return out

def gen_char_spc(timing):
  out = int(timing['char_spc']) * [0]
  return out

def gen_sym_spc(timing):
  out = int(timing['sym_spc']) * [0]
  return out

def gen_longsym_spc(timing):
  out = int(timing['longsym_spc']) * [0]
  return out

def gen_morse_syms(Fs, f, sender, sym):
  out = []
  first = 1
  timing = sender["timing"]
  for s in sym:
    if not first and s in ".-":
      out += gen_sym_spc(timing)

    if s == '.':
      out += gen_tone(Fs, f, timing['dit'], sender["tone"])
    elif s == '-':
      out += gen_tone(Fs, f, timing['dah'], sender["tone"])
    elif s == '>':
      out += gen_longsym_spc(timing)
    first = 0
  return out

def gen_tone(Fs, f, l, tone):
  T = l / Fs
  t = np.linspace(0, T, int(l))
  a = tone["volume"] * np.iinfo(np.int16).max
  w = 2 * np.pi * f
  sig = a * np.sin(w * t)

  len_attack = int(Fs * tone["attack"])
  len_release = int(Fs * tone["release"])
  attack = np.linspace(0, 1, len_attack)
  release = np.linspace(1, 0, len_release)
  hold = np.linspace(1, 1, len(sig) - len_attack - len_release)
  envelope = np.concatenate([attack, hold, release])
  sig *= envelope

  return sig.tolist()

def calc_full_timing(fs, sym_rate, char_rate, word_rate):
  sym_timing = calc_timing(fs, sym_rate)
  char_timing = calc_timing(fs, char_rate)
  word_timing = calc_timing(fs, word_rate)
  timing = {"dit": sym_timing["dit"],
            "dah": sym_timing["dah"],
            "sym_spc": sym_timing["sym_spc"],
            "char_spc": char_timing["char_spc"],
            "word_spc": word_timing["word_spc"],
            "longsym_spc": sym_timing["char_spc"]}
  return timing

def calc_timing(fs, rate):
  ts = 1 / fs
  wpm = rate / 5 # Paris
  sym_units_per_minute = wpm * 50
  sym_unit = 60 / sym_units_per_minute
  smpl_sym_unit = sym_unit / ts
  smpl_dit = 1 * smpl_sym_unit
  smpl_dah = 3 * smpl_sym_unit
  smpl_sym_spc = 1 * smpl_sym_unit
  smpl_char_spc = 3 * sym_unit / ts
  smpl_word_spc = 7 * sym_unit / ts
  return {"dit": smpl_dit,
          "dah": smpl_dah,
          "sym_spc": smpl_sym_spc,
          "char_spc": smpl_char_spc,
          "word_spc": smpl_word_spc}

def trigger(data, N, start_val = 0, start_index = 0):
  prev_val = start_val
  prev_index = start_index
  points = []
  index = 0
  stats = {}
  for sample in data:
    if sample != prev_val:
      new_index = start_index + index
      length = new_index - prev_index
      if prev_val == 0:
        length += N
      else:
        length -= N
      dd = ditdah(length, prev_val)
      if dd not in stats:
        stats[dd] = []
      stats[dd].append(length)
      if dd in ('other', 'sym', 'longsym', '', ' ') and len(points) > 0 and points[-1][3] == 'other':
        prev = points[-1]
        points[-1] = (prev[0], new_index, prev[2] + length, prev[3], prev_val)
      else:
        points.append((prev_index, new_index, length, dd, prev_val))
      prev_val = sample
      prev_index = new_index
    index += 1
  if index - 1 != prev_index:
    points.append((prev_index, start_index + index - 1, -1, 'other', prev_val))
#  print_sym_stats(stats)
  return points

def print_sym_stats(stats):
#  for dd in stats:
#    print(dd)
  print(stats)
#  plot([stats['.'], stats['-']])
  plot([stats[''], stats[' ']])
  pass
    
def plot(list):
  plt.figure()
  for data in list:
    plt.plot(data)
  plt.xlabel('Sample index')
  plt.ylabel('Amplitude')
  plt.title('Waveform')
  plt.show()

def ditdah(length, sample):
  deviation = 0.2
  sym_unit = 1420 # Avsn 15
  sym_unit = 1520 # Avsn 25
  len_dit = sym_unit
  len_dah = 3 * sym_unit
  len_sym = sym_unit
  len_longsym = 3 * sym_unit # Should it really be like this??

  char_unit = 80 / 30 * sym_unit
  len_char = 3 * char_unit
  len_char = 25450 # Don't understand where they get this from
  len_word = 7 * char_unit
  len_word = 52400 # Don't understand where they get this from
  if sample == 1:
    if around(len_dit, deviation, length):
      return '.'
    elif around(len_dah, deviation, length):
      return '-'
  else:
    if around(len_sym, deviation, length):
      return 'sym'
    elif around(len_char, deviation, length):
      return ''
    elif around(len_word, deviation, length):
      return ' '
    elif around(len_longsym, deviation, length):
      return 'longsym'
  return 'other'

def around(avg_length, deviation, length):
  min = avg_length * (1 - deviation)
  max = avg_length * (1 + deviation)
  return min <= length <= max

def decode(points):
  content = []
  str = ""
  syms = ""
  syms_point = None
  prev_point = 'other'
  for point in points:
    sym = point[3]
    if sym == '-' or sym == '.':
      syms += sym
      syms_point = point
      prev_point = 'morse'
    elif (sym == '' or sym == ' ') and prev_point == 'morse':
      char = translate_char(syms)
      str += char + sym
      syms = ""
      prev_point = 'morse'
    elif sym == 'longsym' and prev_point == 'morse':
      syms += "<longsym>"
      prev_point = 'morse'
    elif sym == 'other' or sym == '' or sym == ' ' or sym == 'longsym':
      if syms != "":
        str += translate_char(syms)
        syms = ""
      if str != "":
        if str == "e":
          content.append({"type": "other", "point": syms_point})
        else:
          content.append({"type": "str", "str": str})
        str = ""
      content.append({"type": "other", "point": point})
      prev_point = 'other'
    elif sym == 'sym' and prev_point == 'morse':
      pass
    else:
      content.append({"type": "other", "point": point})
      prev_point = 'other'
  if syms != '':
    str += translate_char(syms)
    if str != "":
      if str == "e":
        content.append({"type": "other", "point": syms_point})
      else:
        content.append({"type": "str", "str": str})
  return content

def print_content(content):
  for part in content:
    if part["type"] == "str":
      print(part["str"])

def get_alphabet():
  alphabet = {".-": "a",
              "-...": "b",
              "-.-.": "c",
              "-..": "d",
              ".": "e",
              "..-.": "f",
              "--.": "g",
              "....": "h",
              "..": "i",
              ".---": "j",
              "-.-": "k",
              ".-..": "l",
              "--": "m",
              "-.": "n",
              "---": "o",
              ".--.": "p",
              "--.-": "q",
              ".-.": "r",
              "...": "s",
              "-": "t",
              "..-": "u",
              "...-": "v",
              ".--": "w",
              "-..-": "x",
              "-.--": "y",
              "--..": "z",
              ".--.-": "\xe5",
              ".-.-": "\xe4",
              "---.": "\xf6",

              ".----": "1",
              "..---": "2",
              "...--": "3",
              "....-": "4",
              ".....": "5",
              "-....": "6",
              "--...": "7",
              "---..": "8",
              "----.": "9",
              "-----": "0",

              "-...-": "=",
              ".-.-.": "+",
              ".-.-.-": ".",
              "-..-.": "/",
              "..--..": "?",
              "--..--": ",",
              ".-...": "<wait>",
              "-....-": "-",
              "..<longsym>..": "<again>",
              "........": "<error>",
              }
  return alphabet

def letter_to_sym(c):
  alphabet = get_alphabet()
  for key, value in alphabet.items():
    if value == c:
      return key
  print("Can't find letter: " + c)
  exit(-1)

def translate_char(syms):
  alphabet = get_alphabet()
  char = ""
  if syms != "" and syms != "<longsym>":
    char = " " + syms + " "
  if syms in alphabet.keys():
    char = alphabet[syms]
  return char

if __name__ == '__main__':
  main()
