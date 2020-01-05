from typing import List, Dict, NewType, TypedDict, Callable
from functools import wraps


def route_url(url: str, methods: List):
    def decorator(func: Callable):
        @wraps(func)
        def routed(*args, **kwargs):
            return func(*args, **kwargs)
        return routed
    return decorator


@route_url('/view/project/generic', methods=['POST'])
class ProjectGeneric(TypedDict):
    project_name: str


@route_url('/view/<pid>/spots', methods=["GET", "POST"])
class SpotGeneric(TypedDict):
    pass


@route_url('/api/v1/spot', methods=['POST'])
class SpotPaged(TypedDict):
    pass



