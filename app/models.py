from __future__ import annotations
from typing import List, Dict, Union
from datetime import datetime
import hashlib
from enum import Enum
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin
from flask_login import AnonymousUserMixin
from sqlalchemy.exc import IntegrityError
from . import db, login_manager
from .utils import is_nice_time
from .utils import normalize_time
from .utils import rand_date_in
from random import choice
from random import randint
from random import uniform
import base64

rand_date = rand_date_in(datetime(2019, 1, 1), datetime(2019, 12, 31))
TIMEFORMAT = "%Y-%m-%dT%H:%M"


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
    __tablename__ = "user"
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
    def gen_admin(cls):
        user = cls(user_name='admin',
                   last_seen=datetime.now(),
                   passwd_hash=generate_password_hash('123456'),
                   permission=Permission.ADMIN.value)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    @classmethod
    def gen_fake(cls, count=20):
        for _ in range(count):
            user = cls(user_name=chr(randint(33, 127)),
                       last_seen=rand_date(),
                       passwd_hash=generate_password_hash(
                           str(randint(10000, 99999))),
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
            last_seen=datetime.ctime(self.last_seen))

    def __repr__(self):
        return "<User {}>".format(self.user_name)


class Location(db.Model):
    """
    City, each city may contain multiple projects.
    """
    __tablename__ = "location"
    location_id = db.Column(db.Integer, primary_key=True)
    climate_area_id = db.Column(
        db.Integer, db.ForeignKey("climate_area.climate_area_id"))
    province = db.Column(db.String(64))
    city = db.Column(db.String(64), unique=True)

    project = db.relationship("Project", backref="location", lazy="dynamic")

    def update(self, update_location: Location) -> None:
        self.climate_area_id = (update_location.climate_area_id
                                or self.climate_area_id)
        self.province = update_location.province or self.province
        self.city = update_location.city or self.city
        db.session.commit()

    def to_json(self):
        if self.climate_area is not None:
            climate_area = self.climate_area.to_json()
        else:
            climate_area = None

        return dict(climate_area=climate_area,
                    province=self.province,
                    city=self.city)

    @classmethod
    def gen_fake(cls, count=20):
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
    __tablename__ = "project"
    project_id = db.Column(db.Integer, primary_key=True)
    outdoor_spot_id = db.Column(
        db.Integer, db.ForeignKey("outdoor_spot.outdoor_spot_id"))
    location_id = db.Column(db.Integer, db.ForeignKey("location.location_id"))

    tech_support_company_id = db.Column(
        db.Integer, db.ForeignKey("company.company_id"))
    project_company_id = db.Column(
        db.Integer, db.ForeignKey("company.company_id"))
    construction_company_id = db.Column(
        db.Integer, db.ForeignKey("company.company_id"))

    project_name = db.Column(db.String(64), unique=True)
    district = db.Column(db.String(64))
    floor = db.Column(db.Integer)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    area = db.Column(db.Float)
    demo_area = db.Column(db.Float)

    building_type = db.Column(db.String(64))
    building_height = db.Column(db.Float)

    started_time = db.Column(db.DateTime)
    finished_time = db.Column(db.DateTime)
    record_started_from = db.Column(db.DateTime)

    description = db.Column(db.String(2048))

    spot = db.relationship("Spot", backref="project",
                           cascade="all,delete", uselist=False)
    project_detail = db.relationship("ProjectDetail", backref="project",
                                     cascade="all,delete", uselist=False)

    tech_support_company = db.relationship(
        "Company",
        backref="tech_support_company",
        uselist=False,
        foreign_keys=[tech_support_company_id])

    project_company = db.relationship(
        "Company",
        backref="project_company",
        uselist=False,
        foreign_keys=[project_company_id])

    construction_company = db.relationship(
        "Company",
        backref="construction_company",
        uselist=False,
        foreign_keys=[construction_company_id])

    spot = db.relationship("Spot", backref="project", lazy="dynamic")

    def update(self, update_project: Project) -> None:
        """
        Full update can not update the project id.
        if a value is not present in the given data, fall back to
        the original record.
        """
        self.outdoor_spot_id = update_project.outdoor_spot_id  \
            or self.outdoor_spot_id
        self.location_id = update_project.location_id \
            or self.location_id

        self.tech_support_company_id = update_project.tech_support_company_id \
            or self.tech_support_company_id

        self.project_company_id = update_project.project_company_id \
            or self.project_company_id

        self.construction_company_id = update_project.construction_company_id \
            or self.construction_company_id

        self.project_name = update_project.project_name or self.project_name
        self.district = update_project.district or self.district
        self.floor = update_project.floor or self.floor

        self.latitude = update_project.latitude or self.latitude
        self.longitude = update_project.longitude or self.longitude

        self.area = update_project.area or self.area
        self.demo_area = update_project.demo_area or self.demo_area
        self.building_type = update_project.building_type or self.building_type
        self.building_height = update_project.building_height \
            or self.building_height
        self.started_time = update_project.started_time or self.started_time
        self.finished_time = update_project.finished_time or self.finished_time

        self.record_started_from = update_project.record_started_from \
            or self.record_started_from
        self.description = update_project.description or self.description
        db.session.commit()

    @classmethod
    def gen_fake(cls, count=38):
        offset = randint(10, 50)
        for i in range(count):
            try:
                proj = cls(outdoor_spot=choice(OutdoorSpot.query.all()),
                           location=choice(Location.query.all()),
                           # TODO deprecated
                           company=choice(Company.query.all()),
                           project_name=str(offset + i) + \
                           choice('abcdefghijklmno') * 30,
                           district=chr(randint(33, 127)),
                           floor=randint(33, 127),
                           longitude=uniform(30, 32),
                           latitude=uniform(105, 120),
                           area=randint(1000, 3000),
                           demo_area=randint(1000, 3000),
                           building_type=chr(randint(33, 127)),
                           building_height=randint(33, 127),
                           started_time=rand_date(),
                           finished_time=rand_date(),
                           record_started_from=rand_date(),
                           description=chr(randint(33, 127)))
                db.session.add(proj)
            except IndexError as e:
                print("Error! Project.gen_fake: ", e)

            try:
                db.session.commit()
            except IndexError:
                db.commit.rollback()

    def to_json(self) -> Dict:
        location = (
            self.location.to_json()
            if self.location is not None else None)

        tech_support_company = (
            self.tech_support_company.to_json()
            if self.tech_support_company is not None else None)

        project_company = (
            self.project_company.to_json()
            if self.project_company is not None else None)

        construction_company = (
            self.construction_company.to_json()
            if self.construction_company is not None else None)

        outdoor_spot = (
            self.outdoor_spot.to_json()
            if self.outdoor_spot is not None else None)

        started_time = (
            self.started_time.strftime("%Y-%m-%d")
            if self.started_time else None)

        finished_time = (
            self.finished_time.strftime("%Y-%m-%d")
            if self.finished_time else None)

        record_started_from = (
            self.record_started_from.strftime("%Y-%m-%d")
            if self.record_started_from else None)

        return dict(
            project_id=self.project_id,
            location=location,
            tech_support_company=tech_support_company,
            project_company=project_company,
            construction_company=construction_company,
            outdoor_spot=outdoor_spot,

            project_name=self.project_name,
            district=self.district,
            floor=self.floor,
            latitude=self.latitude,
            longitude=self.longitude,
            area=self.area,
            demo_area=self.demo_area,
            building_type=self.building_type,
            building_height=self.building_height,
            started_time=started_time,
            finished_time=finished_time,
            record_started_from=record_started_from,
            description=self.description)

    def __repr__(self):
        return "<Project {} {}>".format(self.project_id, self.project_name)


class ProjectDetail(db.Model):
    __tablename__ = "project_detail"
    project_id = db.Column(db.Integer, db.ForeignKey("project.project_id"),
                           primary_key=True)
    image = db.Column(db.Binary)
    image_description = db.Column(db.String(64))

    def update(self, update_project_detail: ProjectDetail) -> None:

        # image can be large object, so check befor update.
        if update_project_detail.image:
            self.image = update_project_detail.image

        self.image_description = update_project_detail.image_description \
            or self.image_description
        db.session.commit()

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
            project_id=self.project_id,
            image=base64.encodebytes(self.image).decode(),
            image_description=self.image_description)


class OutdoorSpot(db.Model):
    __tablename__ = "outdoor_spot"
    outdoor_spot_id = db.Column(db.Integer, primary_key=True)
    outdoor_spot_name = db.Column(db.String(64), unique=True)

    outdoor_record = db.relationship("OutdoorRecord", backref="outdoor_spot",
                                     lazy="dynamic")
    project = db.relationship("Project", backref="outdoor_spot",
                              lazy="dynamic")

    def update(self, update_outdoor_spot: OutdoorSpot) -> None:
        db.session.commit()
        ...

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
        return "<OutdoorSpot {} {}>".format(self.outdoor_spot_id,
                                            self.outdoor_spot_name)


class OutdoorRecord(db.Model):
    """
    Time interval is 1 hour per record.
    """
    __tablename__ = "outdoor_record"
    outdoor_record_time = db.Column(
        db.DateTime, primary_key=True, nullable=False)
    outdoor_spot_id = db.Column(db.Integer,
                                db.ForeignKey("outdoor_spot.outdoor_spot_id"))
    outdoor_temperature = db.Column(db.Float)
    outdoor_humidity = db.Column(db.Float)
    wind_direction = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_chill = db.Column(db.Float)
    solar_radiation = db.Column(db.Float)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not is_nice_time(step_len=5)(self.outdoor_record_time):
            self.outdoor_record_time = \
                normalize_time(5)(self.outdoor_record_time)

    def update(self, update_outdoor_record: OutdoorRecord) -> None:
        db.session.commit()
        ...

    @classmethod
    def gen_fake(cls, count=2000):
        for _ in range(count):
            try:
                record = cls(outdoor_record_time=rand_date(),
                             outdoor_spot=choice(OutdoorSpot.query.all()),
                             outdoor_temperature=randint(20, 30),
                             outdoor_humidity=randint(60, 80),
                             wind_direction=randint(0, 360),
                             wind_speed=randint(0, 200),
                             wind_chill=randint(20, 30),
                             solar_radiation=randint(0, 20))

                db.session.add(record)
            except IndexError as e:
                print("Error! OutdoorRecord.gen_fake: ", e)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        outdoor_record_time = (self.outdoor_record_time.strftime(TIMEFORMAT)
                               if self.outdoor_record_time else None)

        return dict(
            outdoor_spot_id=self.outdoor_spot_id,
            outdoor_record_time=outdoor_record_time,
            outdoor_temperature=self.outdoor_temperature,
            outdoor_humidity=self.outdoor_humidity,
            wind_chill=self.wind_chill,
            wind_direction=self.wind_direction,
            solar_radiation=self.solar_radiation,
            wind_speed=self.wind_speed)

    def __repr__(self):
        return ("<OutdoorRecord {} {}>"
                .format(self.outdoor_spot_id,
                        self.outdoor_record_time))


class ClimateArea(db.Model):
    """
    Climate area is assigned to each specific city.
    """
    __tablename__ = "climate_area"
    climate_area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(64), unique=True)

    location = db.relationship("Location", backref="climate_area",
                               lazy="dynamic")

    def update(self, update_climate_area: ClimateArea) -> None:
        db.session.commit()
        ...

    @classmethod
    def gen_fake(cls):
        for code in [letter + num for letter in ['A', 'B', 'C']
                     for num in '1 2 3'.split()]:
            clm_area = cls(area_name=code)
            db.session.add(clm_area)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        return dict(area_name=self.area_name)

    def __repr__(self):
        return "<ClimateAreas {}>".format(self.area_name)


class Company(db.Model):
    """
    Record company info for one project.
    """
    __tablename__ = "company"
    company_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(40))

    def update(self, update_company: Company) -> None:
        db.session.commit()
        ...

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

    def to_json(self):
        return dict(company_name=self.company_name)

    def __repr__(self):
        return "<Company {}>".format(self.company_id)


class Spot(db.Model):
    __tablename__ = "spot"
    spot_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.project_id"))
    spot_name = db.Column(db.String(64))
    spot_type = db.Column(db.String(64))
    image = db.Column(db.Binary)

    device = db.relationship("Device", backref="spot", lazy="dynamic")

    def update(self, update_spot: Spot) -> None:
        self.project_id = update_spot.project_id or self.project_id
        self.spot_name = update_spot.spot_name or self.spot_name
        self.spot_type = update_spot.spot_type or self.spot_type

        if update_spot.image:  # large object.
            self.image = update_spot.image
        db.session.commit()

    @classmethod
    def gen_fake(cls, count=20):
        for _ in range(count):
            spot = cls(project=choice(Project.query.all()),
                       spot_name=chr(randint(33, 127)),
                       spot_type=chr(randint(33, 127)),
                       image=b'asdadasd')
            db.session.add(spot)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<Spot {}>".format(self.spot_name)

    def to_json(self):
        image_base64 = None
        if self.image:
            base64.encodebytes(self.image).decode()

        return dict(
            number_of_device=db.session.query(
                Device).filter_by(spot_id=self.spot_id).count(),
            spot_id=self.spot_id,
            project_id=self.project_id,
            project_name=self.project.project_name,
            spot_name=self.spot_name,
            spot_type=self.spot_type,
            image=image_base64)


class Device(db.Model):
    """ Device model """
    __tablename__ = "device"
    device_id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("spot.spot_id"))
    online = db.Column(db.Boolean)
    create_time = db.Column(db.DateTime)
    modify_time = db.Column(db.DateTime)
    device_name = db.Column(db.String(64))
    device_type = db.Column(db.String(64))

    spot_record = db.relationship(
        "SpotRecord", backref="device", lazy="dynamic")

    def update(self, update_device: Device) -> None:
        self.spot_id = update_device.spot_id or self.spot_id
        self.online = update_device.online or self.online
        self.create_time = update_device.create_time or self.create_time
        self.modify_time = update_device.modify_time or self.modify_time
        self.device_name = update_device.device_name or self.device_name
        self.device_type = update_device.device_type or self.device_type
        db.session.commit()

    def to_json(self):
        create_time = (
            self.create_time.strftime(TIMEFORMAT)
            if self.create_time else None)

        modify_time = (
            self.modify_time.strftime(TIMEFORMAT)
            if self.modify_time else None)

        spot_name = self.spot.spot_name if self.spot else None
        project_id = (self.spot.project.project_id
                      if self.spot and self.spot.project else None)
        project_name = (self.spot.project.project_name if
                        self.spot and self.spot.project else None)

        return dict(device_id=self.device_id,
                    spot_id=self.spot_id,
                    project_id=project_id,

                    spot_name=spot_name,
                    project_name=project_name,

                    online=self.online,
                    create_time=create_time,
                    modify_time=modify_time,
                    device_name=self.device_name,
                    device_type=self.device_type)


class SpotRecord(db.Model):
    """
    The time interval is 5 mins per record.
    """
    __tablename__ = "spot_record"
    spot_record_id = db.Column(db.Integer, primary_key=True, nullable=False)
    spot_record_time = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("device.device_id"))
    window_opened = db.Column(db.Boolean)  # for xiaomi platform.
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ac_power = db.Column(db.Float)
    pm25 = db.Column(db.Integer)
    co2 = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not is_nice_time(step_min=5)(self.spot_record_time):
            self.spot_record_time = normalize_time(5)(self.spot_record_time)

    def update(self, update_spot_record: SpotRecord) -> None:
        self.spot_record_time = update_spot_record.spot_record_time \
            or self.spot_record_time
        self.device_id = update_spot_record.device_id or self.device_id
        self.window_opened = update_spot_record.window_opened \
            or self.window_opened
        self.temperature = update_spot_record.temperature or self.temperature
        self.humidity = update_spot_record.humidity or self.humidity
        self.ac_power = update_spot_record.ac_power or self.ac_power
        self.pm25 = update_spot_record.pm25 or self.pm25
        self.co2 = update_spot_record.co2 or self.co2
        db.session.commit()

    @classmethod
    def gen_fake(cls, count=5000):
        for _ in range(count):
            try:
                spot_record = cls(
                    spot_record_time=rand_date(),
                    spot=choice(Spot.query.all()),
                    window_opened=bool(choice((0, 1))),
                    temperature=randint(20, 30),
                    humidity=randint(60, 80),
                    ac_power=randint(2000, 3000),
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
        spot_record_time = (self.spot_record_time.strftime(TIMEFORMAT)
                            if self.spot_record_time else None)

        return dict(spot_record_id=self.spot_record_id,
                    device_id=self.device_id,
                    spot_record_time=spot_record_time,
                    window_opened=self.window_opened,
                    temperature=self.temperature,
                    humidity=self.humidity,
                    ac_power=self.ac_power,
                    pm25=self.pm25,
                    co2=self.co2)

    def __repr__(self):
        return "<SpotRecord id: {} {} {}>".format(
            self.spot_record_id, self.spot_record_time, self.device_id)


Data = Union[
    Project,
    Spot,
    ProjectDetail,
    SpotRecord,
    OutdoorSpot,
    OutdoorRecord,
    Device,
    Company,
    Location,
    ClimateArea]
