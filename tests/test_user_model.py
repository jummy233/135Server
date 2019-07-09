import unittest
import time
from datetime import datetime
from app import create_app, db
from app.models import User, Permission


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        User.gen_fake()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cons car cdr')
        self.assertTrue(u.passwd_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cons car cdr')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cons car cdr')
        self.assertTrue(u.verify_password('cons car cdr'))
        self.assertFalse(u.verify_password('lambda'))

    def test_password_salts_are_random(self):
        u = User(password='cons car cdr')
        v = User(password='cons car cdr')
        self.assertTrue(u.passwd_hash != v.passwd_hash)

    def test_permission(self):
        u = User(permission=1 << 2)
        self.assertTrue(u.permission == 1 << 2)

    def test_reset_permission(self):
        u = User(permission=1 << 2)
        u.reset_permission()
        self.assertEqual(u.permission, Permission.NIL.value)

    def test_is_administrator(self):
        u = User(permission=1 << 2)
        self.assertTrue(u.is_administrator())

    def test_to_json(self):
        u = User(password='cons car cdr')
        db.session.add(u)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = u.to_json()
        expected_keys = ['url', 'user_name', 'last_seen']
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
        self.assertEqual('api.get_user', json_user['url'])

