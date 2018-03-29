"""My subtitles library: at the moment supports .srt and .ass"""
from __future__ import division, unicode_literals
from collections import UserDict, UserList
from copy import deepcopy
from decimal import Decimal
from itertools import tee
import os
import re


INVISIBLE_CHARS = re.compile(r"[\u115f\u1160\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u200b"
                             r"\u2028\u2029\u202f\u205f\u3000\u3164\ufeff\uff0e\uffa0\ufff9\ufffa\ufffb\ufffc]")
STYLE_FORMAT = "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, " \
               "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow," \
               " Alignment, MarginL, MarginR, MarginV, Encoding"
EVENT_FORMAT = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"


def pairwise(iterable):
    """https://docs.python.org/3.6/library/itertools.html#itertools-recipes
    s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def preprocess(text: str) -> str:
    """Turns fancy spaces into normal spaces"""
    return INVISIBLE_CHARS.sub(' ', text).strip()


class Timestamp:
    """Left or right end of an event. Supports 4 formats: ass, srt, ss (santiseconds) and sec (seconds)"""
    def __init__(self, stamp, stamp_type: str):  # stamp: str || int || float || Decimal
        try:
            if stamp_type == 'sec':
                self._value = int(round(Decimal(stamp)*100))
            elif stamp_type == 'ss':
                self._value = int(stamp)
            elif stamp_type == 'ass':
                h, m, s = stamp.split(':')
                s, ss = s.split('.')
                self._value = int(h) * 360000 + int(m) * 6000 + int(s) * 100 + int(ss)
            elif stamp_type == 'srt':
                h, m, s = stamp.split(':')
                s, ms = s.split(',')
                self._value = int(h) * 360000 + int(m) * 6000 + int(s) * 100 + int(round(int(ms)/10))
            elif stamp_type == 'vtt':
                h, m, s = stamp.split(':')
                s, ms = s.split('.')
                self._value = int(h) * 360000 + int(m) * 6000 + int(s) * 100 + int(round(int(ms)/10))
            else:
                raise TypeError("Unknown time stamp type: %s" % stamp_type)
        except ValueError:
            raise RuntimeError("Error: incorrect syntax of a time stamp: %s" % repr(stamp))

    def __add__(self, ss: int) -> 'Timestamp':
        x = deepcopy(self)
        x += ss
        return x

    def __eq__(self, other: 'Timestamp') -> bool:
        return self._value == other.ss

    def __hash__(self):
        return hash(self._value)

    def __iadd__(self, ss: int) -> 'Timestamp':
        self._value += ss
        return self

    def __isub__(self, ss: int) -> 'Timestamp':
        self._value -= ss
        return self

    def __imul__(self, coef) -> 'Timestamp':
        self._value = int(round(coef * self._value))
        return self

    def __lt__(self, other: 'Timestamp') -> bool:
        return self._value < other.ss

    def __le__(self, other: 'Timestamp') -> bool:
        return self._value <= other.ss

    def __mul__(self, coef) -> 'Timestamp':
        x = deepcopy(self)
        x *= coef
        return x

    def __repr__(self):
        return "Timestamp %s" % self.ass

    def __str__(self):
        return self.ass

    def __sub__(self, other: 'Timestamp') -> int:
        if type(other) in (int, float, Decimal):
            raise TypeError("Only Timestamp can be subtracted from Timestamp")
        return self._value - other.ss

    @property
    def ss(self) -> int:
        return self._value

    @property
    def sec(self) -> Decimal:
        return Decimal(self._value) / Decimal(100)

    @property
    def ass(self) -> str:
        tmp, ss = divmod(self._value, 100)
        tmp, s = divmod(tmp, 60)
        h, m = divmod(tmp, 60)
        return "{h}:{m:0>2}:{s:0>2}.{ss:0>2}".format(h=h, m=m, s=s, ss=ss)

    @property
    def srt(self) -> str:
        tmp, ss = divmod(self._value, 100)
        tmp, s = divmod(tmp, 60)
        h, m = divmod(tmp, 60)
        return "{h:0>2}:{m:0>2}:{s:0>2},{ss:0>2}0".format(h=h, m=m, s=s, ss=ss)


class Timing:
    """Timing of a single event"""
    def __init__(self, begin, end, stamps_type: str):
        self.begin, self.end = Timestamp(begin, stamps_type), Timestamp(end, stamps_type)

    def __add__(self, ss: int) -> 'Timing':
        x = deepcopy(self)
        x += ss
        return x

    def __contains__(self, item: Timestamp) -> bool:
        return self.begin <= item < self.end

    def __eq__(self, other: 'Timing') -> bool:
        return self.begin == other.begin and self.end == other.end

    def __hash__(self):
        return hash((self.begin, self.end))

    def __iadd__(self, ss: int) -> 'Timing':
        """Move timing ss ahead"""
        self.begin += ss
        self.end += ss
        return self

    def __imul__(self, coef) -> 'Timing':
        """Multiplying both ends by coef: feature for changing the framerate."""
        self.begin *= coef
        self.end *= coef
        return self

    def __isub__(self, ss: int) -> 'Timing':
        """Move timing ss behind"""
        return self.__iadd__(-ss)

    def __len__(self) -> int:
        return self.end.ss - self.begin.ss

    def __lt__(self, other: 'Timing') -> bool:
        return (self.begin, self.end) < (other.begin, other.end)

    def __le__(self, other: 'Timing') -> bool:
        return (self.begin, self.end) <= (other.begin, other.end)

    def __mul__(self, coef) -> 'Timing':
        x = deepcopy(self)
        x *= coef
        return x

    def __repr__(self):
        return "Timing(%s)" % self

    def __str__(self):
        return str(self.begin) + ',' + str(self.end)

    def __sub__(self, ss: int) -> 'Timing':
        x = deepcopy(self)
        x -= ss
        return x

    def collides(self, other: 'Timing') -> bool:
        return other.begin in self or self.begin in other

    @property
    def consistent(self) -> bool:
        return Timestamp(0, 'ss') <= self.begin <= self.end

    def intersection(self, other: 'Timing') -> int:
        a, b = sorted([self, other])
        return max(0, min(a.end, b.end) - b.begin)

    def union(self, other: 'Timing') -> 'Timing':
        timestamps = [self.begin.ss, self.end.ss, other.begin.ss, other.end.ss]
        return Timing(min(timestamps), max(timestamps), 'ss')

    def similarity(self, other: 'Timing') -> float:
        return self.intersection(other) / len(self.union(other))

    @property
    def pad_view(self) -> str:
        tmp, ss = divmod(self.begin.ss, 100)
        m, s = divmod(tmp, 60)
        return "{m:0>2}:{s:0>2}.{ss:0>2},{ls}.{lss:0>2}".format(m=m, s=s, ss=ss,
                                                                ls=len(self) // 100, lss=len(self) % 100)


class Event(UserDict):
    DEFAULT = [('layer', '0'),
               ('timing', Timing('0', '0', 'ss')),
               ('style', 'Default'), ('actor', ''),
               ('margin_l', '0'), ('margin_r', '0'), ('margin_v', '0'),
               ('effect', ''),
               ('text', '')]
    DEF_DICT = dict(DEFAULT)
    REGEX = re.compile(r'Dialogue:(?: *)(\d+),([0-9:.]+),([0-9:.]+),(.*?),(.*?),(\d+),(\d+),(\d+),(.*?),(.*)')
    TEMPLATE = "Dialogue: " + ",".join("{d[%s]}" % key for key, _ in DEFAULT)

    def __init__(self, **kwargs):
        UserDict.__init__(self, kwargs)

    def __eq__(self, other: 'Event') -> bool:
        return self['style'] == other['style'] and self['text'] == other['text']

    def __getitem__(self, item: str):  # -> str || Timing
        if item not in self:
            return self.DEF_DICT[item]
        return self.data[item]

    def __iadd__(self, ss: int) -> 'Event':
        self['timing'] += ss
        return self

    def __imul__(self, coef) -> 'Event':
        self['timing'] *= coef
        return self

    def __len__(self):
        return len(self['timing'])

    def __le__(self, other: 'Event') -> bool:
        return self['timing'] <= other['timing']

    def __lt__(self, other: 'Event') -> bool:
        return self['timing'] < other['timing']

    def __str__(self):
        return self.TEMPLATE.format(d=self).replace('\n', '\\N')

    @classmethod
    def from_ass(cls, dialogue_line: str) -> 'Event':
        match = cls.REGEX.match(dialogue_line)
        if match is None:
            raise RuntimeError("Syntax error: %s" % dialogue_line)
        layer, begin, end = (match.group(i) for i in (1, 2, 3))
        return cls(layer=layer, timing=Timing(begin, end, 'ass'),
                   **dict((key, match.group(i)) for i, (key, _) in zip(range(4, 11), cls.DEFAULT[2:])))


class Style(UserDict):
    DEFAULT = [('name', 'Default'),
               ('font', 'Arial'),
               ('size', '68'),
               ('colors', '&H00FFFFFF,&H000000FF,&H007D7E80,&H00000000'),
               ('tail', '0,0,0,0,100,100,0,0,1,2.25,2.25,2,30,30,45,1')]
    DEF_DICT = dict(DEFAULT)
    REGEX = re.compile(r'Style:(?: *)(.*?),(.+?),(\d+),(&H[0-9A-F]{8},&H[0-9A-F]{8},&H[0-9A-F]{8},&H[0-9A-F]{8}),(.*)')
    TEMPLATE = "Style: " + ",".join("{d[%s]}" % key for key, _ in DEFAULT)

    def __init__(self, **kwargs):
        UserDict.__init__(self, kwargs)

    def __eq__(self, other: 'Style') -> bool:
        return self['name'] == other['name'] and self['colors'] == other['colors']

    def __getitem__(self, item: str) -> str:
        if item not in self:
            return self.DEF_DICT[item]
        return self.data[item]

    def __le__(self, other: 'Style') -> bool:
        return self['name'] <= other['name']

    def __lt__(self, other: 'Style') -> bool:
        return self['name'] < other['name']

    def __str__(self):
        return self.TEMPLATE.format(d=self)

    @classmethod
    def from_ass(cls, style_line: str) -> 'Style':
        match = cls.REGEX.match(style_line)
        if match is None:
            raise RuntimeError("Syntax error: %s" % style_line)
        return cls(**dict((key, match.group(i)) for i, (key, _) in zip(range(1, 6), cls.DEFAULT)))


class Subs(UserList):
    RESOLUTION = (1920, 1080)
    VERBOSE = True
    SECTION_RE = re.compile(r'\[(.*)\]$')
    SRT_TIMING_RE = re.compile(r'(\d+:\d+:\d+,\d+)[ >-]+(\d+:\d+:\d+,\d+)$')
    VTT_TIMING_RE = re.compile(r'(\d+:\d+:\d+\.\d+)[ >-]+(\d+:\d+:\d+\.\d+)')

    def __init__(self):
        UserList.__init__(self)
        self.script_info = {}
        self.styles = {'Default': Style()}  # Name: Style object

    def __add__(self, other) -> 'Subs':
        return other.__radd__(self)

    def __iadd__(self, ss: int) -> 'Subs':
        for event in self:
            event += ss
        return self

    def __imul__(self, coef) -> 'Subs':
        for event in self:
            event *= coef
        return self

    def __radd__(self, other) -> 'Subs':
        if isinstance(other, Subs):
            ans = deepcopy(self)
            ans.data += other.data
            for key, value in other.styles.items():
                if key not in ans.styles:
                    ans.styles[key] = value
            return ans
        elif isinstance(other, int):
            tmp = deepcopy(self)
            ans = tmp.__iadd__(other)
            return ans
        raise TypeError

    def add_style(self, style_line: str) -> None:
        new_style = Style.from_ass(style_line)
        name = new_style['name']
        if name in self.styles and name != 'Default' and self.VERBOSE:
            print("Warning: duplicate style %s" % repr(name))
        self.styles[name] = new_style

    def add_event(self, dialogue_line: str) -> None:
        self.append(Event.from_ass(dialogue_line))

    def check_events_collisions(self) -> None:
        self.sort()
        for event1, event2 in pairwise(self):
            if event1['timing'].collides(event2['timing']):
                print("Warning: timing collision:\n{}\n{}".format(event1, event2))

    def ensure_consistent_timing(self) -> None:
        for event in self:
            if not event['timing'].consistent:
                print("Warning: inconsistent timing in event\n{}".format(event))

    @classmethod
    def parse(cls, file_path: str) -> 'Subs':
        if os.path.isfile(file_path):
            if file_path[-4:] == '.ass':
                return cls.parse_ass(file_path)
            elif file_path[-4:] == '.srt':
                return cls.parse_srt(file_path)
            elif file_path[-4:] == '.vtt':
                return cls.parse_vtt(file_path)
            else:
                print("Unknown subtitle format: '{}'".format(file_path))
        else:
            print("File '{}' does not exist.".format(file_path))

    @classmethod
    def parse_ass(cls, file_path: str) -> 'Subs':
        with open(file_path, 'rb') as ass_file:
            ass_txt = ass_file.read().decode()
        current_section = ''
        ans = cls()
        for line in ass_txt.split('\n'):
            if current_section != "Events":
                line = line.split(';')[0]
            line = preprocess(line)
            if line == '':
                continue
            match = cls.SECTION_RE.match(line)
            if match is None:
                if current_section == 'Script Info':
                    tmp = line.split(':', 1)
                    var, value = tmp
                    value = value.lstrip()
                    ans.script_info[var] = value
                elif 'Format:' in line:
                    continue
                elif current_section == 'V4+ Styles':
                    ans.add_style(line)
                elif current_section == 'Events':
                    ans.add_event(line.replace('\\N', '\n'))
            else:
                current_section = match.group(1)
        return ans

    @classmethod
    def parse_srt(cls, file_path: str) -> 'Subs':
        with open(file_path, 'rb') as srt_file:
            srt_txt = srt_file.read().decode()
        events = []
        current_text = ''
        for line in reversed(srt_txt.split('\n')):
            line = preprocess(line)
            if line == '' or line.isdigit():
                continue
            match = cls.SRT_TIMING_RE.match(line)
            if match is None:
                current_text = line + '\n' + current_text
            else:
                current_timing = Timing(match.group(1), match.group(2), 'srt')
                events.append(Event(timing=current_timing, text=current_text.strip()))
                current_text = ''
        ans = cls()
        for event in reversed(events):
            ans.append(event)
        return ans

    @classmethod
    def parse_vtt(cls, file_path: str) -> 'Subs':
        with open(file_path, 'rb') as srt_file:
            srt_txt = srt_file.read().decode()
        events = []
        current_text = ''
        for line in reversed(srt_txt.split('\n')):
            line = preprocess(line)
            if line == '' or line.isdigit():
                continue
            match = cls.VTT_TIMING_RE.match(line)
            if match is None:
                current_text = line + '\n' + current_text
            else:
                current_timing = Timing(match.group(1), match.group(2), 'vtt')
                events.append(Event(timing=current_timing, text=current_text.strip()))
                current_text = ''
        ans = cls()
        for event in reversed(events):
            ans.append(event)
        return ans

    def remove_actors(self) -> None:
        for event in self:
            if 'actor' in event:
                del event['actor']

    def remove_extra_styles(self) -> None:
        existing_styles = set(event['style'] for event in self)
        for key in list(self.styles.keys()):
            if key not in existing_styles:
                del self.styles[key]

    def unify_symbols(self) -> None:
        for event in self:
            event['text'] = re.sub(r'\s+', ' ', event['text'].replace('...', '…').replace(' - ', ' — '))
            event['text'] = re.sub(r'… ?', '… ', event['text']).strip()

    def language_processing(self, lang: str) -> None:
        for event in self:
            if lang == 'rus':
                event['text'] = event['text'].replace('…?', '?..').replace('…!', '!..').replace('c', 'с')
            elif lang == 'eng':
                event['text'] = event['text'].replace('?..', '…?').replace('!..', '…!')
            else:
                print("Warning: unsupported language {}, no language processing performed.".format(repr(lang)))

    def set_default_resolution(self) -> None:
        self.script_info['PlayResX'], self.script_info['PlayResY'] = self.RESOLUTION

    def set_default_styles(self, resolution: tuple = None) -> None:
        if resolution is None:
            resolution = tuple(int(self.script_info['PlayRes{}'.format(c)]) for c in 'XY')
        size = str(int(round(int(Style.DEF_DICT['size'])*resolution[0]/self.RESOLUTION[0])))
        for _, style in self.styles.items():
            for key in ('font', 'tail'):
                style[key] = Style.DEF_DICT[key]
            style['size'] = size

    def join_info(self) -> str:
        return "\n".join(x+': '+str(y) for x, y in sorted(self.script_info.items())) + '\n'

    def join_styles(self) -> str:
        output_styles = [str(self.styles[i]) for i in self.styles]
        return '\n'.join(sorted(output_styles)) + '\n'

    def join_events(self) -> str:
        self.sort()
        output_events = [str(event) for event in self]
        return '\n'.join(output_events) + '\n'

    def output_ass(self, file_path: str) -> None:
        text = '\ufeff[Script Info]\n{info}\n[V4+ Styles]\n{style_format}\n'\
               '{styles}\n[Events]\n{event_format}\n{events}'\
                .format(info=self.join_info(), styles=self.join_styles(), events=self.join_events(),
                        style_format=STYLE_FORMAT, event_format=EVENT_FORMAT)
        with open(file_path, "wb") as f:
            f.write(text.replace('\n', '\r\n').encode())

    def output_srt(self, file_path: str) -> None:
        self.sort()
        text = ''
        for event in self:
            timing = event['timing']
            str_timing = " --> ".join(ts.srt for ts in (timing.begin, timing.end))
            text += str_timing + '\n' + event['text'] + '\n\n'
        with open(file_path, "wb") as f:
            f.write(text.strip().replace('\n', '\r\n').encode())

    def clean_ass(self, file_path: str, lang: str) -> None:
        ans = deepcopy(self)
        ans.remove_extra_styles()
        ans.remove_actors()
        ans.unify_symbols()
        ans.language_processing(lang)
        ans.set_default_resolution()
        ans.set_default_styles()
        if self.VERBOSE:
            ans.check_events_collisions()
            ans.ensure_consistent_timing()
        ans.output_ass(file_path)


def merge(dir_name='merge') -> None:
    subs = []
    s, e = 'XX', 'XX'
    for filename in os.listdir(dir_name):
        match = re.search(r'[sS](\d{1,2})[eE](\d{1,2})', filename)
        if match and s == 'XX':
            s, e = [match.group(i).zfill(2) for i in (2, 4)]
        try:
            sbs = Subs.parse(os.path.join(dir_name, filename))
            if sbs is not None:
                subs.append(sbs)
        except UnicodeDecodeError:
            pass
    sum(subs).clean_ass(os.path.join(dir_name, 'S{}E{}.ass'.format(s, e)), 'eng')


if __name__ == '__main__':
    merge('.')
