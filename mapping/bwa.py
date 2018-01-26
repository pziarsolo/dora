import sys
from pathlib import Path
from subprocess import PIPE, Popen, run
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
    tempdir = conf.get('tmpdir', gettempdir())
    threads = get_num_threads(conf.get('threads', None))
    interleave = conf.get('interleave', False)
    do_duplicates = conf.get('do_duplicates', False)
    do_downgrade_edges = conf.get('do_downgrade_edge', True)

    if not read1_path.exists():
        msg = '{}: reads not available\n'.format(library)
        sys.stdout.write(msg)
        return {'fail': True, 'sample': library, 'error_msg': msg}

    if out_path.exists():
        msg = '{} already mapped\n'.format(out_path)
        sys.stdout.write(msg)
        return {'fail': True, 'sample': sample, 'error_msg': msg}

    readgroup = {'ID': library, 'LB': library, 'SM': sample,
                 'PL': 'illumina'}

    stderr_fhand = open(str(out_path.with_suffix('.stderr')), 'w')
    bwa_conf = {'index_fpath': bwa_index, 'threads': threads,
                'readgroup': readgroup, 'log_fhand': stderr_fhand}
    if read2_path and read2_path.exists():
        bwa_conf['paired_paths'] = [read1_path, read2_path]
    elif interleave:
        bwa_conf['interleave_path'] = read1_path
    else:
        bwa_conf['unpaired_path'] = read1_path

    duplicates_out_is_tmp = True
    map_out_is_tmp = True
    used_fhands = []

    if not do_downgrade_edges and do_duplicates:
        duplicates_out_is_tmp = False
    elif not do_downgrade_edges and not do_duplicates:
        map_out_is_tmp = False

    if map_out_is_tmp:
        bam_fhand = NamedTemporaryFile(suffix='.bwa.bam', dir=tempdir)
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
    finally:
        bwa_process.wait()
    out_fhand = bam_fhand

    used_fhands.append(bam_fhand)

    if do_duplicates:
        if duplicates_out_is_tmp:
            dup_fhand = NamedTemporaryFile(suffix='.dup.bam', dir=tempdir)
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
        used_fhands.append(dup_fhand)

    if do_downgrade_edges:
        downgrade_fhand = open(out_path, 'w')
        downgrade_read_edges(out_fhand.name, downgrade_fhand.name, 3)

        out_fhand = downgrade_fhand
        used_fhands.append(downgrade_fhand)

    index_bam(out_fhand.name)
    stderr_fhand.close()
    for fhand in used_fhands:
        if fhand.name != out_fhand.name:
            remove_fhand(fhand)
        else:
            fhand.close()

    return {'fail': False, 'sample': library, 'error_msg': 'OK'}


def map_with_bwamem(index_fpath, unpaired_path=None, paired_paths=None,
                    interleave_path=None, threads=None, log_fhand=None,
                    extra_params=None, readgroup=None):
    'It maps with bwa mem algorithm'
    interleave = False
    num_called_fpaths = 0
    in_paths = []
    if unpaired_path is not None:
        num_called_fpaths += 1
        in_paths.append(unpaired_path)
    if paired_paths is not None:
        num_called_fpaths += 1
        in_paths.extend(paired_paths)
    if interleave_path is not None:
        num_called_fpaths += 1
        in_paths.append(interleave_path)
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
#     print(' '.join(cmd))
    bwa = Popen(cmd, stderr=log_fhand, stdout=PIPE)
    return bwa
