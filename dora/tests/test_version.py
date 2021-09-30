import unittest

import dora
from dora import VersionManager


class VersionTest(unittest.TestCase):
    def test_get_version(self):
        vm = VersionManager()
        self.assertIsInstance(vm.get_file_version(), str)
        self.assertEqual(vm.get_file_version(), dora.__version__)


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Bowtie2Test.test_map_with_bowtie2']
    unittest.main()
