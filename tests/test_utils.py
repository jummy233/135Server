import unittest
from datetime import datetime as dt
import utils as u
from itertools import i


class TestUtils(unittest.TestCase):
    def test_is_nice_time(self):
        nice_time = (dt(2019, 1, 1, 1, 5),
                     dt(2019, 1, 1, 12, 30),
                     dt(1970, 12, 3, 23, 45))

        bad_time = (dt(2019, 1, 1, 2, 3),
                    dt(2000, 12, 3, 17, 1))

        nice_result = all(map(u.is_nice_time(5), nice_time))
        bad_result = not all(map(u.is_nice_time(5), bad_time))
        self.assertTrue(nice_result and bad_result)



