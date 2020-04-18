from typing import Optional
import unittest
from app.dataGetter.apis import jianyanyuanGetter as j
from app.dataGetter import authConfig
import time
import json
jauth = authConfig.jauth


class JianyanyuanGetterTest(unittest.TestCase):
    def setUp(self):
        self.token = j._get_token(jauth)

    def test_get_token(self):
        token = j._get_token(jauth)
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

        data = [
            {
                'gid': 'uarlid',  # 3.temp 4.hum
                'data': j._get_device_attrs(jauth, self.token, 'uarlid')},
            {
                'gid': 'rkrbhj',  # 155.ac_power
                'data': j._get_device_attrs(jauth, self.token, 'rkrbhj')},
            {
                'gid': 'kcdamh',  # 3.temp 4.hum 2.co2 1.pm25
                'data': j._get_device_attrs(jauth, self.token, 'kcdamh')},
            {
                'gid': 'ndbayo',  # 3.temp 4.hum
                'data': j._get_device_attrs(jauth, self.token, 'ndbayo')},
            {
                'gid': 'usliid',  # 1.pm25 2.co2 3.temp 4.hum
                'data': j._get_device_attrs(jauth, self.token, 'usliid')},
            {
                'gid': 'jpotmu',  # None
                'data': j._get_device_attrs(jauth, self.token, 'jpotmu')},
            {
                'gid': 'rzcucq',  # None
                'data': j._get_device_attrs(jauth, self.token, 'rzcucq')},
            {
                'gid': 'cpvfxc',  # 1.pm25 2.co2 3.Temp 4.hum 5.
                'data': j._get_device_attrs(jauth, self.token, 'cpvfxc')},
            {
                'gid': 'qvrmlp',  # 3.temp 4.hum
                'data': j._get_device_attrs(jauth, self.token, 'qvrmlp')},
            {
                'gid': 'ghaqam',  # 32.ac_power
                'data': j._get_device_attrs(jauth, self.token, 'ghaqam')},
            {
                'gid': 'qqyffg',  # 3.temp 4.hum 5.
                'data': j._get_device_attrs(jauth, self.token, 'qqyffg')},
            {
                'gid': 'sougci',  # 32 power
                'data': j._get_device_attrs(jauth, self.token, 'sougci')}
        ]
        with open('app/dataGetter/static/j_device_attrs.json', 'w') as f:
            f.write(json.dumps(data))

        expected_len = [6, 9, 26, 6, 24, 101, 67, 22, 6, 5, 6, 5]
        self.assertTrue(len(expected_len) == len(data) and
                        all(map(len, (d['data'] for d in data))))

    def test_get_datapoint(self):
        params: j.DataPointParam = (
            {'gid': 'uarlid',
             'did': '20205754003878404097',
             'aid': "3,4",
             'startTime': '2019-07-23T00:00:00',
             'endTime': '2019-07-24T00:00:00'})
        data = j._get_data_points(jauth, self.token, params)
        self.assertTrue(data[0]['as']['4'] == 46.0)


