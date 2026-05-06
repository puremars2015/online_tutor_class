from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Admin, Course, CourseCategory, UserCourse, Payment

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    purchases = user.purchases.all()
    payments = user.payments.order_by(Payment.created_at.desc()).limit(50).all()

    return jsonify({
        'user': user.to_dict(),
        'purchases': [p.to_dict() for p in purchases],
        'payments': [p.to_dict() for p in payments]
    }), 200


@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    if 'level' in data:
        user.level = data['level']
    if 'balance' in data:
        user.balance = data['balance']
    if 'is_active' in data:
        user.is_active = data['is_active']

    db.session.commit()

    return jsonify({'message': 'User updated', 'user': user.to_dict()}), 200


@bp.route('/users/<int:user_id>/balance', methods=['POST'])
@jwt_required()
def adjust_balance(user_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    amount = float(data.get('amount', 0))

    user.balance += amount

    payment = Payment(
        user_id=user.id,
        amount=amount,
        payment_type='adjustment',
        status='completed',
        note=data.get('note', 'Admin adjustment')
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Balance adjusted',
        'new_balance': float(user.balance)
    }), 200


@bp.route('/users/<int:user_id>/courses', methods=['POST'])
@jwt_required()
def add_user_course(user_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    course_id = data.get('course_id')

    course = Course.query.filter_by(id=course_id, is_deleted=False).first()
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    existing = UserCourse.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing:
        existing.is_paid = True
        db.session.commit()
        return jsonify({'message': 'Course access granted', 'purchase': existing.to_dict()}), 200

    purchase = UserCourse(
        user_id=user_id,
        course_id=course_id,
        is_paid=True
    )

    course.enrolled_count += 1

    db.session.add(purchase)
    db.session.commit()

    return jsonify({'message': 'Course added', 'purchase': purchase.to_dict()}), 201


@bp.route('/users/<int:user_id>/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
def remove_user_course(user_id, course_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    purchase = UserCourse.query.filter_by(user_id=user_id, course_id=course_id).first()
    if not purchase:
        return jsonify({'error': 'Purchase record not found'}), 404

    purchase.is_paid = False
    db.session.commit()

    return jsonify({'message': 'Course access revoked'}), 200


@bp.route('/courses/all', methods=['GET'])
@jwt_required()
def get_all_courses():
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    courses = Course.query.filter_by(is_deleted=False).order_by(Course.created_at.desc()).all()
    return jsonify([c.to_dict() for c in courses]), 200


@bp.route('/courses/<int:course_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_course(course_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    course.is_active = not course.is_active
    db.session.commit()

    return jsonify({
        'message': f'Course {"activated" if course.is_active else "deactivated"}',
        'course': course.to_dict()
    }), 200


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    total_users = User.query.count()
    total_courses = Course.query.filter_by(is_deleted=False).count()
    active_courses = Course.query.filter_by(is_deleted=False, is_active=True).count()
    total_enrollments = UserCourse.query.filter_by(is_paid=True).count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_type.in_(['purchase', 'recharge', 'deposit']),
        Payment.status == 'completed'
    ).scalar() or 0

    return jsonify({
        'total_users': total_users,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_enrollments': total_enrollments,
        'total_revenue': float(total_revenue)
    }), 200