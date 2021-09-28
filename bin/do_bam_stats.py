#!/usr/bin/env python
import sys
import argparse
from tempfile import NamedTemporaryFile
from subprocess import Popen

import pysam


def _setup_argparse():
    'It returns the argument parser'
    description = 'Calculate bam stats using samtools'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input', help='BAM or SAM files to process',
                        type=argparse.FileType('rb'), nargs='*')
    parser.add_argument('-s', '--sample', help='Sample You want to calculate')
    parser.add_argument('-q', '--min_mapq', type=int, default=0,
                        help='min. MAPQ to consider')
    parser.add_argument('-o', '--outfile', default=sys.stdout,
                        help='File to write the stats',
                        type=argparse.FileType('wt'))
    parser.add_argument('--rm_dups', action='store_true', default=False,
                        help='remove dups from stats')
    return parser


def _parse_args(parser):
    'It parses the command line and it returns a dict with the arguments.'

    parsed_args = parser.parse_args()
    in_fhands = parsed_args.input
    out_fhand = getattr(parsed_args, 'outfile')
    sample = parsed_args.sample
    min_mapq = parsed_args.min_mapq
    rm_dups = parsed_args.rm_dups
    return {'in_fhands': in_fhands, 'sample': sample, 'min_mapq': min_mapq,
            'out_fhand': out_fhand, 'rm_dups': rm_dups}


def _select_rgs_by_sample(in_fhands, sample=None):
    selected_rgs = []
    if sample is None:
        return selected_rgs
    for in_fhand in in_fhands:
        samfile = pysam.AlignmentFile(in_fhand.name, "r")
        for rg in samfile.header['RG']:
            rg_sample = rg['SM']
            rg_id = rg['ID']
            if rg_sample == sample:
                selected_rgs.append(rg_id)
    return selected_rgs


def make_stats_for_sample(in_fhands, stats_fhand, sample=None, min_mapq=None,
                          rm_dups=False):
    selected_rgs = _select_rgs_by_sample(in_fhands, sample)
    if len(in_fhands) > 1:
        merge_cmd = ['samtools', 'merge', '-u', '-']
        merge_cmd.extend([fhand.name for fhand in in_fhands])
        merge_cmd.append('|')
    else:
        merge_cmd = []

    flag = '1536' if rm_dups else '512'
    view_cmd = ['samtools', 'view', '-u', '-F', flag]

    if min_mapq:
        view_cmd.extend(['-q', str(min_mapq)])

    if selected_rgs and len(selected_rgs) == 1:
        view_cmd.extend(['-r', selected_rgs[0]])
    elif selected_rgs and len(selected_rgs) > 1:
        rg_fhand = NamedTemporaryFile()
        for rg in selected_rgs:
            rg_fhand.write(rg + '\n')
        rg_fhand.flush()
        view_cmd.extend(['-R', rg_fhand.name])

    if merge_cmd:
        view_cmd.append('-')
    else:
        view_cmd.append(in_fhands[0].name)
    view_cmd.append('|')

    stat_cmd = ['samtools', 'stats', '-c', '0,2000,1']
    if rm_dups:
        stat_cmd.append('-d')
    stat_cmd.append('-')

    cmd = merge_cmd + view_cmd + stat_cmd
    bash_fhand = NamedTemporaryFile(mode='wt')
    bash_fhand.write('#!/bin/bash\n')
    bash_fhand.write('set -o pipefail\n')
    bash_fhand.write(' '.join(cmd) + '\n')
    bash_fhand.flush()
    # sys.stderr.write(open(bash_fhand.name).read())

    process = Popen(['bash', bash_fhand.name], stdout=stats_fhand)
    process.wait()
    status_code = process.returncode

    # some temp file cleaning
    bash_fhand.close()
    try:
        rg_fhand.close()
    except UnboundLocalError:
        pass

    if status_code:
        raise RuntimeError('Error calculating stats')


def run():
    'It makes the actual job'
    parser = _setup_argparse()
    args = _parse_args(parser)
    stats_fhand = args['out_fhand']
    sample = args['sample']
    make_stats_for_sample(args['in_fhands'], stats_fhand,
                          sample=sample,
                          min_mapq=args['min_mapq'],
                          rm_dups=args['rm_dups'])


if __name__ == '__main__':
    run()
