#!/usr/bin/env python3
import argparse
import sys
from dora.mapping.bwa import map_mp_bwamem


def _setup_argparse():
    'It returns the argument parser'
    description = 'Map with bwa'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-1', '--pair1', help='pair 1 fast path', required=True,
                        type=argparse.FileType('rb'))
    parser.add_argument('-2', '--pair2', help='pair 2 fast path',
                        type=argparse.FileType('rb'))
    parser.add_argument('-r', '--bwa_index', required=True,
                        help='Path to bwa index')
    parser.add_argument('-o', '--outfile', required=True, help='Output file')
    parser.add_argument('-t', '--threads', help='Threads', default=1, type=int)
    parser.add_argument('-s', '--sample', required=True, help='sample')
    parser.add_argument('-l', '--library', help='Library')
    parser.add_argument('-g', '--read_group', help='Read group')
    parser.add_argument('-d', '--do_duplicates', help='Do duplicates?',
                        action='store_true')
    parser.add_argument('-e', '--do_downgrade_edges', help='Do duplicates?',
                        action='store_true')
    parser.add_argument('-c', '--downgrade_edges_conf', nargs=2, type=int,
                        help='Read start and end edges sizes to downgrade')
    parser.add_argument('-f', '--filter_supplementary',
                        help='Filter out supplementary reads',
                        action='store_true')
    return parser


def _parse_args(parser):
    'It parses the command line and it returns a dict with the arguments.'

    parsed_args = parser.parse_args()
    pair1 = parsed_args.pair1
    pair2 = parsed_args.pair2
    conf = {}
    conf['read1_fpath'] = pair1.name
    if pair2 is not None:
        conf['read2_fpath'] = pair2.name
        paired = True
    else:
        paired = False
    conf['paired'] = paired

    conf['out_fpath'] = parsed_args.outfile
    sample = parsed_args.sample
    conf['sample'] = sample
    conf['library'] = parsed_args.library if parsed_args.library else sample
    conf['read_group'] = parsed_args.read_group if parsed_args.read_group else sample
    conf['index'] = parsed_args.bwa_index

    conf['threads'] = parsed_args.threads
    conf['do_duplicates'] = parsed_args.do_duplicates
    conf['do_downgrade_edges'] = parsed_args.do_downgrade_edges
    conf['filter_supplementary'] = parsed_args.filter_supplementary
    if parsed_args.do_downgrade_edges:
        start, end = parsed_args.downgrade_edges_conf
        downgrade_edges_conf = {'read_start_size': start, 'read_end_size': end}
        conf['downgrade_edges_conf'] = downgrade_edges_conf

    return conf


def main():
    parser = _setup_argparse()
    conf = _parse_args(parser)
    log_fhand = sys.stdout
    conf['log_fhand'] = log_fhand
    result = map_mp_bwamem(conf)
    if result['fail'] == True:
        log_fhand.write(result['error_msg'] + '\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
