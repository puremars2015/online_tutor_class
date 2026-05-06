from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Payment, UserCourse, User, Course

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    data = request.get_json()
    course_id = data.get('course_id')

    course = Course.query.filter_by(id=course_id, is_deleted=False).first()
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    existing = UserCourse.query.filter_by(user_id=user.id, course_id=course_id).first()
    if existing:
        return jsonify({'error': 'Already purchased'}), 400

    if float(user.balance) < float(course.price):
        return jsonify({
            'error': 'Insufficient balance',
            'required': float(course.price),
            'current': float(user.balance)
        }), 400

    user.balance -= course.price

    purchase = UserCourse(
        user_id=user.id,
        course_id=course_id,
        is_paid=True
    )

    course.enrolled_count += 1

    payment = Payment(
        user_id=user.id,
        amount=-float(course.price),
        payment_type='purchase',
        status='completed',
        note=f'Purchase course: {course.title}'
    )

    db.session.add(purchase)
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Purchase successful',
        'purchase': purchase.to_dict(),
        'remaining_balance': float(user.balance)
    }), 200


@bp.route('/notify', methods=['POST'])
def payment_notify():
    data = request.get_json()

    transaction_id = data.get('transaction_id')
    amount = float(data.get('amount', 0))
    user_id = data.get('user_id')

    if not transaction_id or not user_id:
        return jsonify({'error': 'Invalid notification'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing = Payment.query.filter_by(transaction_id=transaction_id).first()
    if existing:
        return jsonify({'message': 'Already processed'}), 200

    user.balance += amount

    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type='deposit',
        status='completed',
        transaction_id=transaction_id,
        note=data.get('note', 'External deposit')
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Deposit successful',
        'new_balance': float(user.balance)
    }), 200