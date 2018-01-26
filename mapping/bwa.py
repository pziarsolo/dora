import sys
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import gettempdir, NamedTemporaryFile

from mapping.bam import mark_duplicates, downgrade_read_edges, index_bam
from mapping.utils import (get_num_threads, map_process_to_sortedbam,
                           remove_fhand)


def map_mp_bwamem(conf):
    sample = conf.get('sample')
    library = conf.get('library', sample)
    read1_path = Path(conf.get('read1_fpath'))
    read2_path = conf.get('read2_fpath', None)
    if read2_path:
        read2_path = Path(read2_path)
    out_path = Path(conf.get('out_fpath'))
    bwa_index = conf.get('index')
    tempdir = conf.get('tmpdir', gettempdir)
    threads = get_num_threads(conf.get('threads', None))
    interleave = conf.get('interleave', False)
    do_duplicates = conf('do_duplicates', False)
    do_downgrade_edges = conf('do_downgrade_edge', True)

    if not read1_path.exists:
        msg = '{}: reads not available\n'.format(library)
        sys.stdout.write(msg)
        return {'fail': True, 'sample': library, 'error_msg': msg}

    if out_path.exists:
        msg = '{} already mapped\n'.format(out_path)
        sys.stdout.write(msg)
        return {'fail': True, 'sample': sample, 'error_msg': msg}

    readgroup = {'ID': library, 'LB': library, 'SM': sample,
                 'PL': 'illumina'}

    stderr_fhand = open(str(out_path.with_suffix('.stderr')), 'w')
    bwa_conf = {'bwa_index': bwa_index, 'threads': threads,
                'readgroup': readgroup, 'log_fhand': stderr_fhand}
    if read2_path.exists:
        bwa_conf['paired_paths'] = [read1_path, read2_path]
    elif interleave:
        bwa_conf['interleave_path'] = read1_path
    else:
        bwa_conf['unpaired_path'] = read1_path

    downgrade_edges_out_is_tmp = True
    duplicates_out_is_tmp = True
    map_out_is_tmp = True

    if do_downgrade_edges:
        downgrade_edges_out_is_tmp = False
    elif do_duplicates:
        duplicates_out_is_tmp = True
    else:
        map_out_is_tmp = True

    if map_out_is_tmp:
        bam_fhand = NamedTemporaryFile(suffix='.bam', dir=tempdir)
    else:
        bam_fhand = open(out_path, 'w')
    bwa_process = map_with_bwamem(**bwa_conf)
    try:
        map_process_to_sortedbam(bwa_process, bam_fhand.name,
                                 stderr_fhand=stderr_fhand,
                                 tempdir=tempdir)
    except RuntimeError:
        msg = '{}: error mapping\n'.format(sample)
        sys.stderr.write(msg)
        remove_fhand(bam_fhand)
        return True, sample, msg

    out_fhand = bam_fhand

    if do_duplicates:
        if duplicates_out_is_tmp:
            dup_fhand = NamedTemporaryFile(suffix='.bam', dir=tempdir)
        else:
            dup_fhand = open(out_path, 'w')
        try:
            mark_duplicates(out_fhand.name, dup_fhand.name, stderr_fhand=stderr_fhand)
        except RuntimeError:
            msg = '{}: error marking duplicates\n'.format(sample)
            sys.stderr.write(msg)
            remove_fhand(bam_fhand)
            remove_fhand(dup_fhand)
            return {'fail': True, 'sample': library, 'error_msg': msg}
    out_fhand = dup_fhand

    if do_downgrade_edges:
        if downgrade_edges_out_is_tmp:
            downgrade_fhand = NamedTemporaryFile(suffix='.bam', dir=tempdir)
        else:
            downgrade_fhand = open(out_path, 'w')
        downgrade_read_edges(out_fhand.name, downgrade_fhand.name, 3)

    out_fhand = downgrade_fhand

    index_bam(out_fhand.name)
    stderr_fhand.close()
    for fhand in [bam_fhand, dup_fhand, downgrade_fhand]:
        if fhand.name != out_fhand.name:
            remove_fhand(fhand)

    return {'fail': False, 'sample': library, 'error_msg': 'OK'}


def map_with_bwamem(index_fpath, unpaired_fpath=None, paired_fpaths=None,
                    interleave_fpath=None, threads=None, log_fhand=None,
                    extra_params=None, readgroup=None):
    'It maps with bwa mem algorithm'
    interleave = False
    num_called_fpaths = 0
    in_paths = []
    if unpaired_fpath is not None:
        num_called_fpaths += 1
        in_paths.append(unpaired_fpath)
    if paired_fpaths is not None:
        num_called_fpaths += 1
        in_paths.extend(paired_fpaths)
    if interleave_fpath is not None:
        num_called_fpaths += 1
        in_paths.append(interleave_fpath)
        interleave = True

    if num_called_fpaths == 0:
        raise RuntimeError('At least one file to map is required')
    if num_called_fpaths > 1:
        msg = 'Bwa can not map unpaired and unpaired reads together'
        raise RuntimeError(msg)

    if extra_params is None:
        extra_params = []

    if '-p' in extra_params:
        extra_params.remove('-p')

    if interleave:
        extra_params.append('-p')

    if readgroup is not None:
        rg_str = r"@RG\tID:{ID}\tSM:{SM}\tPL:{PL}\tLB:{LB}".format(**readgroup)
        extra_params.extend(['-R', rg_str])

    binary = 'bwa'
    cmd = [binary, 'mem', '-t', str(get_num_threads(threads)), index_fpath]
    cmd.extend(extra_params)
    cmd.extend(map(str, in_paths))

    bwa = Popen(cmd, stderr=log_fhand, stdout=PIPE)
    return bwa
