
import os
from pathlib import Path
import unittest
import mapping
from tempfile import NamedTemporaryFile, gettempdir
from subprocess import run, PIPE

from mapping.bwa import map_with_bwamem, map_mp_bwamem
from mapping.utils import map_process_to_sortedbam

TEST_DATA_PATHDIR = Path(mapping.__file__).parent.parent.joinpath('test').joinpath('data')


class BwaTest(unittest.TestCase):

    def test_map_with_bwa(self):
        index_fpath = str(TEST_DATA_PATHDIR.joinpath('arabidopsis_genes'))
        reads_path = TEST_DATA_PATHDIR.joinpath('arabidopsis_reads.fastq')
        with NamedTemporaryFile(suffix='.bam') as bam_fhand, open(os.devnull, 'w') as devnull:
            bwa = map_with_bwamem(index_fpath, unpaired_path=reads_path,
                                  log_fhand=devnull)
            map_process_to_sortedbam(bwa, bam_fhand.name, stderr_fhand=devnull)
            out = run(['samtools', 'view', bam_fhand.name], stdout=PIPE)
            assert b'TTCTGATTCAATCTACTTCAAAGTTGGCTTTATCAATAAG' in out.stdout
            bwa.wait()

    def test_complete_map_process(self):
        out_tmp_fpath = os.path.join(gettempdir(), 'asada.bam')
        try:
            conf = {}
            conf['index'] = str(TEST_DATA_PATHDIR.joinpath('arabidopsis_genes'))
            conf['read1_fpath'] = str(TEST_DATA_PATHDIR.joinpath('arabidopsis_reads.fastq'))
            conf['out_fpath'] = out_tmp_fpath
            conf['sample'] = 'test'
            conf['do_duplicates'] = True
            conf['do_downgrade_edges'] = False
            result = map_mp_bwamem(conf)
            assert result == {'fail': False, 'sample': 'test', 'error_msg': 'OK'}
            out = run(['samtools', 'view', '-h', out_tmp_fpath], stdout=PIPE)
            assert b'TTCTGATTCAATCTACTTCAAAGTTGGCTTTATCAATAAG' in out.stdout
        finally:
            if os.path.exists(out_tmp_fpath):
                os.remove(out_tmp_fpath)

    def test_complete_pair_map_process(self):
        out_tmp_fpath = os.path.join(gettempdir(), 'asada.bam')
        try:
            conf = {}
            conf['index'] = str(TEST_DATA_PATHDIR.joinpath('arabidopsis_genes'))
            conf['read1_fpath'] = str(TEST_DATA_PATHDIR.joinpath('arabreads_1.fastq'))
            conf['read2_fpath'] = str(TEST_DATA_PATHDIR.joinpath('arabreads_2.fastq'))
            conf['out_fpath'] = out_tmp_fpath
            conf['sample'] = 'test'
            conf['do_duplicates'] = False
            conf['do_downgrade_edges'] = False
            result = map_mp_bwamem(conf)
            assert result == {'fail': False, 'sample': 'test', 'error_msg': 'OK'}
            out = run(['samtools', 'view', '-h', out_tmp_fpath], stdout=PIPE)
            assert b'SQ\tSN:AT1G55265.1' in out.stdout
        finally:
            if os.path.exists(out_tmp_fpath):
                os.remove(out_tmp_fpath)

        out_tmp_fpath = os.path.join(gettempdir(), 'asada.bam')
        try:
            conf = {}
            conf['index'] = str(TEST_DATA_PATHDIR.joinpath('arabidopsis_genes'))
            conf['read1_fpath'] = str(TEST_DATA_PATHDIR.joinpath('arabreads_1.fastq'))
            conf['read2_fpath'] = str(TEST_DATA_PATHDIR.joinpath('arabreads_2.fastq'))
            conf['out_fpath'] = out_tmp_fpath
            conf['sample'] = 'test'
            conf['do_duplicates'] = False
            conf['do_downgrade_edges'] = False
            result = map_mp_bwamem(conf)
            assert result == {'fail': False, 'sample': 'test', 'error_msg': 'OK'}
            out = run(['samtools', 'view', '-h', out_tmp_fpath], stdout=PIPE)
            assert b'SQ\tSN:AT1G55265.1' in out.stdout
        finally:
            if os.path.exists(out_tmp_fpath):
                os.remove(out_tmp_fpath)


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Bowtie2Test.test_map_with_bowtie2']
    unittest.main()
