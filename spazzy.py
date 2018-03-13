#!/usr/bin/python3

import argparse
import sublib
import re


VERSION = '0.0.1'

start_of_sentence = True
good_symbols = frozenset(list(chr(i) for i in range(ord('a'), ord('z') + 1)) +
                         list(chr(i) for i in range(ord('A'), ord('Z') + 1)) +
                         list(chr(i) for i in range(ord('0'), ord('9') + 1)) +
                         list('()!.,?;:\'♪" \n-'))
effects = re.compile(r'<.*?>', re.DOTALL)
brackets = re.compile(r'\[.*?\]', re.DOTALL)
sentence_border = re.compile(r'([?!.♪]|…$)')
word_regex = re.compile(r'(\w+)')
with open('names.txt') as names:
    dict_of_names = dict((name.strip().lower(), name.strip()) for name in names.readlines())


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
    new_text = ''
    prev_word = ''
    for element in word_regex.split(text):
        if element in dict_of_names:
            prev_word = dict_of_names[element]
            new_text += prev_word
        elif prev_word.lower() + ' ' + element in dict_of_names:
            full_name = dict_of_names[prev_word.lower() + ' ' + element]
            new_text = new_text[:new_text.rfind(prev_word)] + full_name
            prev_word = full_name.split()[-1]
        else:
            new_text += element
            if word_regex.match(element):
                prev_word = element
    text = new_text
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
    return new_text.replace('♪', '').strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Spazz into Anon subs.')
    parser.add_argument('subs', type=sublib.Subs.parse, help='input subtitles path')
    parser.add_argument('-o', '--output', default='out.ass', metavar='OUT',
                        help="output subs path, defaults to 'out.ass'")
    parser.add_argument('-v', '--version', action='version',
                        version='Spazzy, version {}, created by Wolfram, '
                                'anon2anon, https://www.sunnysubs.com'.format(VERSION))

    args = parser.parse_args()
    output_subs = sublib.Subs()
    for event in args.subs:
        processed_text = process_plain_text(event['text'])
        if any(s.isalnum() for s in processed_text):
            output_subs.append(sublib.Event(text=processed_text, timing=event['timing']))
    output_subs.unify_symbols()
    output_subs.output_ass(args.output)
