#!/usr/bin/env python

import argparse
from collections import Counter

import pysam

from mapping.plot import draw_histogram_in_fhand, BAR


def _setup_argparse():
    'It returns the argument parser'
    description = 'Draw mapq histogram'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input', help='BAM or SAM file to process',
                        type=argparse.FileType('rb'))
    parser.add_argument('-o', '--outfile', dest='outfile', required=True,
                        help='Output file',
                        type=argparse.FileType('wb'))

    return parser


def _parse_args(parser):
    'It parses the command line and it returns a dict with the arguments.'

    parsed_args = parser.parse_args()
    bam_fhand = parsed_args.input
    out_fhand = getattr(parsed_args, 'outfile')

    return {'bam_fhand': bam_fhand, 'out_fhand': out_fhand}


def read_mapqs(fhand):
    mapq_counter = Counter()
    bam = pysam.AlignmentFile(fhand.name)
    for read in bam:
        if not read.is_unmapped:
            mapq_counter[read.mapq] += 1
    return mapq_counter


def run():
    'It makes the actual job'
    parser = _setup_argparse()
    args = _parse_args(parser)
    out_fhand = args['out_fhand']

    mapq_counter = read_mapqs(args['bam_fhand'])

    draw_histogram_in_fhand(mapq_counter, fhand=out_fhand,
                            title='Mapq distribution', kind=BAR,
                            ylabel="Num. Seqs", xlabel="Mapq")


if __name__ == '__main__':
    run()
