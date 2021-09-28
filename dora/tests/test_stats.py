import random
import unittest
import numpy as np
class StatsTest(unittest.TestCase):

    def test_coveage_stats(self):
        np_a = np.array([random.randint(1, 1000) for _ in range(100)])
        print(np_a)
        print(np.mean(np_a))
        print(np.median(np_a))
        print(np.average(np_a))


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Bowtie2Test.test_map_with_bowtie2']
    unittest.main()
