from typing import List, Union, Iterable
from abc import ABC, abstractmethod
from flask import Flask


class Analysis:
    @abstractmethod
    def feed(self, data: Iterable):
        """ feed data needed for the algorithm """

    @abstractmethod
    def run(self, *args, **kwargs):
        """ run the analysis """


class Organize:
    """
    Database organization task.
    certain tasks will modify database status.
    """
    @abstractmethod
    def __init__(self, app: Flask):
        self.app = app

    @abstractmethod
    def run(self, *args, **kwargs):
        """ run the database orgization task """


