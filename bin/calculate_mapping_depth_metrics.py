#!/usr/bin/env python3
import sys
import argparse
from collections import Counter

from dora.plot import draw_histogram_in_fhand
from dora.stats import calc_coverage_stats, write_coverage_stats


HEADER = ['Sample', 'Min', 'Max', 'Average depth', 'Std. DEV', 'Median', 'Bases Covered',
          'Bases uncovered', 'GB of mapped reads', 'Uniformity of Coverage (Pct > 0.2*mean)',
          'Uniformity of Coverage (Pct > 0.5*mean)']


def _setup_argparse():
    'It returns the argument parser'
    description = 'Calculate some bam depth stats'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input', help='Depth file produced by samtools depth',
                        type=argparse.FileType('rt'), default=sys.stdin)
    parser.add_argument('-o', '--outfile', default=sys.stdout,
                        help='File to write the stats',
                        type=argparse.FileType('wt'))
    parser.add_argument('-p', '--plotfile',
                        help='File to write the coverage distrib',
                        type=argparse.FileType('wb'))
    parser.add_argument('--outfmt', default='text',
                        help='Format of the output', choices=['text', 'tabular',
                                                              'tabular_header'])
    parser.add_argument('-s', '--samplename', default='default sample name',
                        help='Sample name')
    return parser


def _parse_args(parser):
    'It parses the command line and it returns a dict with the arguments.'

    parsed_args = parser.parse_args()
    in_fhand = parsed_args.input
    out_fhand = getattr(parsed_args, 'outfile')
    plot_fhand = parsed_args.plotfile
    out_format = parsed_args.outfmt
    samplename = parsed_args.samplename

    return {'in_fhand': in_fhand, 'out_fhand': out_fhand,
            'plot_fhand': plot_fhand, 'out_format': out_format,
            'samplename': samplename}



def main():
    parser = _setup_argparse()
    args = _parse_args(parser)
    out_fhand = args['out_fhand']
    in_fhand = args['in_fhand']
    out_format = args['out_format']
    plot_fhand = args['plot_fhand']
    samplename = args['samplename']
    count = 0
    depths = Counter()
    for line in in_fhand:
        line = line.strip()
        if not line or line[0] == '#':
            continue
        items = line.split()
        depths[int(items[2])] += 1
        # count += 1
        # if count > 1000000:
        #     break
    # dps = []
    # for dp, count in depths.items():
    #     dps.extend([dp] * count)
    # depths = np.array(dps)
    stats = calc_coverage_stats(depths, is_counter=True)


    if out_format == 'text':
        write_coverage_stats(stats, samplename, out_fhand)
    else:
        if out_format == 'tabular_header':
            header = HEADER + [f'Pos with dp more than: {rang}' for rang in stats['range_covs'].keys()]
            out_fhand.write('\t'.join(header)+ '\n')
        if 'tabular' in out_format:
            items = [
                samplename,
                str(stats['min']),
                str(stats['max']),
                f"{stats['mean']:.2f}",
                f"{stats['std']:.2f}",
                f"{stats['median']:.2f}",
                str(stats['bases_covered']),
                str(stats['bases_uncovered']),
                str(int(stats['mean'] * stats['bases_covered'])),
                f"{stats['uniformity_coverage_pct0.2']:.2f}",
                f"{stats['uniformity_coverage_pct0.5']:.2f}"]
            total_bases = stats['bases_covered'] + stats['bases_uncovered']
            items.extend(f'{(v/total_bases):.2f}' for v in stats['range_covs'].values())
            out_fhand.write('\t'.join(items)+ '\n')


    if plot_fhand:
        title = 'Dist. of BAM depths'
        x_label = "Depths"
        y_label = "Num. bases with this depth"
        x_min = 1
        x_max = 250
        draw_histogram_in_fhand(depths, fhand=plot_fhand,
                                xlabel=x_label, ylabel=y_label, title=title,
                                xmin=x_min, xmax=x_max, ylog_scale=True)


if __name__ == '__main__':
    main()
