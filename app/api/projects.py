from flask import jsonify
from . import api
from ..models import Project


@api.route('/projects', methods=['GET'])
def get_projects():
    projs = jsonify([p.to_json() for p in Project.query.all()])
    return projs


@api.route('/project/<proj_id>', methods=['GET'])
def get_project(proj_id):
    proj = Project.query.get_or_404(proj_id)
    return jsonify(proj.to_json())






