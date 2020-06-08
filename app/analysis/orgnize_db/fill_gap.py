"""
Fill the gap between time unit.
Some apis only report data when there is a change in
value larger than certain threshold.

This taks will find out those holes in db and fill in
with a reasonable value
"""
from app.analysis.dataType import Organize


class FillGap(Organize):
    def run(self, *args, **kwargs):
        ...
