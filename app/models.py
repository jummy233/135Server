from typing import List, Dict
from datetime import datetime
import hashlib
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy.exc import IntegrityError
from . import db, login_manager
from .utils import is_nice_time, normalize_time, rand_date_in
from random import choice, randrange, randint, uniform
import base64


rand_date = rand_date_in(datetime(2019, 1, 1), datetime(2019, 12, 31))


def gen_fake_db():
    """ generate fake db data for testing """
    User.gen_fake()
    ClimateArea.gen_fake()
    Company.gen_fake()
    Location.gen_fake()
    OutdoorSpot.gen_fake()
    Project.gen_fake()
    Spot.gen_fake()
    OutdoorSpot.gen_fake()
    SpotRecord.gen_fake()
    OutdoorRecord.gen_fake()
    ProjectDetail.gen_fake()


class Permission(Enum):
    """ bitwise permission """
    NIL = 0
    DEMO = 1
    REAL = 2
    ADMIN = 4


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(64), unique=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())
    passwd_hash = db.Column(db.String(128))
    permission = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.permission is None:
            self.permissions = Permission.NIL.value

    @classmethod
    def gen_fake(cls, count=20):
        for _ in range(count):
            user = cls(user_name=chr(randint(33, 127)),
                       last_seen=rand_date(),
                       passwd_hash=generate_password_hash(str(randint(10000, 99999))),
                       permission=choice(list(Permission)).value)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def set_permission(self, perm):
        self.permission = perm

    def reset_permission(self):
        self.permission = Permission.NIL.value

    @property
    def password(self):
        raise AttributeError("password is unreadable")

    @password.setter
    def password(self, password: str):
        self.passwd_hash = generate_password_hash(password)

    def verify_password(self, password) -> bool:
        return check_password_hash(self.passwd_hash, password)

    def can(self, perm) -> bool:
        return self.permission != 0 and self.permission & perm == perm

    def is_administrator(self) -> bool:
        return self.can(Permission.ADMIN.value)

    def to_json(self) -> Dict:
        return dict(
            # TODO  change api.get_user to real resftul api function.
            url='api.get_user',
            user_name=self.user_name,
            last_seen=self.last_seen)

    def __repr__(self):
        return "<User {}>".format(self.user_name)


class Location(db.Model):
    """
    City, each city may contain multiple projects.
    """
    __tablename__ = "locations"
    location_id = db.Column(db.Integer, primary_key=True)
    climate_area_id = db.Column(db.Integer, db.ForeignKey("climate_areas.climate_area_id"))
    province = db.Column(db.String(64))
    city = db.Column(db.String(64), unique=True)

    project = db.relationship("Project", backref="location", lazy="dynamic")

    @classmethod
    def gen_fake(cls, count=10):
        locs: Dict = {
            "江苏": ("苏州", "南通", "常州"),
            "浙江": ("杭州",),
            "上海": ("上海",),
            "重庆": ("重庆",),
            "四川": ("成都", "宜宾"),
            "甘肃": ("宁夏",),
            "安徽": ("合肥",)
        }

        for _ in range(count):
            try:
                randprovince = choice(tuple(locs.keys()))
                loc = cls(climate_area=choice(ClimateArea.query.all()),
                          province=randprovince,
                          city=choice(locs[randprovince]))
                db.session.add(loc)
            except IndexError as e:
                print("Error! Location.gen_fake: ", e)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<Location {} {}>".format(self.province, self.city)


class Project(db.Model):
    __tablename__ = "projects"
    project_id = db.Column(db.Integer, primary_key=True)
    outdoor_spot_id = db.Column(db.Integer, db.ForeignKey("outdoor_spots.outdoor_spot_id"))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id"))
    company_id = db.Column(db.Integer, db.ForeignKey("company.company_id"))
    project_name = db.Column(db.String(64), unique=True)
    district = db.Column(db.String(64))
    floor = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    area = db.Column(db.Float)
    demo_area = db.Column(db.Float)
    building_type = db.Column(db.String(64))
    building_height = db.Column(db.Float)
    finished_time = db.Column(db.Date)
    record_started_from = db.Column(db.Date)
    record_ended_by = db.Column(db.Date, default=datetime.date(datetime.utcnow()))
    description = db.Column(db.String(2048))

    project_detail = db.relationship("ProjectDetail", backref="project", uselist=False)
    spot = db.relationship("Spot", backref="project", lazy="dynamic")

    @classmethod
    def gen_fake(cls, count=10):
        offset = randint(10, 50)
        for i in range(count):
            try:
                proj = cls(outdoor_spot=choice(OutdoorSpot.query.all()),
                           location=choice(Location.query.all()),
                           company=choice(Company.query.all()),
                           project_name=offset + i,
                           district=chr(randint(33, 127)),
                           floor=randint(33, 127),
                           longitude=uniform(30, 32),
                           latitude=uniform(105, 120),
                           area=randint(1000, 3000),
                           demo_area=randint(1000, 3000),
                           building_type=chr(randint(33, 127)),
                           building_height=randint(33, 127),
                           finished_time=rand_date(),
                           record_started_from=rand_date(),
                           record_ended_by=rand_date(),
                           description=chr(randint(33, 127)))
                db.session.add(proj)
            except IndexError as e:
                print("Error! Project.gen_fake: ", e)

            try:
                db.session.commit()
            except IndexError:
                db.commit.rollback()

    def to_json(self) -> Dict:
        return dict(
            url='api.get_projects',
            project_id=self.project_id,
            location=dict(
                location_id=self.location.location_id,
                province=self.location.province,
                city=self.location.city),
            company=dict(
                construction_company=self.company.construction_company,
                tech_support_company=self.company.tech_support_company,
                project_company=self.company.project_company),
            project_name=self.project_name,
            district=self.district,
            floor=self.floor,
            latitude=self.latitude,
            longitude=self.longitude,
            area=self.area,
            demo_area=self.demo_area,
            building_type=self.building_type,
            building_height=self.building_height,
            finished_time=self.finished_time,
            record_started_from=self.record_started_from,
            record_ended_by=self.record_ended_by,
            description=self.description)

    def __repr__(self):
        return "<Project {} {}>".format(self.project_id, self.project_name)


class ProjectDetail(db.Model):
    __tablename__ = "project_details"
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), primary_key=True)
    image = db.Column(db.Binary)
    image_description = db.Column(db.String(64))

    @classmethod
    def gen_fake(cls, count=10):
        for _ in range(count):  # pk for Outdoor spot is given.
            pd = cls(project_id=choice(Project.query.all()).project_id,
                     image=b'someimgsomeimgsomeimgsomeimgsomeimg',
                     image_description=chr(randint(33, 127)))
            db.session.add(pd)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<ProjectDetail {}>".format(self.project_id)

    def to_json(self):
        return dict(
            image=base64.encodebytes(self.image).decode(),
            image_description=self.image_description)


class OutdoorSpot(db.Model):
    __tablename__ = "outdoor_spots"
    outdoor_spot_id = db.Column(db.Integer, primary_key=True)
    outdoor_spot_name = db.Column(db.String(64), unique=True)

    outdoor_record = db.relationship("OutdoorRecord", backref="outdoor_spot", lazy="dynamic")
    project = db.relationship("Project", backref="outdoor_spot", lazy="dynamic")

    @classmethod
    def gen_fake(cls, count=10):
        offset = randint(50, 100)
        for i in range(count):  # pk for Outdoor spot is given.
            od_spot = cls(outdoor_spot_id=i + offset,
                          outdoor_spot_name=chr(randint(33, 127)))
            db.session.add(od_spot)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        return dict(
            outdoor_spot_id=self.outdoor_spot_id,
            outdoor_spot_name=self.outdoor_spot_name)

    def __repr__(self):
        return "<OutdoorSpot {} {}>".format(self.outdoor_spot_id, self.outdoor_spot_name)


class OutdoorRecord(db.Model):
    """
    Time interval is 1 hour per record.
    """
    __tablename__ = "outdoor_records"
    outdoor_record_time = db.Column(db.DateTime, primary_key=True, nullable=False)
    outdoor_spot_id = db.Column(db.Integer, db.ForeignKey("outdoor_spots.outdoor_spot_id"))
    outdoor_temperature = db.Column(db.Float)
    outdoor_humidity = db.Column(db.Float)
    chilling_temperature = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    wind_speed = db.Column(db.Float)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not is_nice_time(step_len=5)(self.outdoor_record_time):
            self.outdoor_record_time = normalize_time(5)(self.outdoor_record_time)

    @classmethod
    def gen_fake(cls, count=200):
        for _ in range(count):
            try:
                record = cls(outdoor_record_time=rand_date(),
                             outdoor_spot=choice(OutdoorSpot.query.all()),
                             outdoor_temperature=randint(20, 30),
                             outdoor_humidity=randint(60, 80),
                             chilling_temperature=randint(20, 30),
                             wind_direction=randint(0, 359),
                             wind_speed=randint(0, 200))

                db.session.add(record)
            except IndexError as e:
                print("Error! OutdoorRecord.gen_fake: ", e)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        return dict(
            outdoor_spot_id=self.outdoor_spot_id,
            outdoor_record_time=self.outdoor_record_time,
            outdoor_temperature=self.outdoor_temperature,
            outdoor_humidity=self.outdoor_humidity,
            chilling_temperature=self.chilling_temperature,
            wind_direction=self.wind_direction,
            wind_speed=self.wind_speed)

    def __repr__(self):
        return "<OutdoorRecord {} {}>".format(self.outdoor_spot_id, self.outdoor_record_time)


class ClimateArea(db.Model):
    """
    Climate area is assigned to each specific city.
    """
    __tablename__ = "climate_areas"
    climate_area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(64), unique=True)

    location = db.relationship("Location", backref="climate_area", lazy="dynamic")

    @classmethod
    def gen_fake(cls):
        for code in [letter + num for letter in ['A', 'B', 'C'] for num in '1 2 3'.split()]:
            clm_area = cls(area_name=code)
            db.session.add(clm_area)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        return dict(area_name=self.area_name,
                    climate_area_id=self.climate_area_id)

    def __repr__(self):
        return "<ClimateAreas {}>".format(self.area_name)


class Company(db.Model):
    """
    Record company info for one project.
    """
    __tablename__ = "company"
    company_id = db.Column(db.Integer, primary_key=True)
    construction_company = db.Column(db.String(64))
    tech_support_company = db.Column(db.String(64))
    project_company = db.Column(db.String(64))

    project = db.relationship("Project", backref="company", lazy="dynamic")

    @classmethod
    def gen_fake(cls, count=5):
        for _ in range(count):
            company = cls(construction_company=chr(randint(33, 127)),
                          tech_support_company=chr(randint(33, 127)),
                          project_company=chr(randint(33, 127)))
            db.session.add(company)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<Company {}>".format(self.company_id)


class Spot(db.Model):
    __tablename__ = "spots"
    spot_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"))
    spot_name = db.Column(db.String(64))
    image = db.Column(db.Binary)

    spot_record = db.relationship("SpotRecord", backref="spot", lazy="dynamic")

    @classmethod
    def gen_fake(cls, count=20):
        for _ in range(count):
            spot = cls(project=choice(Project.query.all()),
                       spot_name=chr(randint(33, 127)),
                       image=b'asdadasd')
            db.session.add(spot)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<Spot {}>".format(self.spot_name)

    def to_json(self):
        return dict(
            spot_id=self.spot_id,
            project_id=self.project_id,
            project_name=self.project.project_name,
            spot_name=self.spot_name,
            image=base64.encodebytes(self.image).decode())

class SpotRecord(db.Model):
    """
    The time interval is 5 mins per record.
    """
    __tablename__ = "spot_records"
    spot_record_time = db.Column(db.DateTime, primary_key=True, nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("spots.spot_id"))
    window_opened = db.Column(db.Boolean)  # for xiaomi platform. noting to do with demoproj
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    energy_comsumption = db.Column(db.Float)
    pm25 = db.Column(db.Integer)
    co2 = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not is_nice_time(step_len=5)(self.spot_record_time):
            self.spot_record_time = normalize_time(5)(self.spot_record_time)

    @classmethod
    def gen_fake(cls, count=200):
        for _ in range(count):
            try:
                spot_record = cls(spot_record_time=rand_date(),
                                  spot=choice(Spot.query.all()),
                                  window_opened=bool(choice((0, 1))),
                                  temperature=randint(20, 30),
                                  humidity=randint(60, 80),
                                  energy_comsumption=randint(2000, 3000),
                                  pm25=randint(20, 100),
                                  co2=randint(10, 30))

                db.session.add(spot_record)
            except IndexError as e:  # Spot is empty.
                print("Error! SpotRecord.gen_fake: ", e)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        return dict(spot_id=self.spot_id,
                    spot_name=self.spot.spot_name,
                    spot_record_time=self.spot_record_time,
                    temperature=self.temperature,
                    humidity=self.humidity,
                    energy_comsumption=self.energy_comsumption,
                    pm25=self.pm25,
                    co2=self.co2)

    def __repr__(self):
        return "<SpotRecord {} {}>".format(self.spot, self.spot_record_time)
