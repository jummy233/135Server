"""
Script to init database.
"""

import json
import os
import sqlite3
from operator import itemgetter
import logging
from functools import partial
from typing import List, Dict, Union, Generator, Iterator, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from fuzzywuzzy import fuzz

from app.models import ClimateArea, Location, Project, Spot, Device, SpotRecord
from app.modelOperations import add_location, add_project, add_spot, add_spot_record
from app import db
from dataGetter import dataMidware
import dataGetter as D

current_dir = os.path.abspath(os.path.dirname(__file__))

####################
#  create database #
####################


def create_db(force=True) -> None:
    logging.debug('- createcreate init  db')
    db_path = os.path.join(current_dir, 'development.sqlite')
    schema_path = os.path.join(current_dir, 'schema.sql')

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

        add_project(proj_json)

####################
#  Load full data  #
####################


def fuzztuple(match_string, candiates: Tuple[str, str]) -> float:
    fst, snd = candiates
    fuzz_on = partial(fuzz.partial_ratio, match_string)
    return max(fuzz_on(fst), fuzz_on(snd))


class JianyanyuanLoadFull:
    """
    load all Jianyanyuan data.
    devices spot and records are large and has heavy state dependency.
    """

    def __init__(self):
        self.j = dataMidware.JianYanYuanData()

    def load_spots(self):
        """
        -----------------------------------------
         Different methods to get spot
        -----------------------------------------
        method 1:    fuzzy match the JianyanyuanData Location typedict with project name
        method 2:    use the j_project_device_table's projects name. (all project from jianyanyuan)
        other wise:  no enough information, pass

        Jianyanyuan spot are just project. There is no room information.

        """
        spots: Optional[Generator] = self.j.spot()
        if not spots:
            logging.warning('empty spot from JianYanYuanData')
            return

        def spotname_from_projectname(project_name: str) -> str:
            return project_name + '测点'

        # method 1 fuzzy match
        projects: Tuple = tuple(Project.query.all())
        for s in spots:

            project_name = s.get('project_name')
            fuzzon = partial(fuzz.partial_ratio, project_name)
            fuzz_results: List[float] = list(map(lambda p: fuzzon(p.project_name), projects))
            max_ratio = max(fuzz_results)

            spot_post: Dict = {}

            if max_ratio > 80:  # > 80 means a good match
                project = projects[fuzz_results.index(max_ratio)]
                spot_post = {
                    "project": project,
                    "spot_name": spotname_from_projectname(project.project_name),
                    "spot_type": None,
                    "image": None
                }

                add_spot(spot_post)

        # method 2: Use keys of j_project_device_table.
        with open('./dataGetter/static/j_project_device_table.json', 'r') as f:
            json_data: Dict = json.loads(f.read())
            projects = (Project
                        .query
                        .filter(Project.project_name in json_data.keys()))

        spot_names = list(map(lambda p: spotname_from_projectname(p.project_name), projects))

        for spot_name in spot_names:
            if not Spot.query.filter(Spot.spot_name == spot_names):
                spot_post = {
                    "project": project,
                    "spot_name": spotname_from_projectname(project.project_name),
                    "spot_type": None,
                    "image": None
                }
                add_spot(spot_post)

    def load_devices(self):
        # Jianyanyuan devices.
        devices: Optional[Generator] = self.j.device()
        if not devices:
            logging.warning('empty device from JianyanyuanData')
            return

        for d in devices:
            pass

    def load_spot_records(self):
        pass


def db_init(full=False):
    load_climate_area()
    load_location()
    load_projects()

    if full:
        load_data = JianyanyuanLoadFull()
        load_data.load_spots()
        # load_data.load_devices()
        # load_data.load_spot_records()

