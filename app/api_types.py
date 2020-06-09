from typing import List
from typing import Dict
from typing import TypedDict
from typing import Union
from typing import Optional
import enum


class ReturnCode(enum.Enum):
    OK = 0
    BAD_REQUEST = 1
    NO_DATA = 2


ApiResponse = TypedDict(
    'ApiResponse',
    {
        'status': int,
        'data': Union[List, Dict],
        'message': Optional[str]
    },
    total=False)


ApiRequest = TypedDict(
    'ApiRequest',
    {
        'request': Union[Dict, List, str]
    })

PagingRequest = TypedDict(
    'PagingRequest',
    {
        'size': int,
        'pageNo': int
    })


def is_ApiRequest(data: Optional[Dict]) -> bool:
    if not data:
        return False
    return 'request' in data.keys()

