"""
Organize database and do some data analysis.
"""
from flask import Flask
from app.analysis.dataType import Analysis, Organize
from typing import List


class AnalysisEngine:
    """
    maintain a list of database related tasks
    """
    def __init__(self):
        ...

    def init_app(self, app: Flask):
        self.app = app

    def register(self, ):
        """ register a task """
        ...

    def unregister(self, ):
        """ unregister a task """
        ...

    def show_task_list(self) -> List:
        """ show the current task list """
        ...

    def run(self, ):
        """ run the """
        ...

