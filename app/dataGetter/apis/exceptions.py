import urllib3
import requests
import http
from functools import wraps
from logger import make_logger
import os


logger = make_logger(__name__, 'dataGetter_log')


def connection_exception(f):
    @wraps(f)
    def call(*args, **kwargs):
        result = None
        try:
            result = f(*args, **kwargs)
        except urllib3.response.ProtocolError as e:
            logger.error(f'[urllib3] {f.__name__}', e)
        except http.client.IncompleteRead as e:
            logger.error(f'[http] {f.__name__}', e)
        except requests.models.ChunkedEncodingError as e:
            logger.error(f'[requests] {f.__name__}', e)
        except BaseException as e:
            logger.error(
                'some Exception happend when send and receiving data. %s ', e)
        finally:
            # if os.environ.get('DEBUG_DG_API'):
            #     print("==========>")
            #     print(f)
            #     print("==========>")
            return result
    return call
