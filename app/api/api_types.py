from typing import (
    List, Dict, NewType, TypedDict, Callable,
    Union, Optional)
from functools import wraps
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



