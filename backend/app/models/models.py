from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.Unicode(80), nullable=False)
    phone = db.Column(db.Unicode(20))
    level = db.Column(db.Integer, default=1)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    purchases = db.relationship('UserCourse', back_populates='user', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'phone': self.phone,
            'level': self.level,
            'balance': float(self.balance) if self.balance else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.Unicode(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class CourseCategory(db.Model):
    __tablename__ = 'course_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    description = db.Column(db.UnicodeText)
    sort_order = db.Column(db.Integer, default=0)

    courses = db.relationship('Course', back_populates='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order
        }


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('course_categories.id'), nullable=False)
    title = db.Column(db.Unicode(200), nullable=False)
    description = db.Column(db.UnicodeText)
    content = db.Column(db.UnicodeText)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.Unicode(500))
    video_path = db.Column(db.Unicode(500))
    enrolled_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('CourseCategory', back_populates='courses')
    purchases = db.relationship('UserCourse', back_populates='course', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'price': float(self.price),
            'image_url': self.image_url,
            'video_path': self.video_path,
            'enrolled_count': self.enrolled_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserCourse(db.Model):
    __tablename__ = 'user_courses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='purchases')
    course = db.relationship('Course', back_populates='purchases')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'is_paid': self.is_paid
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.Unicode(20), nullable=False)
    status = db.Column(db.Unicode(20), default='pending')
    transaction_id = db.Column(db.Unicode(100))
    note = db.Column(db.UnicodeText)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'payment_type': self.payment_type,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }