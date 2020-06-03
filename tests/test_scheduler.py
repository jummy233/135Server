from unittest import TestCase
from unittest import skip
import app.dataGetter.dataloader.Scheduler as S
from app.dataGetter.dataGen import JianYanYuanData
from datetime import datetime as dt
from datetime import timedelta
import tempfile
import os
import app
from app import db, scheduler
from threading import enumerate


class TestFetchActor(TestCase):
    """
    To fetch device it must exist in the db first.
    """

    def setUp(self):
        self.app = app.create_app('testing')
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            scheduler.update_device()
            scheduler.close()  # don't use the scheduler.
            self.actor = S.FetchActor(app, JianYanYuanData(app))
            self.actor.start()

    @skip("works")
    def test_update_device(self):
        """ should show total 332 devices """
        with self.app.app_context():
            from app.models import Device
            self.assertTrue(Device.query.filter(
                Device.device_name.like("%lumi%")).count() > 0)
            self.assertTrue(Device.query.filter(
                Device.device_name.like("%2009%")).count() > 0)
            self.assertTrue(Device.query.count() > 300)

    # def test_send(self):
    #     trange = (dt(2020, 3, 12, 12), dt(2002, 3, 12, 13))
    #     self.actor.send((2, trange))
    #     with self.app.app_context():
    #         from app.models import SpotRecord
    #         print("+++", SpotRecord.query.all())

    # def test_nonblocking(self):
    #     ...

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.actor.close()
