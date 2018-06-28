from pysam import index, AlignmentFile
from array import array
from tempfile import NamedTemporaryFile
import subprocess
from subprocess import CalledProcessError
import shutil

LEFT_DOWNGRADED_TAG = 'dl'
RIGTH_DOWNGRADED_TAG = 'dr'
QUAL_TO_SUBSTRACT = 60


def index_bam(path):
    'It indexes a bam file'
    index(str(path))


def downgrade_read_edges(in_fpath, out_fpath, read_start_size, read_end_size,
                         qual_to_substract=QUAL_TO_SUBSTRACT):
    in_sam = AlignmentFile(in_fpath)
    out_sam = AlignmentFile(out_fpath, 'wb', template=in_sam)
    for aligned_read in in_sam:
        if (aligned_read.has_tag(LEFT_DOWNGRADED_TAG) or
                aligned_read.has_tag(RIGTH_DOWNGRADED_TAG)):
            raise RuntimeError('Edge qualities already downgraded\n')

        _downgrade_edge_qualities(aligned_read, read_start_size, read_end_size,
                                  qual_to_substract=qual_to_substract)
        out_sam.write(aligned_read)


def _downgrade_edge_qualities(aligned_read, read_start_size, read_end_size,
                              qual_to_substract):
    is_reversed = bool(aligned_read.flag & 16)
    if is_reversed:
        right_limit = aligned_read.qstart + read_start_size
        left_limit = aligned_read.qend - read_end_size
    else:
        left_limit = aligned_read.qstart + read_start_size
        right_limit = aligned_read.qend - read_end_size
    quals = list(aligned_read.query_qualities)

    if left_limit >= right_limit:
        right_limit = left_limit + 1

    left_quals = quals[:left_limit]
    right_quals = quals[right_limit:]

    def minus(qual):
        qual -= qual_to_substract
        if qual < 0:
            qual = 0
        return qual

    downgraded_left_quals = list(map(minus, left_quals))
    downgraded_right_quals = list(map(minus, right_quals))

    new_quals = downgraded_left_quals
    new_quals.extend(quals[left_limit:right_limit])
    new_quals.extend(downgraded_right_quals)
    try:
        assert len(quals) == len(new_quals)
    except AssertionError:
        print(left_limit, right_limit)
        print(left_quals, downgraded_left_quals)
        print(right_quals, downgraded_right_quals)
        raise
    aligned_read.query_qualities = array('B', new_quals)

    def to_sanger_qual(quals):
        return ''.join(chr(33 + qual) for qual in quals)

    aligned_read.set_tag(LEFT_DOWNGRADED_TAG, to_sanger_qual(left_quals),
                         value_type='Z')
    aligned_read.set_tag(RIGTH_DOWNGRADED_TAG, to_sanger_qual(right_quals),
                         value_type='Z')


def _restore_qual_from_tag(aligned_read):

    def to_phred_qual(quals):
        return [ord(qual) - 33 for qual in quals]

    left_quals, rigth_quals = [], []
    if aligned_read.has_tag(LEFT_DOWNGRADED_TAG):
        left_quals = aligned_read.get_tag(LEFT_DOWNGRADED_TAG)
        left_quals = to_phred_qual(left_quals)
    if aligned_read.has_tag(RIGTH_DOWNGRADED_TAG):
        rigth_quals = aligned_read.get_tag(RIGTH_DOWNGRADED_TAG)
        rigth_quals = to_phred_qual(rigth_quals)

    if left_quals or rigth_quals:
        recover_qual = left_quals
        left_limit = len(left_quals)
        rigth_limit = -len(rigth_quals) if len(rigth_quals) else None
        recover_qual += aligned_read.query_qualities[left_limit:rigth_limit]
        recover_qual += rigth_quals
        aligned_read.query_qualities = array('B', recover_qual)


def mark_duplicates(in_fpath, out_fpath=None, tmp_dir=None, metric_fpath=None,
                    stderr_fhand=None):
    if out_fpath is None:
        out_fpath = in_fpath

    if out_fpath == in_fpath:
        mark_dup_fhand = NamedTemporaryFile(suffix='.mark_dup.bam',
                                            delete=False, dir=tmp_dir)
        temp_out_fpath = mark_dup_fhand.name
    else:
        temp_out_fpath = out_fpath

    failed = _mark_duplicates(in_fpath, temp_out_fpath, metric_fpath,
                              stderr_fhand=stderr_fhand)

    if failed:
        msg = 'Mark duplicate process failed, for {}'
        raise RuntimeError(msg.format(in_fpath))

    if temp_out_fpath != out_fpath:
        shutil.move(temp_out_fpath, out_fpath)


def _mark_duplicates(in_fpath, out_fpath, metric_fpath, stderr_fhand):
    if metric_fpath is None:
        metric_fpath = '/dev/null'

    cmd = ['picard-tools', 'MarkDuplicates', 'VALIDATION_STRINGENCY=LENIENT',
           'M={}'.format(metric_fpath), 'INPUT={}'.format(in_fpath),
           'OUTPUT={}'.format(out_fpath)]
    failed = False
    try:
        subprocess.run(cmd, stderr=stderr_fhand, stdout=stderr_fhand)
    except CalledProcessError:
        failed = True
    return failed
