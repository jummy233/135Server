import unittest
from datetime import datetime as dt
from app import utils as u


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

    def test_normalize_time(self):
        time_paris = (
            (dt(2019, 1, 1, 1, 5), dt(2019, 1, 1, 1, 5)),
            (dt(2000, 12, 3, 4, 50), dt(2000, 12, 3, 4, 50)),
            (dt(2000, 4, 23, 12, 30), dt(2000, 4, 23, 12, 30)),
            (dt(2019, 1, 1, 1, 3), dt(2019, 1, 1, 1, 5)),
            (dt(1993, 4, 3, 1, 27), dt(1993, 4, 3, 1, 25)),
            (dt(1993, 4, 3, 1, 28), dt(1993, 4, 3, 1, 30)),
            (dt(1993, 4, 30, 23, 59), dt(1993, 5, 1, 0, 0)),
            (dt(2008, 8, 23, 4, 59), dt(2008, 8, 23, 5, 0))
        )

        res = map(lambda dp: u.normalize_time(5)(dp[0]) == dp[1], time_paris)
        # res = map(lambda dp: (u.normalize_time(5)(dp[0]), dp[1]), time_paris)
        # __import__('pprint').pprint(list(res))

        self.assertTrue(res)


