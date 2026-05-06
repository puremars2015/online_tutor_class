from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models import User, Admin

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register/user', methods=['POST'])
def register_user():
    data = request.get_json()

    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    user = User(
        email=data['email'],
        password_hash=hashed_password,
        username=data['username'],
        phone=data.get('phone')
    )

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity={'type': 'user', 'id': user.id})

    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201


@bp.route('/register/admin', methods=['POST'])
def register_admin():
    data = request.get_json()

    if Admin.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    admin = Admin(
        email=data['email'],
        password_hash=hashed_password,
        username=data['username']
    )

    db.session.add(admin)
    db.session.commit()

    access_token = create_access_token(identity={'type': 'admin', 'id': admin.id})

    return jsonify({
        'message': 'Admin registered successfully',
        'access_token': access_token,
        'admin': admin.to_dict()
    }), 201


@bp.route('/login/user', methods=['POST'])
def login_user():
    data = request.get_json()

    user = User.query.filter_by(email=data.get('email')).first()

    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity={'type': 'user', 'id': user.id})
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@bp.route('/login/admin', methods=['POST'])
def login_admin():
    data = request.get_json()

    admin = Admin.query.filter_by(email=data.get('email')).first()

    if admin and bcrypt.check_password_hash(admin.password_hash, data['password']):
        access_token = create_access_token(identity={'type': 'admin', 'id': admin.id})
        return jsonify({
            'access_token': access_token,
            'admin': admin.to_dict()
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200