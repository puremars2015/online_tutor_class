from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from app import db, bcrypt
from app.models import User, Admin, Course, CourseCategory, UserCourse, Payment
from decimal import Decimal

bp = Blueprint('views', __name__)

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def get_current_admin():
    if 'admin_id' in session:
        return Admin.query.get(session['admin_id'])
    return None

@bp.route('/')
def home():
    category_id = request.args.get('category_id', type=int)
    categories = CourseCategory.query.order_by(CourseCategory.sort_order).all()

    query = Course.query.filter_by(is_deleted=False, is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    courses = query.order_by(Course.created_at.desc()).all()

    return render_template('frontend/home.html',
                         courses=courses,
                         categories=categories,
                         selected_category=category_id)

@bp.route('/courses')
def courses():
    category_id = request.args.get('category_id', type=int)
    categories = CourseCategory.query.order_by(CourseCategory.sort_order).all()

    query = Course.query.filter_by(is_deleted=False, is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    courses = query.order_by(Course.created_at.desc()).all()

    return render_template('frontend/courses.html',
                         courses=courses,
                         categories=categories,
                         selected_category=category_id)

@bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.filter_by(id=course_id, is_deleted=False).first_or_404()
    user = get_current_user()
    is_enrolled = False
    if user:
        is_enrolled = UserCourse.query.filter_by(user_id=user.id, course_id=course_id, is_paid=True).first() is not None

    return render_template('frontend/course_detail.html', course=course, is_enrolled=is_enrolled)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = 'user'
            return redirect(url_for('views.home'))

        flash('Email 或密碼錯誤')
        return redirect(url_for('views.login'))

    return render_template('frontend/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('密碼確認不符')
            return redirect(url_for('views.register'))

        if User.query.filter_by(email=email).first():
            flash('Email 已經存在')
            return redirect(url_for('views.register'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, password_hash=hashed, username=username, phone=phone)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        session['user_type'] = 'user'
        return redirect(url_for('views.home'))

    return render_template('frontend/register.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('views.home'))

@bp.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login'))

    purchases = user.purchases.all()
    payments = user.payments.order_by(Payment.created_at.desc()).limit(50).all()

    return render_template('frontend/dashboard.html', user=user, purchases=purchases, payments=payments)

@bp.route('/recharge', methods=['POST'])
def recharge():
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login'))

    amount = float(request.form.get('amount', 0))
    if amount > 0:
        user.balance += amount
        payment = Payment(user_id=user.id, amount=amount, payment_type='recharge', status='completed', note='Balance recharge')
        db.session.add(payment)
        db.session.commit()

    return redirect(url_for('views.dashboard'))

@bp.route('/payment-notify', methods=['POST'])
def payment_notify():
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login'))

    amount = float(request.form.get('amount', 0))
    if amount > 0:
        user.balance += amount
        payment = Payment(user_id=user.id, amount=amount, payment_type='deposit', status='completed', note='External deposit')
        db.session.add(payment)
        db.session.commit()

    return redirect(url_for('views.dashboard'))

@bp.route('/checkout/<int:course_id>', methods=['GET', 'POST'])
def checkout(course_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login'))

    course = Course.query.filter_by(id=course_id, is_deleted=False).first_or_404()

    if request.method == 'POST':
        if user.balance < course.price:
            flash('餘額不足')
            return redirect(url_for('views.checkout', course_id=course_id))

        existing = UserCourse.query.filter_by(user_id=user.id, course_id=course_id).first()
        if existing and existing.is_paid:
            flash('已經購買過此課程')
            return redirect(url_for('views.checkout', course_id=course_id))

        user.balance -= course.price

        purchase = UserCourse(user_id=user.id, course_id=course_id, is_paid=True)
        course.enrolled_count += 1

        payment = Payment(user_id=user.id, amount=-course.price, payment_type='purchase', status='completed', note=f'Purchase course: {course.title}')

        db.session.add(purchase)
        db.session.add(payment)
        db.session.commit()

        flash('購買成功')
        return redirect(url_for('views.dashboard'))

    return render_template('frontend/checkout.html', course=course, balance=user.balance)

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = Admin.query.filter_by(email=email).first()
        if admin and bcrypt.check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session['user_type'] = 'admin'
            return redirect(url_for('views.admin_dashboard'))

        flash('Email 或密碼錯誤')
        return redirect(url_for('views.admin_login'))

    return render_template('backend/admin_login.html')

@bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('views.home'))

@bp.route('/admin')
def admin_dashboard():
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    total_users = User.query.count()
    total_courses = Course.query.filter_by(is_deleted=False).count()
    active_courses = Course.query.filter_by(is_deleted=False, is_active=True).count()
    total_enrollments = UserCourse.query.filter_by(is_paid=True).count()

    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_type.in_(['purchase', 'recharge', 'deposit']),
        Payment.status == 'completed'
    ).scalar() or 0

    stats = {
        'total_users': total_users,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_enrollments': total_enrollments,
        'total_revenue': float(total_revenue)
    }

    return render_template('backend/admin_dashboard.html', admin=admin, stats=stats)

@bp.route('/admin/users')
def admin_users():
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('backend/admin_users.html', users=users)

@bp.route('/admin/api/users/<int:user_id>')
def admin_api_user(user_id):
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get_or_404(user_id)
    return jsonify({
        'user': user.to_dict(),
        'purchases': [p.to_dict() for p in user.purchases.all()],
        'payments': [p.to_dict() for p in user.payments.order_by(Payment.created_at.desc()).limit(50).all()]
    })

@bp.route('/admin/users/<int:user_id>/adjust', methods=['GET', 'POST'])
def admin_adjust_user(user_id):
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        note = request.form.get('note', '')

        user.balance += amount
        payment = Payment(user_id=user.id, amount=amount, payment_type='adjustment', status='completed', note=note)
        db.session.add(payment)
        db.session.commit()

        flash(f'餘額已調整 {amount} 元')
        return redirect(url_for('views.admin_users'))

    return render_template('backend/admin_user_adjust.html', user=user)

@bp.route('/admin/users/<int:user_id>/courses', methods=['GET', 'POST'])
def admin_user_courses(user_id):
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        course = Course.query.get(course_id)
        if course:
            existing = UserCourse.query.filter_by(user_id=user_id, course_id=course_id).first()
            if existing:
                existing.is_paid = True
            else:
                purchase = UserCourse(user_id=user_id, course_id=course_id, is_paid=True)
                db.session.add(purchase)
                course.enrolled_count += 1
            db.session.commit()
        return redirect(url_for('views.admin_user_courses', user_id=user_id))

    purchases = user.purchases.all()
    all_courses = Course.query.filter_by(is_deleted=False, is_active=True).all()
    return render_template('backend/admin_user_courses.html', user=user, purchases=purchases, all_courses=all_courses)

@bp.route('/admin/courses')
def admin_courses():
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    courses = Course.query.filter_by(is_deleted=False).order_by(Course.created_at.desc()).all()
    categories = {c.id: c.name for c in CourseCategory.query.all()}

    course_list = []
    for c in courses:
        course_list.append({
            'id': c.id,
            'title': c.title,
            'category_name': categories.get(c.category_id, '-'),
            'price': c.price,
            'enrolled_count': c.enrolled_count,
            'is_active': c.is_active
        })

    return render_template('backend/admin_courses.html', courses=course_list)

@bp.route('/admin/upload/image', methods=['POST'])
def admin_upload_image():
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'Unauthorized'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if ext not in allowed_ext:
        return jsonify({'error': 'Invalid file type'}), 400

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({'url': f'/media/{filename}'}), 200


@bp.route('/admin/courses/new', methods=['GET', 'POST'])
@bp.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def admin_course_form(course_id=None):
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    course = Course.query.get(course_id) if course_id else None
    categories = CourseCategory.query.order_by(CourseCategory.sort_order).all()
    action = f'/admin/courses/{course_id}/edit' if course else '/admin/courses/new'

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        title = request.form.get('title')
        description = request.form.get('description')
        content = request.form.get('content')
        price = float(request.form.get('price', 0))
        image_url = request.form.get('image_url')

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext in allowed_ext:
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = f'/media/{filename}'

        if course:
            course.category_id = category_id
            course.title = title
            course.description = description
            course.content = content
            course.price = price
            if image_url:
                course.image_url = image_url
        else:
            course = Course(category_id=category_id, title=title, description=description, content=content, price=price, image_url=image_url)
            db.session.add(course)

        db.session.commit()
        flash('課程已儲存')
        return redirect(url_for('views.admin_courses'))

    return render_template('backend/admin_course_form.html', course=course, categories=categories, action=action)

@bp.route('/admin/courses/<int:course_id>/toggle')
def admin_toggle_course(course_id):
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    course = Course.query.get_or_404(course_id)
    course.is_active = not course.is_active
    db.session.commit()

    return redirect(url_for('views.admin_courses'))

@bp.route('/admin/courses/<int:course_id>/delete')
def admin_delete_course(course_id):
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    course = Course.query.get_or_404(course_id)
    course.is_deleted = True
    db.session.commit()

    return redirect(url_for('views.admin_courses'))

@bp.route('/admin/categories')
def admin_categories():
    admin = get_current_admin()
    if not admin:
        return redirect(url_for('views.admin_login'))

    categories = CourseCategory.query.order_by(CourseCategory.sort_order).all()
    return render_template('backend/admin_categories.html', categories=categories)