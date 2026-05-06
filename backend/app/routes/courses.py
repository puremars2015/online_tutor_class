from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Course, CourseCategory, UserCourse, User

bp = Blueprint('courses', __name__, url_prefix='/api/courses')

@bp.route('/categories', methods=['GET'])
def get_categories():
    categories = CourseCategory.query.filter_by().order_by(CourseCategory.sort_order).all()
    return jsonify([c.to_dict() for c in categories]), 200


@bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    category = CourseCategory(
        name=data['name'],
        description=data.get('description'),
        sort_order=data.get('sort_order', 0)
    )

    db.session.add(category)
    db.session.commit()

    return jsonify(category.to_dict()), 201


@bp.route('/', methods=['GET'])
def get_courses():
    category_id = request.args.get('category_id', type=int)
    is_active = request.args.get('is_active', 'true').lower() == 'true'

    query = Course.query.filter_by(is_deleted=False)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if is_active:
        query = query.filter_by(is_active=True)

    courses = query.order_by(Course.created_at.desc()).all()

    return jsonify([c.to_dict() for c in courses]), 200


@bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.query.filter_by(id=course_id, is_deleted=False).first()

    if not course:
        return jsonify({'error': 'Course not found'}), 404

    return jsonify(course.to_dict()), 200


@bp.route('/', methods=['POST'])
@jwt_required()
def create_course():
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    course = Course(
        category_id=data['category_id'],
        title=data['title'],
        description=data.get('description'),
        content=data.get('content'),
        price=data['price'],
        image_url=data.get('image_url'),
        video_path=data.get('video_path')
    )

    db.session.add(course)
    db.session.commit()

    return jsonify(course.to_dict()), 201


@bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    data = request.get_json()

    if 'category_id' in data:
        course.category_id = data['category_id']
    if 'title' in data:
        course.title = data['title']
    if 'description' in data:
        course.description = data['description']
    if 'content' in data:
        course.content = data['content']
    if 'price' in data:
        course.price = data['price']
    if 'image_url' in data:
        course.image_url = data['image_url']
    if 'video_path' in data:
        course.video_path = data['video_path']
    if 'is_active' in data:
        course.is_active = data['is_active']

    db.session.commit()

    return jsonify(course.to_dict()), 200


@bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    identity = get_jwt_identity()
    if identity['type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    course.is_deleted = True
    db.session.commit()

    return jsonify({'message': 'Course deleted'}), 200


@bp.route('/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(identity['id'])
    course = Course.query.filter_by(id=course_id, is_deleted=False).first()

    if not course:
        return jsonify({'error': 'Course not found'}), 404

    existing = UserCourse.query.filter_by(user_id=user.id, course_id=course_id).first()
    if existing:
        return jsonify({'error': 'Already enrolled'}), 400

    return jsonify({
        'message': 'Ready to checkout',
        'course': course.to_dict(),
        'user_balance': float(user.balance)
    }), 200


@bp.route('/video/<path:filename>', methods=['GET'])
@jwt_required()
def serve_video(filename):
    identity = get_jwt_identity()
    if identity['type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 403

    user_id = identity['id']
    course_id = request.args.get('course_id', type=int)

    if not course_id:
        return jsonify({'error': 'Course ID required'}), 400

    purchase = UserCourse.query.filter_by(user_id=user_id, course_id=course_id, is_paid=True).first()
    if not purchase:
        return jsonify({'error': 'Not purchased'}), 403

    return send_from_directory('../media/courses', filename)