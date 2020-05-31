import unittest
import app.dataGetter.dataGen as DG
import app.dataGetter.dataGen.jianyanyuanData as jianyanyuanData
from app import create_app, db
from app.modelOperations import commit
from app.dataGetter.apis import jianyanyuanGetter
import db_init
from datetime import datetime
from datetime import timedelta
from typing import Dict, List, Iterator, Generator, Optional
from itertools import islice
from tests.fake_db import gen_fake
import logging
import json

logging.basicConfig(level=logging.WARNING)


class TestdataGenJianYanYuanDataStatic(unittest.TestCase):
    """
    Static method test
    """
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
        device = jianyanyuanData.MakeDict.make_device(device_result)

        self.assertTrue(device_result.get("deviceId")
                        == device.get("device_name"))
        self.assertTrue(device_result.get("productName")
                        == device.get("device_type"))
        self.assertTrue(device_result.get("createTime")
                        == device.get("create_time"))

    def test_JianYanYuanData_make_location(self):
        location = jianyanyuanData.MakeDict.make_location(self.device_result)
        self.assertTrue(isinstance(location, Dict)
                        and "province" in location.keys())


class TestdataGenJianYanYuanDataState(unittest.TestCase):
    """
    Statful method test
    """

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.j = DG.JianYanYuanData(self.app)
        db.create_all()
        db_init.create_db("testing.sqlite")
        db_init.load_climate_area()
        db_init.load_location()
        gen_fake()

    def tearDown(self):
        self.j.close()
        db.drop_all()
        self.app_context.pop()

    def test_JianYanYuanData_device(self):
        devices = self.j.device()
        self.assertTrue(isinstance(devices, Iterator)
                        and next(devices).get("device_name") is not None)

    def test_JianYanYuanData_spot(self):
        spot = next(self.j.spot())
        # all entry should be None
        # because the API doesn't provides enough
        # information.
        self.assertTrue(spot == {
            "spot_name": None,
            "project_name": None,
            "spot_type": None})

    def test_JianYanYuanData_spot_record(self):
        spot_records = self.j.spot_record(49)
        sr = spot_records

        self.assertTrue(isinstance(sr, Iterator))


@unittest.skip('skip')
class TestdataGen_XiaomiData(unittest.TestCase):
    pass
