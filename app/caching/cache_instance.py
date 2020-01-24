"""
Need to run under app_context for database access.
"""
from __future__ import annotations
from flask import Flask
from .caching import empty_cache, is_cache_empty, Cache
from typing import Optional, Type
import logging


class CacheInstance:

    # expensive !
    def __init__(self):

        # def cache_init_error_info(f):
        #     logging.debug('cache init error')
        #     return f

        self.is_init: bool = False

        self._global_cache: Cache = empty_cache()
        self.global_cacheall = lambda f: f

    @property
    def global_cache(self):
        return self._global_cache

    @global_cache.setter
    def global_cache(self, value: Cache):
        # modify old object rather than assign a new one.
        self._global_cache.update(value)

    def init_app(self, app: Flask):

        with app.app_context():
            # load global cache.
            from .global_cache import init_global_cache
            result = init_global_cache(self)

            if result is None:
                logging.warning('cache is empty')
            else:
                self.is_init = True
                logging.warning('cache instance is ready.')

    def load(self) -> Optional[CacheInstance]:
        """ guarantee self is loaded """
        if self.is_init:
            return self
        else:
            logging.error('cache instance is not init')
            return None

    def __str__(self) -> str:
        s = '<CacheInstance cache {} {}>'.format(
            self.global_cache.keys() if self.global_cache else None,
            self.global_cacheall)
        return s


