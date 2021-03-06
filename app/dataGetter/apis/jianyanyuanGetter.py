import http
import json
import urllib.parse
from hashlib import md5, sha1
import threading
from operator import itemgetter
from typing import (Dict, Iterator, List, NewType, Optional, Tuple, TypedDict,
                    Union, cast)

import requests
import urllib3

from .exceptions import connection_exception
from logger import make_logger
from timeutils.time import currentTimestamp


logger = make_logger('JianYanYuanGetter', 'dataGetter_log')


################
#  auth types  #
################

Token = NewType('Token', str)
Uid = NewType('Uid', str)
# Necessary value for authenticion.
AuthToken = NewType('AuthToken', Tuple[Token, Uid])

AuthData = (
    TypedDict(
        'AuthData',
        {
            'account': str,
            'password': str,
            'base_url': str,
            'auth_url': str,
            'device_url': str,
            'attr_url': str,
            'datapoint_url': str
        }))

#######################
#  param type  #
#######################
DeviceParam = (
    TypedDict('DeviceParam',
              {'companyId': Optional[str],
               'start': Optional[int],
               'size': Optional[int],
               'pageNo': Optional[int],
               'pageSize': Optional[int]}))

DataPointParam = (
    TypedDict(
        'DataPointParam',
        {
            'gid': Optional[str],
            'did': Optional[str],
            # list of attrs. string in form "<aid>, <aid>"
            'aid': Optional[str],
            'startTime': Optional[str],
            'endTime': Optional[str]
        }))  # time format: yyyy-MM-ddTHH:mm:ss

Gid = NewType('Gid', str)

###############
#  Result Type#
###############

DeviceResult = NewType('DeviceResult', Dict)
AttrResult = NewType('AttrResult', Dict)
DataPointResult = TypedDict(
    'DataPointResult',
    {
        'as': Dict,
        'key': str
    })


#############
#  attr ids #
#############
attrs: Dict = {
    # data collectors.
    'pm25': '1',
    'co2': '2',
    'temperature': '3',
    'humidity': '4',

    # there are two ac power aid for differnt devices.
    'ac_power1': '155',
    'ac_power2': '32'
}


@connection_exception
def get_token(auth: AuthData, timestamp: Optional[int] = None) \
        -> Optional[AuthToken]:
    """
    get token
    """
    (account, password, base_url, auth_url) = itemgetter(
        'account', 'password', 'base_url', 'auth_url')(auth)

    # construct request
    url = urllib.parse.urljoin(base_url, auth_url)
    timestamp = cast(int, timestamp or currentTimestamp(digit=13))

    md5pw = md5(password.encode('ascii')).hexdigest()
    sign = md5((md5pw + str(timestamp)).encode('ascii')).hexdigest()

    request_data = {
        'account': account,
        'sign': sign,
        'ts': timestamp,
        'ukey': ''
    }
    response: requests.Response
    response = requests.post(url, json=request_data)

    if response.status_code != 200:
        logger.error('error response %s', response)
        return None
    rj = response.json()
    return AuthToken((rj['token'], rj['uid']))


@connection_exception
def get_device_list(auth: AuthData,
                    authtoken: Optional[AuthToken],
                    params: Dict = {}) -> Optional[List[DeviceResult]]:
    """
    (token + params) return device list as dict by given param
    only return the Array with data.
    """

    method = 'POST'
    timestamp: int = currentTimestamp(13)
    params_json = json.dumps(params)
    if not authtoken:
        logger.error('token is None')
        return None
    token, uid = authtoken

    # construct request
    base_url, device_url = itemgetter('base_url', 'device_url')(auth)
    url = urllib.parse.urljoin(base_url, device_url)

    sign = sha1((method
                 + device_url
                 + params_json
                 + str(timestamp)
                 + token).encode('ascii')).hexdigest()

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'ts': str(timestamp),
        'uid': uid,
        'sign': sign
    }

    response: requests.Response
    response = requests.post(url, data=params_json, headers=headers)

    rj: Dict = response.json()
    logger.debug("[jianyanyuan get device list] %s", response)

    if response.status_code != 200:
        logger.error('error response %s', response)
        return None

    if rj['code'] != 0:
        logger.error('error return code: %s', rj)
        return None
    return rj['data']['devs']


@connection_exception
def get_device_attrs(
        auth: AuthData,
        authtoken: Optional[AuthToken],
        gid: str) -> Optional[List[AttrResult]]:
    """
    (token + attrId) return paramter attr table
    only return the Array with data.
    """

    method = 'GET'
    timestamp: int = currentTimestamp(13)

    if not authtoken:
        logger.error('token is None')
        return None
    token, uid = authtoken

    # construct request.
    base_url, attr_url = itemgetter('base_url', 'attr_url')(auth)
    attr_url_gid: str = urllib.parse.urljoin(attr_url, gid)
    url = urllib.parse.urljoin(base_url, attr_url_gid)

    sign = sha1(
        (method
         + attr_url_gid
         + str(timestamp)
         + token).encode('ascii')).hexdigest()

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'ts': str(timestamp),
        'uid': uid,
        'sign': sign}

    response: requests.Response
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error('error response %s', response)
        return None

    logger.debug("[jianyanyuan get attrs] %s", response.content)
    rj: Dict = response.json()
    if rj['code'] != 0:
        logger.error('error return code: ', rj)
        return None
    return rj['data']['jsonArray']


@connection_exception
def get_data_points(
        auth: AuthData,
        authtoken: Optional[AuthToken],
        params: DataPointParam) -> Optional[List[DataPointResult]]:

    method = 'POST'
    timestamp: int = currentTimestamp(13)
    param_json = json.dumps(params)
    if not authtoken:
        logger.error('token is None')
        return None
    token, uid = authtoken

    # construct request.
    base_url, datapoint_url = itemgetter('base_url', 'datapoint_url')(auth)
    url = urllib.parse.urljoin(base_url, datapoint_url)

    sign = sha1((method
                 + datapoint_url
                 + param_json
                 + str(timestamp)
                 + token).encode('ascii')).hexdigest()

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'ts': str(timestamp),
        'uid': uid,
        'sign': sign}

    response: requests.Response
    response = requests.post(url, data=param_json, headers=headers)

    logger.debug("[jianyanyuan get datapoints] %s", response)

    if response.status_code != 200:
        logger.error('error response %s %s', response, response.request.body)
        return None

    rj = response.json()

    if rj['code'] != 0:
        logger.error(
            'server error return code : %s %s, \ntoken: %s',
            rj, response.request.body, str(authtoken))
        return None

    # notice some apis are broken and return attrs
    if 'asData' not in rj['data'].keys():
        logger.warning(
            'warning, broken api, no data in datapoint return keys: %s %s',
            rj['code'],
            response.request.body)
        return None

    # logger.debug('correct authtoken %s', str(authtoken))
    return rj['data']['asData']
