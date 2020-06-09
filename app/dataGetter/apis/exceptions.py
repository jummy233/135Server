import urllib3
import requests
import http
from functools import wraps
from logger import make_logger


logger = make_logger(__name__, 'dataGetter_log')


def connection_exception(f):
    @wraps(f)
    def call(*args, **kwargs):
        result = None
        try:
            result = f(*args, **kwargs)
        except urllib3.response.ProtocolError as e:
            logger.error('[urllib3] Protocal error %s ', e)
        except http.client.IncompleteRead as e:
            logger.error('[http] IncompleteRead error %s ', e)
        except requests.models.ChunkedEncodingError as e:
            logger.error('[requests ]ChunkedEncodingError %s ', e)
        except BaseException as e:
            logger.error(
                'some Exception happed when send and receiving data. %s ', e)
        finally:
            return result
    return call



