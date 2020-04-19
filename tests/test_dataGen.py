import unittest
import app.dataGetter.dataGen as DG
import app.dataGetter.dataGen.jianyanyuanData as jianyanyuanData
from app import create_app, db
from app.dataGetter.apis import jianyanyuanGetter
from timeutils.time import str_to_datetime
from datetime import datetime
from datetime import timedelta
from typing import Dict, List, Iterator, Generator, Optional
from itertools import islice
from tests.fake_db import gen_fake
import logging
import json

logging.basicConfig(level=logging.WARNING)


class TestdataGenJianYanYuanData(unittest.TestCase):
    daterange = (datetime.now() - timedelta(days=2),
                 datetime.now() - timedelta(days=1))

    device_result = json.loads("""
    {   "deviceId": "20111863847736381446",
        "deviceName": "Device",
        "companyId": "HKZ",
        "productId": "001",
        "modelId": "COP",
        "gid": "NDBAYo",
        "type": 1,
        "isPublic": false,
        "online": 0,
        "status": 1,
        "createTime": "2019-08-06T15:19:02",
        "companyName": "C1",
        "productName": "pp",
        "modelName": "ESIC-SN01",
        "uidsNum": 0,
        "busModelId": 2,
        "public": false }
    """)

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.j = DG.JianYanYuanData(self.app)
        db.create_all()
        gen_fake()

    def tearDown(self):
        self.j.close()
        db.drop_all()
        self.app_context.pop()

    def test_JianYanYuanData_make_spot_record(self):
        # range test.
        param = {'gid': 'cpvfxc',
                 'did': '20180624033015488513',
                 'aid': '1,2,3,4,32,155',
                 'startTime': '2020-04-17T17:48:15',
                 'endTime': '2020-04-18T17:48:15'}

        datapoint = {'as': {'4': 73.0, '1': 23.0, '3': 21.32},
                     'key': '2020-04-18T17:59:46'}

        result = {'spot_record_time': datetime(2020, 4, 18, 17, 59, 46),
                  'device_name': '20180624033015488513',
                  'temperature': 21.32,
                  'humidity': 73.0, 'pm25': 23.0,
                  'co2': None,
                  'window_opened': None,
                  'ac_power': None}

        sr = (jianyanyuanData
              .MakeDict
              .make_spot_record(datapoint, param))

        self.assertTrue(result == sr)

    def test_JianYanYuanData_make_spot(self):
        location = jianyanyuanData.MakeDict.make_location(self.device_result)
        spot = jianyanyuanData.MakeDict.make_spot(location)
        self.assertTrue("project_name" in spot.keys())

    def test_JianYanYuanData_make_device(self):
        device_result = self.device_result
        __import__('pdb').set_trace()
        device = jianyanyuanData.MakeDict.make_device(device_result)
        self.assertTrue(
            device_result.get("deviceId") == device.get("device_name")
            and device_result.get("productName") == device.get("device_type")
            and str_to_datetime(device_result.get("createTime"))
            == device.get("create_time"))

    def test_JianYanYuanData_device(self):
        devices = self.j.device()
        self.assertTrue(isinstance(devices, Iterator)
                and )

    def test_JianYanYuanData_make_location(self):
        location = jianyanyuanData.MakeDict.make_location(self.device_result)
        self.assertTrue(isinstance(location, Dict)
                        and "province" in location.keys())

    def test_JianYanYuanData_spot(self):
        spot = self.j.spot()
        # for n in spot:
        #     print(n)

    def test_JianYanYuanData_spot_record(self):
        spot_records = self.j.spot_record(49)
        slice_spot_record = islice(spot_records, 3, 5)

        self.assertTrue(isinstance(slice_spot_record, Iterator) and
                        isinstance(next(slice_spot_record), Generator))


@unittest.skip('skip')
class TestdataGen_XiaomiData(unittest.TestCase):
    pass
