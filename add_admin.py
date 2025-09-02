from app import app, db
from app.models import Admin

with app.app_context():
    username = 'admin'
    password = 'admin123'  # Change this after first login for security
    if not Admin.query.filter_by(username=username).first():
        admin = Admin(username=username, password=password)
        db.session.add(admin)
        db.session.commit()
        print('Super admin created.')
    else:
        print('Super admin already exists.')
