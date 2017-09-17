#!/usr/bin/python3

import argparse
import subprocess
import sublib


VERSION = '0.0.1'

TRIM = "[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{name}];" \
       "[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{name}];"
CONCAT = "[v{prev}][v{name}]concat[vc{name}];[a{prev}][a{name}]concat=v=0:a=1[ac{name}];"


def process_video(ffmpeg_path: str, input_path: str, parts_to_save: sublib.Subs, output_path: str, *ffmpeg_args):
    filter_complex = ""
    for index, event in enumerate(parts_to_save):
        timing = event['timing']
        filter_complex += TRIM.format(start=str(timing.begin.sec), end=str(timing.end.sec), name=str(index))
        if index > 0:
            filter_complex += CONCAT.format(prev=('c' if index > 1 else '') + str(index-1), name=str(index))
    out_name = ('c' if len(parts_to_save) > 1 else '') + str(len(parts_to_save) - 1)
    subprocess.call([ffmpeg_path, '-y', '-i', input_path, '-filter_complex', filter_complex[:-1],
                     '-map', '[v%s]' % out_name, '-map', '[a%s]' % out_name, *ffmpeg_args, output_path])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove several parts of the video using a subtitles file. '
                                                 "By default, it saves the parts covered by subtitles' timing. "
                                                 'Use --reverse flag to change this behaviour. '
                                                 'Note that the output file will be rewritten anyway.')
    parser.add_argument('video', help='input video path')
    parser.add_argument('subs', type=sublib.Subs.parse, help='input subtitles path')
    parser.add_argument('-o', '--output', default='out.mp4', metavar='OUT',
                        help="output video path, defaults to 'out.mp4'")
    # parser.add_argument('-r', '--reverse', action='store_true',
    #                     help="if set, the script will REMOVE the parts covered by subtitles' timing")
    parser.add_argument('-fp', '--ffmpeg-path', default='ffmpeg', metavar='PATH',
                        help='set the directory with ffmpeg binary, required unless ffmpeg is in OS PATH')
    # parser.add_argument('-fd', '--ffmpeg-default', action='store_true',
    #                     help='do not pass adcut default arguments into ffmpeg')
    parser.add_argument('-fa', '--ffmpeg-args', default=['-strict', '-2'], nargs=argparse.REMAINDER,
                        help="pass all the following arguments to ffmpeg")
    parser.add_argument('-v', '--version', action='version',
                        version='Adcut, version {}, created by Wolfram, '
                                'anon2anon, https://www.sunnysubs.com'.format(VERSION))

    args = parser.parse_args()
    process_video(args.ffmpeg_path, args.video, args.subs, args.output, *args.ffmpeg_args)
