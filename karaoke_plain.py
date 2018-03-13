from copy import deepcopy
from sublib import Subs, Timing
import re

KARAOKE_REGEX = re.compile(r'{\\k(\d+)}')

if __name__ == '__main__':
    subs = Subs.parse('haiku.ass')
    new_subs = deepcopy(subs)
    new_subs.data.clear()
    for event in subs:
        current_sum = event['timing'].begin.ss
        for index, clause in enumerate(KARAOKE_REGEX.finditer(event['text'])):
            new_sum = current_sum + int(clause.group(1))
            new_event = deepcopy(event)
            new_event['timing'] = Timing(current_sum, new_sum, 'ss')
            pieces = KARAOKE_REGEX.split(event['text'])[2::2]
            new_event['text'] = ''.join(pieces[:index+1]) + '{\\alpha&HFF&}' + ''.join(pieces[index+1:])
            new_subs.append(new_event)
            current_sum = new_sum
    new_subs.clean_ass('haiku_gen.ass', 'rus')
