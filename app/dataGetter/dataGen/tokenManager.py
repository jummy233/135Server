from typing import Callable, Generic, TypeVar, Optional
from threading import Thread, Lock, Condition
from timeutils.time import PeriodicTimer
import logging
from contextlib import contextmanager


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
        self._refreshed = Condition()
        self._is_refresing = False
        self._quit = False

    def _init_token(self, gettoken: TokenGetter[T]):
        self._gettoken = gettoken
        self._token = self._gettoken()

    def _init_timer(self):
        """
        we want to be able to join the timer since SpotData
        might exit in the middle of the runtime.
        """
        self.timer = PeriodicTimer(self._expires_in, daemon=False)

    @property
    def token(self):
        return self._token

    @contextmanager
    def valid_token_ctx(self):
        """
        Ensure a valid token even it's between refreshing
        """
        with self._refreshed:
            if self._is_refresing:
                self._refreshed.wait()
        try:
            yield self.token
        finally:
            ...

    def start(self):
        self.t = Thread(target=self.run)
        self.timer.start()
        self.t.start()

    def run(self):
        while True:
            # print(self.token)  # NOTE DEBUG
            if self._quit:
                break
            self.timer.wait_for_tick()
            self._is_refresing = True
            with self._refreshed:
                self._refreshed.notify_all()
                self._refresh()
            self._is_refresing = False

    def __del__(self):
        self.close()

    def close(self):
        self._quit = True
        self.timer.close()
        self.t.join()

    def _refresh(self):
        logging.debug("refreshing token")
        self._token = self._gettoken()
