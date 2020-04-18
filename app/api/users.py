from flask import jsonify
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from . import api


@api.route('/users', methods=['GET'])
def get_users():
    users = jsonify([p.to_json() for p in User.query.all()])
    return users


@api.route('/user/<uid>', methods=['GET'])
def get_user(uid):
    user = User.query.get_or_404(uid)
    return jsonify(user.to_json())


# NOTE: need permission to delete users.
@api.route('/users/<uid>', methods=['DELETE'])
def delete_user(uid):
    u = User.query.filter_by(user_id=uid).first()
    db.session.delete(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
