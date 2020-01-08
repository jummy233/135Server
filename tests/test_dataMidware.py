import unittest
from dataGetter import dataMidware
from dataGetter import jianyanyuanGetter
from datetime import datetime
from typing import Dict, List, Iterator, Generator
from itertools import islice


class TestdataMidware_JianYanYuanData(unittest.TestCase):
    def setUp(self):
        self.j = dataMidware.JianYanYuanData()

    def tearDown(self):
        self.j.close()

    def test_JianYanYuanData_make_spot_record(self):
        # range test.
        datapoint_params = map(
            self.j._make_datapoint_param, self.j.device_list[:10])
        datapoints = map(self.j._datapoint, datapoint_params)

        spot_records = map(
            lambda dp: None if not dp else self.j.make_spot_record(dp[0]), datapoints)

        # for sr in spot_records:
        #     __import__('pprint').pprint(sr)

        self.assertTrue(any(
            map(lambda sr: isinstance(sr['spot_record_time'], datetime)
                if isinstance(sr, Dict) else False,
                spot_records)))

    def test_JianYanYuanData_make_spot(self):
        locations = map(self.j.make_location, self.j.device_list)
        spot = map(self.j.make_spot, locations)
        self.assertTrue('project_name' in next(spot).keys())

    def test_JianYanYuanData_make_device(self):
        device_result = self.j.device_list[4]
        device = self.j.make_device(device_result)
        self.assertTrue(
            isinstance(device, Dict) and isinstance(device['device_name'], str))

    def test_JianYanYuanData_device(self):
        devices = self.j.device()
        # for n in devices:
        #     __import__('pprint').pprint(n)
        self.assertTrue(isinstance(devices, Iterator))

    def test_JianYanYuanData_make_location(self):
        location = self.j.make_location(self.j.device_list[0])
        self.assertTrue(isinstance(location, Dict))

    def test_JianYanYuanData_spot(self):
        spot = self.j.spot()
        for n in spot:
            print(n)

    def test_JianYanYuanData_spot_record(self):
        spot_records = self.j.spot_record()
        slice_spot_record = islice(spot_records, 3, 5)

        self.assertTrue(isinstance(slice_spot_record, Iterator) and
                        isinstance(next(slice_spot_record), Generator))


@unittest.skip('skip')
class TestdataMidware_XiaomiData(unittest.TestCase):
    pass
