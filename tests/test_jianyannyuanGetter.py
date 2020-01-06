from typing import Optional
import unittest
from dataGetter import jianyanyuanGetter as j
from dataGetter import authConfig
from dataGetter import dataMidware
import time
jauth = authConfig.jauth


class JianyanyuanGetterTest(unittest.TestCase):
    def setUp(self):
        self.token = j._get_token(jauth)

    def test_get_token(self):
        token = j._get_token(jauth)
        # print(token)
        self.assertTrue(isinstance(token, tuple) and len(token) == 2)

    def test_get_device_list(self):
        params: j.DeviceParam = (
            {'companyId': 'HKZ',
             'start': 1,
             'size': 10,
             'pageNo': 1,
             'pageSize': '10'})
        data = j._get_device_list(jauth, self.token, params)
        # print(data['devs'][0]['deviceId'])
        # print(data)
        self.assertTrue(isinstance(data, list))

    def test_get_device_attrs(self):
        data = j._get_device_attrs(jauth, self.token, 'ofskcl')
        self.assertTrue(data[0]['deviceValueId'] == 33)

    def test_get_datapoint(self):
        params: j.DataPointParam = (
            {'gid': 'ofskcl',
             'did': '20227493777269940224',
             'aid': "33,104,121",
             'startTime': '2019-12-16T00:00:00',
             'endTime': '2019-12-17T00:00:00'})
        data = j._get_data_points(jauth, self.token, params)
        # print(data)
        self.assertTrue(data is not None)


