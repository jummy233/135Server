"""
Higher level db api build on top of modelOperations.
provide coroutine styles api that can be easily reused and
pickled.
"""

from app.modelOperations import ModelOperations, commit
from app.dataGetter.dataGen.dataType import SpotRecord
from app.dataGetter.dataGen.dataType import Device

from flask import Flask
from typing import Generator
from typing import cast
from typing import Dict
from typing import TypeVar
from typing import Callable
from typing import Union
from logger import make_logger
from functools import partial
import logging

logger = logging.getLogger(__name__)
Co_T = Union[SpotRecord, Device]


def _model_co(op: Callable) -> Generator[None, Co_T, None]:
    """
    a family of coroutines to interact with the database.
    op is a method from `modelOperations`.
    """
    while True:
        data: Co_T = yield
        try:
            op(data)
            commit()
        except Exception:
            # should never stop
            logger.warning('modelcoro: error when add spot record')


record_co: Generator[None, SpotRecord, None]
record_co = _model_co(ModelOperations.Add.add_spot_record)
record_send = record_co.send

device_co: Generator[None, Device, None]
device_co = _model_co(ModelOperations.Add.add_device)
device_send = device_co.send
