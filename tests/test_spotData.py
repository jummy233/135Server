"""
NOTE: The  test assume scheduler.update_device() is executed.
"""

import unittest
import app.dataGetter.dataGen as DG
from itertools import islice
from app import create_app, db, scheduler
import time
from datetime import datetime
from tests.fake_db import gen_fake
import threading
from multiprocessing import Pool
from app.dataGetter.dataGen.dataType import (
    thunk_iter, device_check, DataSource, WrongDidException)
from app.modelcoro import record_send


class JianyanyuanSpotDataTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        with self.app.app_context():
            # db.drop_all()
            db.create_all()
            scheduler.update_device()
            self.j = scheduler.update_actor.jianyanyuan_actor.datagen

        self.location_attrs = (
            'cityIdLogin',
            'provinceIdLogin',
            'nickname',
            'address',
            'provinceLoginName',
            'cityLoginName',
            'location')

    @unittest.skip('.')
    def test_JianyanyuanConstructor(self):
        token1 = self.j.token
        time.sleep(21)
        token2 = self.j.token
        self.assertTrue(token1 != token2)

    @unittest.skip('.')
    def test_device(self):
        devices = list(self.j.device())
        self.assertTrue(len(devices) > 100)
        dname: str = devices[-1].get("device_name")
        self.assertTrue(dname.isdigit())
        try:
            device_check(dname, DataSource.XIAOMI)
        except WrongDidException:
            self.fail("device name format is incorrect")

    @unittest.skip('.')
    def test_sport_record(self):
        """
        use the device 20205754003878404097
        """
        with self.app.app_context():
            from app.models import Device
            did: int = (
                Device
                .query
                .filter(Device.device_name == "20205754003878404097")
            ).first().device_id

        time_range = (datetime(2019, 9, 23, 00), datetime(2019, 9, 24, 00))
        records = self.j.spot_record(did, time_range)

        # NEED a property test all the way to database commit.
        with self.app.app_context():
            from app.modelOperations import ModelOperations, commit

            def worker(record):
                ModelOperations.Add.add_spot_record(record)

            for i in thunk_iter(records):
                print(i)
                worker(i)
            commit()

    def test_moco(self):
        from app.modelOperations import commit
        with self.app.app_context():
            from app.models import Device
            did: int = (
                Device
                .query
                .filter(Device.device_name == "20205754003878404097")
            ).first().device_id

        time_range = (datetime(2019, 9, 23, 00), datetime(2019, 9, 24, 00))
        records = self.j.spot_record(did, time_range)

        with self.app.app_context():

            for i in thunk_iter(records):
                print(i)
                record_send(i)
            commit()

    def tearDown(self):
        self.j.close()
        del self.j


@unittest.skip('.')
class XiaomiSpotDataTest(unittest.TestCase):
    """ xiaomi doesn't need location data """

    def setUp(self):
        self.app = create_app('testing')
        with self.app.app_context():
            # db.drop_all()
            self.x = scheduler.update_actor.xiaomi_actor.datagen
            db.create_all()

    @unittest.skip('.')
    def test_device(self):
        devices = list(self.x.device())
        self.assertTrue(len(devices) > 100)
        dname: str = devices[-1].get("device_name")
        try:
            device_check(dname, DataSource.XIAOMI)
        except WrongDidException:
            self.fail("device name format is incorrect")

    @unittest.skip('.')
    def test_sport_record(self):
        with self.app.app_context():
            from app.models import Device
            did: int = (
                Device
                .query
                .filter(Device.device_name == "lumi.158d0001fd5c50")
            ).first().device_id
            print(did)

        time_range = (datetime(2020, 6, 5, 16), datetime(2020, 6, 6, 18))
        records = self.x.spot_record(did, time_range)

        # NEED a property test all the way to database commit.
        with self.app.app_context():
            from app.modelOperations import ModelOperations, commit

            def worker(record):
                ModelOperations.Add.add_spot_record(record)

            it = thunk_iter(records)
            for i in it:
                worker(i)
            commit()

    def tearDown(self):
        self.x.close()
        del self.x
