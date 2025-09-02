from app import app, db
from app.models import Admin, Teacher, Student, Attendance

with app.app_context():
    db.create_all()
    print('Database initialized.')
