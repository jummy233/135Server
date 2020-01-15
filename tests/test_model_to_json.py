import unittest
from datetime import datetime
from app import create_app, db
from app import models as m
from app import modelOperations as mops
from .fake_db import gen_fake
import db_init


class TestModelToJson(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        db_init.create_db(name='testing.sqlite')
        m.User.gen_admin()
        db_init.load_climate_area()  # unfull init.

        gen_fake()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_project_to_json(self):
        print('<Project>')
        __import__('pprint').pprint(m.Project.query.first().to_json())
        print()

    def test_spot_to_json(self):
        print('<Spot>')
        __import__('pprint').pprint(m.Spot.query.first().to_json())
        print()

    def test_device_to_json(self):
        print('<Device>')
        __import__('pprint').pprint(m.Device.query.first().to_json())
        print()

    def test_user_to_json(self):
        print('<User>')
        __import__('pprint').pprint(m.User.query.first().to_json())
        print()

    def test_location_to_json(self):
        print('<Location>')
        __import__('pprint').pprint(m.Location.query.first().to_json())
        print()

    def test_spot_record_to_json(self):
        print('<SpotRecord>')
        __import__('pprint').pprint(m.SpotRecord.query.first().to_json())
        print()



