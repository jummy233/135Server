"""
Script to init database.
"""

from typing import List, Dict, Union
import json
import os
import sqlite3
from operator import itemgetter
import logging

from sqlalchemy.exc import IntegrityError

from .models import ClimateArea, Location, Project
from .modelOperations import add_location, add_project
from . import db
from . import dataGetter as D

current_dir = os.path.abspath(os.path.dirname(__file__))

####################
#  create database #
####################


def create_db(force=True) -> None:
    logging.debug('- createcreate init  db')
    par_abs_path = os.path.join(current_dir, os.path.pardir)
    db_path = os.path.join(par_abs_path, 'development.sqlite')
    schema_path = os.path.join(par_abs_path, 'schema.sql')

    if not force and os.path.exists(db_path):
        return

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        with open(schema_path, 'r') as f:
            sql: str = f.read()

        cur.executescript(sql)
        conn.commit()


#########################
#  Record Climate Area  #
#########################


def load_climate_area() -> None:
    logging.debug('- create climate area')
    path = os.path.join(current_dir, 'dataGetter/static/climate_area.json')
    with open(path, 'r') as f:
        data: Dict = json.loads(f.read())
    climate_areas: List = data['climate_area']

    if ClimateArea.query.all():
        return None
    for cl in climate_areas:
        try:
            newcl = ClimateArea(area_name=str(cl))
            db.session.add(newcl)
        except IntegrityError:
            db.commit.rollback()


#####################
#  Record Location  #
#####################
def load_location() -> None:
    logging.debug('- create location')
    path = os.path.join(current_dir, 'dataGetter/static/locations.json')
    with open(path, 'r') as f:
        data: Dict = json.loads(f.read())

    if Location.query.all():
        return None

    for province, vlist in data.items():
        for v in vlist:
            city, clid = itemgetter('name', 'clid')(v)
            d = {'province': province, 'city': city, 'climate_area_name': clid}
            add_location(d)


####################
#  Record Project  #
####################
def load_projects():
    logging.debug('- create proejcts')
    path = os.path.join(current_dir, 'dataGetter/static/projects.json')
    with open(path, 'r') as f:
        data: Dict = json.loads(f.read())

    if Project.query.all():
        return None

    for proj_json in data['data']:

        # construct location
        proj_json_location: str = proj_json['location']
        patterns = (proj_json_location
                    .replace('省', '-')
                    .replace('市', '-')
                    .split('-'))

        if len(patterns) == 2 and not patterns[1]:  # shanghai chongqing
            p, _ = patterns
            location = Location.query.filter_by(city=p).first()

        if len(patterns) == 3:
            _, c, _ = patterns
            location = Location.query.filter_by(city=c).first()

        proj_json['location'] = location

        # construct company
        proj_json['tech_support_company'] = {'company_name': proj_json['tech_support_company']}
        proj_json['project_company'] = {'company_name': proj_json['project_company']}
        proj_json['construction_company'] = {'company_name': proj_json['construction_company']}

        def convert(val: str, typ) -> Union[None, int, float]:
            if not val:
                return None
            return typ(val)

        def json_convert(jsondata, key, typ) -> None:
            jsondata[key] = convert(jsondata[key], typ)

        json_convert(proj_json, 'floor', int)
        json_convert(proj_json, 'longitude', float)
        json_convert(proj_json, 'latitude', float)
        json_convert(proj_json, 'area', float)
        json_convert(proj_json, 'demo_area', float)
        json_convert(proj_json, 'building_height', float)
        json_convert(proj_json, 'started_time', lambda s: s.split('T')[0])
        json_convert(proj_json, 'finished_time', lambda s: s.split('T')[0])
        json_convert(proj_json, 'record_started_from', lambda s: s.split('T')[0])

        add_project(proj_json)

#################
#  Record Spot  #
#################

#########################
#  Record Spot Records  #
#########################


####################
#  Record Devices  #
####################

def db_init():
    load_climate_area()
    load_location()
    load_projects()
