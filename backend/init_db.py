from app import create_app, db
from app.models import User, Admin, CourseCategory, Course

app = create_app()

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(email='admin@example.com').first():
        from app import bcrypt
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Admin(
            email='admin@example.com',
            password_hash=hashed,
            username='系統管理員'
        )
        db.session.add(admin)

    if not CourseCategory.query.first():
        categories = [
            CourseCategory(name='網頁', sort_order=1),
            CourseCategory(name='docker', sort_order=2),
            CourseCategory(name='openclaw', sort_order=3),
            CourseCategory(name='opencode', sort_order=4),
            CourseCategory(name='claude cowork', sort_order=5),
            CourseCategory(name='llm訓練與架設', sort_order=6),
        ]
        for cat in categories:
            db.session.add(cat)

        db.session.commit()
        print('資料庫初始化完成！')
        print('預設管理員: admin@example.com / admin123')