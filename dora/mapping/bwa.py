from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import gettempdir, NamedTemporaryFile

from dora.mapping.bam import (mark_duplicates, downgrade_read_edges, index_bam,
                              filter_bam_by_flagstat)
from dora.mapping.utils import (get_num_threads, map_process_to_sortedbam,
                                remove_fhand)


def map_mp_bwamem(conf):
    sample = conf.get('sample')
    bwa_extra_paramas = conf.get('bwa_params', [])
    library = conf.get('library', sample)
    read_group = conf.get('read_group', library)
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
    do_downgrade_edges = conf.get('do_downgrade_edges', True)
    downgrade_edges_conf = conf.get('downgrade_edges_conf', None)
    do_csi_index = conf.get('do_csi_index', False)
    log_fhand = conf.get('log_fhand', None)
    filter_supplementary = conf.get('filter_supplementary', False)

    if log_fhand is None:
        log_fhand = open(str(out_path.with_suffix('.stderr')), 'w')
    Path(tempdir).mkdir(exist_ok=True)

    if not read1_path.exists():
        msg = '{}: reads not available'.format(read_group)
        # sys.stdout.write(msg)
        return {'fail': True, 'sample': read_group, 'error_msg': msg}

    if out_path.exists():
        msg = '{} already mapped'.format(out_path)
        # sys.stdout.write(msg)
        return {'fail': True, 'sample': read_group, 'error_msg': msg}

    readgroup = {'ID': read_group, 'LB': library, 'SM': sample,
                 'PL': 'illumina'}


    bwa_conf = {'index_fpath': bwa_index, 'threads': threads,
                'readgroup': readgroup, 'log_fhand': log_fhand}
    if read2_path and read2_path.exists():
        bwa_conf['paired_paths'] = [read1_path, read2_path]
    elif interleave:
        bwa_conf['interleave_path'] = read1_path
    else:
        bwa_conf['unpaired_path'] = read1_path


    used_fhands = []
    final_analysis = None

    if do_downgrade_edges:
        final_analysis = 'downgrade_edges'
    elif not do_downgrade_edges and do_duplicates:
        final_analysis = 'duplicates'
    elif not do_downgrade_edges and not do_duplicates and filter_supplementary:
        final_analysis = 'filter_supplementary'
    else:
        final_analysis = 'mapping'

    if final_analysis != 'mapping':
        bam_fhand = NamedTemporaryFile(suffix='.bwa.bam', dir=tempdir)
    else:
        bam_fhand = out_path.open('w')
    bwa_process = map_with_bwamem(**bwa_conf)
    try:
        map_process_to_sortedbam(bwa_process, bam_fhand.name,
                                 stderr_fhand=log_fhand,
                                 tempdir=tempdir)
    except RuntimeError:
        msg = '{}: error mapping'.format(library)
        # sys.stderr.write(msg)
        remove_fhand(bam_fhand)
        return {'fail': True, 'sample': read_group, 'error_msg': msg}
    finally:
        bwa_process.wait()
    out_fhand = bam_fhand

    used_fhands.append(bam_fhand)

    if filter_supplementary:
        if final_analysis != 'filter_supplementary':
            supplememtary_fhand = NamedTemporaryFile(suffix='.supplementary.bam', dir=tempdir)
        else:
            supplememtary_fhand = out_path.open('w')
        flag = '2048'
        try:
            filter_bam_by_flagstat(out_fhand.name, flag,
                                   out_fpath=supplememtary_fhand.name, tmp_dir=None,
                                   stderr_fhand=log_fhand)
        except Exception as error:
            print(error)
            raise
        out_fhand = supplememtary_fhand
        used_fhands.append(supplememtary_fhand)


    if do_duplicates:
        if final_analysis != 'duplicates':
            dup_fhand = NamedTemporaryFile(suffix='.dup.bam', dir=tempdir)
        else:
            dup_fhand = out_path.open('w')
        try:
            mark_duplicates(out_fhand.name, dup_fhand.name, stderr_fhand=log_fhand)
        except RuntimeError:
            msg = '{}: error marking duplicates\n'.format(sample)
            # sys.stderr.write(msg)
            remove_fhand(bam_fhand)
            remove_fhand(dup_fhand)
            return {'fail': True, 'sample': read_group, 'error_msg': msg}
        out_fhand = dup_fhand
        used_fhands.append(dup_fhand)

    if do_downgrade_edges:
        downgrade_fhand = out_path.open('w')
        if downgrade_edges_conf is None:
            downgrade_edges_conf = {}
        downgrade_read_edges(out_fhand.name, downgrade_fhand.name,
                             **downgrade_edges_conf)

        out_fhand = downgrade_fhand
        used_fhands.append(downgrade_fhand)

    index_bam(out_fhand.name, do_csi_index=do_csi_index)
    log_fhand.close()
    for fhand in used_fhands:
        if fhand.name != out_fhand.name:
            remove_fhand(fhand)
        else:
            fhand.close()

    return {'fail': False, 'sample': read_group, 'error_msg': 'OK'}


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
