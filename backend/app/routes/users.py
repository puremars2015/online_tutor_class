from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Payment

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    if 'username' in data:
        user.username = data['username']
    if 'phone' in data:
        user.phone = data['phone']

    db.session.commit()

    return jsonify({'message': 'Profile updated', 'user': user.to_dict()}), 200


@bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    return jsonify({'balance': float(user.balance) if user.balance else 0.0}), 200


@bp.route('/balance/recharge', methods=['POST'])
@jwt_required()
def recharge_balance():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    data = request.get_json()
    amount = float(data.get('amount', 0))

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    user.balance += amount

    payment = Payment(
        user_id=user.id,
        amount=amount,
        payment_type='recharge',
        status='completed',
        note='Balance recharge'
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Balance recharged',
        'balance': float(user.balance),
        'payment': payment.to_dict()
    }), 200


@bp.route('/purchases', methods=['GET'])
@jwt_required()
def get_purchases():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    purchases = user.purchases.all()

    return jsonify([p.to_dict() for p in purchases]), 200


@bp.route('/payment-history', methods=['GET'])
@jwt_required()
def get_payment_history():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    payments = user.payments.order_by(Payment.created_at.desc()).all()

    return jsonify([p.to_dict() for p in payments]), 200