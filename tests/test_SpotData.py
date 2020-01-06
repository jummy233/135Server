from typing import Optional
import unittest
from dataGetter import dataMidware
import time


class SpotDataTest(unittest.TestCase):
    def setUp(self):
        self.j = dataMidware.JianYanYuanData()
        self.location_attrs = (
            'cityIdLogin',
            'provinceIdLogin',
            'nickname',
            'address',
            'provinceLoginName',
            'cityLoginName',
            'location')

    def test_JianyanyuanConstructor(self):
        token1 = self.j.token
        time.sleep(21)
        token2 = self.j.token
        self.assertTrue(token1 != token2)

    def test_spot_location(self):
        g = self.j.spot_location()
        self.assertTrue(any(g))  # not all None

    def test_filter_attrs(self):
        d = self.j._filter_location_attrs(
            self.j.device_list[5], self.location_attrs)
        self.assertTrue(d is not None and len(d.keys()) <= len(self.location_attrs))

    def test_make_datapoint_param(self):
        r = self.j.device_list[8]
        param = self.j._make_datapoint_param(r)
        self.assertTrue(param is not None and 'gid' in param.keys())

