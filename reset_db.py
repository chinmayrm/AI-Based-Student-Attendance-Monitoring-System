from app import app, db
from app.models import Student, Attendance, Teacher, Admin

def reset_database():
    with app.app_context():
        db.create_all()  # Ensure all tables exist
        # Delete all attendance records
        Attendance.query.delete()
        # Delete all students
        Student.query.delete()
        # Delete all teachers
        Teacher.query.delete()
        # Delete all admins
        Admin.query.delete()
        db.session.commit()
        print("All records deleted from Attendance, Student, Teacher, and Admin tables.")

if __name__ == '__main__':
    reset_database()
