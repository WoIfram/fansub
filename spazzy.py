#!/usr/bin/python3

import argparse
import re
from collections import defaultdict
from operator import itemgetter
from itertools import groupby

# https://pypi.python.org/pypi/pyahocorasick
import ahocorasick

import sublib


VERSION = '0.2.0'

start_of_sentence = True
good_symbols = frozenset(list(chr(i) for i in range(ord('a'), ord('z') + 1)) +
                         list(chr(i) for i in range(ord('A'), ord('Z') + 1)) +
                         list(chr(i) for i in range(ord('0'), ord('9') + 1)) +
                         list('()!.,?;:\'♪" \n-'))
effects = re.compile(r'<.*?>', re.DOTALL)
brackets = re.compile(r'\[.*?\]', re.DOTALL)
sentence_border = re.compile(r'([?!.♪]|…$)')
word_regex = re.compile(r'(\w+)')
automaton = ahocorasick.Automaton()
with open('names.txt') as names:
    dict_of_names = defaultdict(list)
    for name in names.readlines():
        sensitive = name.strip()
        if sensitive == '':
            continue
        insensitive = sensitive.lower()
        automaton.add_word(insensitive, insensitive)
        for i, symb in enumerate(sensitive):
            if symb.isupper():
                dict_of_names[insensitive].append(i)
    automaton.make_automaton()


def capitalize(word):
    cap = True
    answer = ''
    for symb in word:
        if cap and symb.isalpha():
            answer += symb.capitalize()
            cap = False
        else:
            answer += symb
    return answer


def process_plain_text(text: str):
    global start_of_sentence
    text = effects.sub('', text)
    text = brackets.sub('', text)
    text = ''.join(letter for letter in text if letter in good_symbols)
    text = text.replace('...', '…').replace('\n', ' ').replace('--', ' — ')
    text = text.lower()

    cap_needed = set()
    for ending, name in automaton.iter(text):
        begin = ending - len(name) + 1
        left_word_border = (begin == 0) or not text[begin - 1].isalpha()
        right_word_border = (ending == len(text) - 1) or not text[ending + 1].isalpha()
        if left_word_border and right_word_border:
            for index in dict_of_names[name]:
                cap_needed.add(begin + index)
    text = ''.join((symb.upper() if i in cap_needed else symb) for i, symb in enumerate(text))

    new_text = ''
    for element in sentence_border.split(text):
        if sentence_border.match(element):
            start_of_sentence = True
            new_text += element
        else:
            if start_of_sentence:
                new_text += capitalize(element)
                if any(s.isalpha() for s in element):
                    start_of_sentence = False
            else:
                new_text += element
    text = new_text.replace('♪', '').strip()
    if len(text) == 0:
        return ''
    new_text = text[0]
    for i in range(1, len(text)):
        if text[i].isupper() and text[i-1].islower():
            new_text += ' ' + text[i]
        else:
            new_text += text[i]
    return new_text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Spazz into Anon subs.')
    parser.add_argument('subs', type=sublib.Subs.parse, help='input subtitles path')
    parser.add_argument('-o', '--output', default='out.ass', metavar='OUT',
                        help="output subs path, defaults to 'out.ass'")
    parser.add_argument('-v', '--version', action='version',
                        version='Spazzy, version {}, created by Wolfram, '
                                'anon2anon, https://www.sunnysubs.com'.format(VERSION))

    args = parser.parse_args()
    processed_subs = sublib.Subs()
    for event in args.subs:
        processed_text = process_plain_text(event['text'])
        if any(s.isalnum() for s in processed_text):
            processed_subs.append(sublib.Event(text=processed_text, timing=event['timing']))
    output_subs = sublib.Subs()
    for timing, events in groupby(processed_subs, itemgetter('timing')):
        output_subs.append(sublib.Event(text=' '.join(map(itemgetter('text'), events)), timing=timing))
    output_subs.clean_ass(args.output, 'eng')
