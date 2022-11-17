#!/usr/bin/env python3
import sys
import os

from dora.mapping.utils import generate_bwa_confs_from_project, run_multiprocesses
from dora.mapping.bwa import map_mp_bwamem

MARK_DUPLICATES = None
DOWNGRADE_EDGES = None


def main():
    threads = 20
    processes = 6
    paired = True
    project_path = sys.argv[1]
    read_dir = os.path.join(project_path, 'reads/clean')
    out_dir = os.path.join(project_path, 'mapping/bams')
    tmp_dir = os.path.join(project_path, 'tmp')
    samples_path = os.path.join(project_path, 'samples.txt')
    pair_def_format = ''  # how are the pair formated _1 or _R1
    downgrade_edges_conf = {'read_start_size': 3, 'read_end_size': 3}
    bwa_index = '/home/jope/genomes/tomato/S_lycopersicum_chromosomes.2.50.fa'
    log_fhand = sys.stdout
    if MARK_DUPLICATES is None or DOWNGRADE_EDGES is None:
        raise ValueError('You have to set the MARK_DUPLICATES and DOWNGRADE EDGES')

    confs = generate_bwa_confs_from_project(samples_path, bwa_index,
                                            do_duplicates=MARK_DUPLICATES,
                                            do_downgrade_edges=DOWNGRADE_EDGES,
                                            tmp_dir=tmp_dir,
                                            read_dir=read_dir, threads=threads,
                                            downgrade_edges_conf=downgrade_edges_conf,
                                            out_dir=out_dir, paired=paired,
                                            pair_def_format=pair_def_format)
    run_multiprocesses(map_mp_bwamem, confs, processes, log_fhand)


if __name__ == '__main__':
    main()
