#!/usr/bin/env python

'It draws a histogram with the coverage of a bam file'

import argparse
import sys
from collections import Counter

from dora.plot import draw_histogram_in_fhand

COVERAGE_RANGE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 75, 100)
PLOTS_PER_CHAR = 3


def _setup_argparse():
    'It returns the argument parser'
    description = 'Draw coverage histogram'
    epilog = 'WARNING: It will be 10 times faster if bams with only one read'
    epilog += ' group are used and min_mapq is not used'
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('input', help='Bamstat file', default=sys.stdin,
                        type=argparse.FileType('rt'), nargs='?')
    parser.add_argument('-p', '--plotfile', required=True,
                        help='File to write the graph',
                        type=argparse.FileType('wb'))
    parser.add_argument('-o', '--outfile', default=sys.stdout,
                        help='File to write the stats',
                        type=argparse.FileType('wt'))
    parser.add_argument('-m', '--xlim_left', type=int,
                        help='Limit of the x axes in the left')
    parser.add_argument('-M', '--xlim_rigth', type=int,
                        help='Limit of the x axes in the rigth')
    parser.add_argument('-b', '--ylim_bottom', type=int,
                        help='Limit of the y axes in the bottom')
    parser.add_argument('-t', '--ylim_top', type=int,
                        help='Limit of the y axes in the top')
    parser.add_argument('-g', '--genome_size', help='Genome_size', type=int)

    return parser


def _parse_args(parser):
    'It parses the command line and it returns a dict with the arguments.'

    parsed_args = parser.parse_args()
    in_fhand = parsed_args.input
    plot_fhand = getattr(parsed_args, 'plotfile')
    out_fhand = getattr(parsed_args, 'outfile')
    xlim_left = parsed_args.xlim_left
    xlim_rigth = parsed_args.xlim_rigth
    ylimits = parsed_args.ylim_bottom, parsed_args.ylim_top
    genome_size = parsed_args.genome_size
    return {'in_fhand': in_fhand, 'out_fhand': out_fhand, 'ylimits': ylimits,
            'xlim_left': xlim_left, 'xlim_rigth': xlim_rigth,
            'plot_fhand': plot_fhand, 'genome_size': genome_size}


def _get_coverages(fhand):
    coverages = Counter()
    for line in fhand:

        if not line.startswith('COV'):
            continue
        line = line.strip()
        cov, num_bases = line.split()[2:]
        coverages[int(cov)] = int(num_bases)
    return coverages


def run():
    'It makes the actual job'
    parser = _setup_argparse()
    args = _parse_args(parser)

    coverages = _get_coverages(args['in_fhand'])

    title = 'Dist. of BAM coverages'
    xlabel = "Coverage"
    ylabel = "Num. bases with this coverage"

    draw_histogram_in_fhand(coverages, fhand=args['plot_fhand'],
                            xlabel=xlabel, ylabel=ylabel, title=title,
                            xmin=args['xlim_left'], xmax=args['xlim_rigth'],
                            ylimits=args['ylimits'], ylog_scale=True)

    write_coverage_stats(coverages, 'sample', args['out_fhand'],
                         args['genome_size'])


def write_coverage_stats(coverages, sample, out_fhand, genome_size, ):
    stdout = 'Data for sample {}\n'.format(sample)
    stdout += '-------------------------------\n'
    stdout += 'Minimum coverage value: {}\n'.format(min(coverages.keys()))
    stdout += 'Maximum coverage value: {}\n'.format(max(coverages.keys()))
    out_fhand.write(stdout)

    limit_count = Counter()
    for cov, count in coverages.items():
        for coverage_limit in COVERAGE_RANGE:
            if cov >= coverage_limit:
                limit_count[coverage_limit] += count
    out_fhand.write('Positions with the given coverage:\n')
    out_fhand.write('----------------------------------\n')
    out_fhand.write('Coverture\tcount\t%porcentaje bases\t')
    out_fhand.write('coverture/positions cov>1\n')

    for limit in sorted(limit_count.keys()):
        fraction_of_1 = limit_count[limit] / limit_count[1]
        if genome_size:
            percent_mapped = '{:.2%}'.format(limit_count[limit] / genome_size)
        else:
            percent_mapped = 'unknown'

        out_fhand.write("{}\t{}\t{}\t{}\n".format(limit, limit_count[limit],
                                                  percent_mapped,
                                                  fraction_of_1))
    out_fhand.write("\n")


if __name__ == '__main__':
    run()
