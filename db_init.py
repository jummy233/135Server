"""
Script to init database.

TODO: Some funtions are deprecated, need to clean sometome

"""

import json
import os
import sqlite3
import threading
from functools import partial
from itertools import islice
from logging import DEBUG
from operator import itemgetter
from queue import Queue
from typing import (Any, Callable, Dict, Generator, Generic, Iterator, List,
                    NewType, Optional, Tuple, Type, TypeVar, Union, cast)

from fuzzywuzzy import fuzz
from sqlalchemy.exc import IntegrityError
from flask import current_app

from app import db
from app.modelOperations import ModelOperations, commit
from app.models import ClimateArea, Device, Location, Project, Spot, SpotRecord
from concurrent_fetch import thread_fetcher
from app.dataGetter.dataGen import JianYanYuanData
from app.dataGetter.dataGen import XiaoMiData
from app.dataGetter.dataGen import dataType as DGType
from lazybox import LazyBox, LazyGenerator
from logger import make_logger

logger = make_logger('db_init', 'app_log', DEBUG)
current_dir = os.path.abspath(os.path.dirname(__file__))

T = TypeVar('T')
U = TypeVar('U')
Job = Callable[[], Optional[Generator[T, None, None]]]


####################
#  create database #
####################


def create_db(name='development.sqlite', force=True) -> None:

    logger.debug('- creating db')
    db_path = os.path.join(current_dir, name)
    schema_path = os.path.join(current_dir, 'schema.sql')

    if not force and os.path.exists(db_path):
        return

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        with open(schema_path, 'r') as f:
            sql: str = f.read()

        cur.executescript(sql)
        conn.commit()


##############################
#  Data fetching strategies  #
##############################


def threaded_collector(
        jobs: Iterator[Job],
        max_concurrent_thread_num: int,
        queue: Queue,  # T
        worker: Callable[[Queue,  Iterator[Job]], None],
        consumer: Callable[[T], None],
        hook: Callable[..., None]) -> None:
    """
    Colletor data with thread worker and pipe results to consumer.
    spawn limit amount of thread once at a time and consume the result
    right after
    """

    total_count: int = 0
    queue_worder = partial(worker, queue)  # avoid pass queue all the time

    try:
        while jobs:  # iterate through till jobs is exthausted.
            logger.info('<Main Thread>On job: {}'.format(total_count))

            # list of jobs wrap in iterator. Will be evaled in thread.
            # job_buffer is garuanteed to be exthausted.
            # ps: job_buffer has known length, which is
            # max_concurrent_thread_num
            job_buffer: LazyGenerator[Job] = LazyGenerator(
                islice(jobs, max_concurrent_thread_num))

            total_count += max_concurrent_thread_num

            threads = list()

            for idx in range(max_concurrent_thread_num):
                logger.info('<Main Thread> Start thread %d', idx)

                # work wrapped by lazy iterator with only 1 element.
                s: LazyBox[Job] = next(job_buffer)

                t = threading.Thread(target=queue_worder, args=(s,))

                t.setDaemon(True)  # avoid race in queue

                threads.append(t)

                t.start()

            for idx, t in enumerate(threads):
                t.join()
                logger.info('<Main Thread> thread  %d done', idx)

            # consume queue.
            logger.info('consumming data...')
            with threading.Lock():

                while not queue.empty():

                    # feed the data fetched into consumer.
                    feed: T = queue.get()
                    consumer(feed)
            hook()

    except StopIteration:
        return


#########################
#  Record Climate Area  #
#########################


def load_climate_area() -> None:
    logger.debug('- create climate area')
    path = os.path.join(current_dir, 'app/dataGetter/static/climate_area.json')
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
    logger.debug('- create location')
    path = os.path.join(current_dir, 'app/dataGetter/static/locations.json')
    with open(path, 'r') as f:
        data: Dict = json.loads(f.read())

    if Location.query.all():
        return None

    for province, vlist in data.items():
        for v in vlist:
            city, clid = itemgetter('name', 'clid')(v)
            d = {'province': province, 'city': city, 'climate_area_name': clid}
            ModelOperations.Add.add_location(d)


####################
#  Record Project  #
####################


def load_projects():
    logger.debug('- create projcts')
    path = os.path.join(current_dir, 'app/dataGetter/static/projects.json')
    with open(path, 'r') as f:
        data: Dict = json.loads(f.read())

    # if Project.query.all():
    #     return None

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
        proj_json['tech_support_company'] = {
            'company_name': proj_json['tech_support_company']
        }
        proj_json['project_company'] = {
            'company_name': proj_json['project_company']
        }
        proj_json['construction_company'] = {
            'company_name': proj_json['construction_company']
        }

        ModelOperations.Add.add_project(proj_json)

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

    def __init__(
            self,
            datapoint_thread_num: int = 30,
            datapoint_from: int = 0):
        self.j = JianYanYuanData(current_app)
        self.datapoint_thread_num = datapoint_thread_num
        self.datapoint_from = datapoint_from

    def close(self):
        self.j.close()

    def load_spots(self):
        """
        -----------------------------------------
         Different methods to get spot
        -----------------------------------------
        method 1:    use the j_project_device_table's projects name.
                     (all project from jianyanyuan)
        method 2:    fuzzy match the JianyanyuanData Location typedict with
                     project name
        other wise:  no enough information, pass

        Jianyanyuan spot are just project. There is no room information.

        """
        spots: Optional[Generator] = self.j.spot()
        if not spots:
            logger.warning('empty spot from JianYanYuanData')
            return

        def spotname_from_projectname(project_name: str) -> str:
            return project_name + '测点'

        def load_by_table_lookup():
            """ method 1: Use keys of j_project_device_table. """
            with open('app/dataGetter/static/j_project_device_table.json',
                      'r') as f:
                json_data: Dict = json.loads(f.read())
                projects = [
                    (Project
                     .query
                     .filter_by(project_name=pn))
                    .first() for pn in json_data.keys()]

            names: List[Tuple[str, str]] = list(
                map(lambda p:
                    (spotname_from_projectname(p.project_name),
                     p.project_name),
                    projects))

            for spot_name, project_name in names:

                if not Spot.query.filter_by(spot_name=spot_name).first():
                    project = Project.query.filter_by(
                        project_name=project_name).first()
                    if not project:  # project doesn't exist, skip it.
                        continue

                    spot_post = {
                        "project": project,
                        "spot_name": spotname_from_projectname(
                            project.project_name),
                        "spot_type": None,
                        "image": None
                    }
                    ModelOperations.Add.add_spot(spot_post)

        def load_by_fuzzy_match():
            """ method 2 fuzzy match """
            projects: Tuple = tuple(Project.query.all())
            for s in spots:

                project_name = s.get('project_name')
                fuzzon = partial(fuzz.partial_ratio, project_name)
                fuzz_results: List[float] = list(
                    map(lambda p: fuzzon(p.project_name), projects))
                max_ratio = max(fuzz_results)

                if max_ratio > 40:  # > 40 means a good match
                    project = projects[fuzz_results.index(max_ratio)]
                    spot_post = {
                        "project": project,
                        "spot_name": spotname_from_projectname(
                            project.project_name),
                        "spot_type": None,
                        "image": None
                    }

                    ModelOperations.Add.add_spot(spot_post)

        load_by_table_lookup()
        load_by_fuzzy_match()
        logger.info('finished loading spot')

    def load_devices(self, raw=False):
        """
        Like Spot devices has two sources to determine its Spot.
        method 1: deduce from j_project_device_table.json file.
        method 2: to determine from the location_info from Device TypedDict
        """

        def handle_location_info(location_info) -> Optional[Spot]:
            """
            Deduce Spot by given location_info.
            if cannot find a result return None.

            priority of elements of location_info:
                1. address
                2. extra

            Because city and province are login location so they are generally
            incorrect.

            If address and extra doesn't yield a Spot, either go with a
            json table search or skip it.

            Note for Jianyanyuan spots are basically the same as projects.
            """
            _, _, address, extra = itemgetter(
                'province', 'city', 'address', 'extra')(location_info)

            projects: Tuple = tuple(Project.query.all())

            # fuzzy match based on address and extra infos.
            fuzz_address_results: List[float] = list(
                map(lambda p: fuzz.partial_ratio(p.project_name, address),
                    projects))

            fuzz_extra_results: List[float] = list(
                map(lambda p: fuzz.partial_ratio(p.project_name, extra),
                    projects))

            max_address_ratio = max(fuzz_address_results)

            max_extra_ratio = max(fuzz_extra_results)

            # ratio > 40 indicate a good match.
            if max_address_ratio < 80 and max_extra_ratio < 80:
                return None

            project: Optional[Project] = None  # get project for spot.
            if max_address_ratio > max_extra_ratio:
                project = projects[fuzz_address_results.index(
                    max_address_ratio)]

            else:
                project = projects[fuzz_extra_results.index(max_extra_ratio)]

            if not project:
                return None

            # use project to query spot.
            spot: Spot = Spot.query.filter_by(project=project).first()
            if not spot:
                return None
            return spot

        # Note: Two methods both loop through device list.
        def load_by_table_lookup(
                d: DGType.Device,
                json_data: Dict,
                json_spot_list: List[Spot]):
            """
            method 1 load project name from json table for given device id
            """

            did = d.get('device_name')

            for project_name, did_lists in json_data.items():
                if did in did_lists:
                    spot = next(
                        filter(
                            lambda s: s.project.project_name == project_name,
                            json_spot_list))

                    device_post_data = {
                        'device_name': did,
                        'device_type': d.get('device_type'),
                        'spot': spot,
                        'online': d.get('online'),
                        'create_time': d.get('create_time'),
                        'modify_time': d.get('modify_time')
                    }
                    ModelOperations.Add.add_device(device_post_data)

        def load_by_location_info(d: DGType.Device):
            """
            method 2, deduce the spot by location_info typedict come
            with Device typedict
            """

            spot: Optional[Spot] = handle_location_info(d['location_info'])

            device_post_data = {
                'device_name': d.get('device_name'),
                'device_type': d.get('device_type'),
                'spot': spot,
                'online': d.get('online'),
                'create_time': d.get('create_time'),
                'modify_time': d.get('modify_time')
            }

            ModelOperations.Add.add_device(device_post_data)

        # Jianyanyuan devices.
        devices: Optional[Generator] = self.j.device()
        if not devices:
            logger.warning('empty device from JianyanyuanData')
            return

        # NOTE: THis is for debug only
        # when raw is true, load device without any extra project
        # information.
        if raw:
            for device in devices:  # dataType.Device
                ModelOperations.Add.add_device(cast(Dict, device))
            commit()

        else:
            # read json files
            with open('app/dataGetter/static/j_project_device_table.json', 'r') as f:
                json_data: Dict = json.loads(f.read())
                json_spot_list = [
                    (Project
                     .query
                     .filter_by(project_name=pn)).first().spot.first()
                    for pn in json_data.keys()]

            for d in devices:  # consumer

                # second operation will overwrite the first one.
                # table lookup has higher accuracy so has higher priority
                # than fuzzy match.
                load_by_table_lookup(d, json_data, json_spot_list)
                load_by_location_info(d)

            logger.info('finished loading device')

    def load_spot_records(self):
        """
        There is no local table look up.
        All info come from dataGen iterator
        """
        spot_records: Iterator[Optional[Generator]] = (
            islice(self.j.spot_record(),
                   self.datapoint_from,
                   None)
        )
        if not spot_records:
            logger.warning('empty spot record from JianYanYuanData')
            return None

        devices: List[Device] = Device.query.all()

        ##########################
        #  deprecated  2020-01-21#
        ##########################

        def record_consumer(queue: Queue):

            def do_record_sr(sr: Dict) -> None:
                """
                record a single spot_record
                `consumer` in threaded_collector
                """
                if sr is None:
                    return

                device = next(
                    filter(lambda d: d.device_name == sr.get('device_name'),
                           devices))
                sr["device"] = device

                ModelOperations.Add.add_spot_record(sr)

            while not queue.empty():
                do_record_sr(queue.get())

        ##########################
        #  deprecated  2020-01-21#
        ##########################

        def record_fetching_worker(
                queue: Queue,  # T

                # lazy iter with only one ele.
                jobs: Job,
                lock: threading.Lock) -> None:
            """
            fetch data from response queue.

            `worker` in in threaded_collector
            """

            # @DEBUG: problem happens in eval
            spot_record_generator = jobs()

            logger.info('process from device {}'.format(spot_record_generator))

            # None generator. might be a broken api or connection error.
            if spot_record_generator is None:
                logger.warning('empty device{}'.format(spot_record_generator))
                return
            # exthaust map without create a list.
            try:
                while True:
                    sr = next(spot_record_generator)
                    with lock:
                        queue.put(sr)

            except StopIteration:
                ...

        logger.info('<Main Thread> Start to fetch data...')

        thread_fetcher(jobs=spot_records,
                       max_thread=self.datapoint_thread_num,
                       fetcher=record_fetching_worker,
                       consumer=record_consumer,
                       after_consume_hook=commit)

        logger.info('finshed loading spot record')


def db_init(full=False):

    logger.info('<Main Thread> Start to load project informations ... ')

    load_climate_area()
    load_location()
    load_projects()

    logger.info('<Main Thread> Finsih loading project informations ... ')
    if full:
        logger.info('<Main Thread> Start to load devices and spot record... ')

        load_data = JianyanyuanLoadFull(
            datapoint_thread_num=50, datapoint_from=1000)
        load_data.load_spots()
        load_data.load_devices()
        load_data.load_spot_records()

        logger.info('<Main Thread> Finsihed loading Data ... ')
        load_data.close()
