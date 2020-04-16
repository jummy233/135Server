from typing import Callable, Generic, TypeVar
from threading import Timer, Lock
import logging


T = TypeVar('T')
TokenGetter = Callable[[], T]


class TokenManager(Generic[T]):
    """
    :params gettoken :: () -> Token
    """
    def __init__(self, gettoken: TokenGetter[T], expires_in: int):
        self._init_token(gettoken)
        self._expires_in = expires_in
        self._init_timer()

    def _init_token(self, gettoken: TokenGetter[T]):
        self._gettoken = gettoken
        self._token = self._gettoken()

    def _init_timer(self):
        self.timer = Timer(self._expires_in, self._refresh)

    @property
    def token(self):
        return self._token

    def start(self):
        self.timer.start()

    def close(self):
        self.cleanup()

    def _cleanup(self):
        self.timer.cancel()
        del self.timer

    def _refresh(self):
        logging.debug("refreshing token")
        self._token = self._gettoken()
        self._cleanup()
        self._init_timer()
        self.timer.start()
