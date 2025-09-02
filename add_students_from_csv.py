import csv
from app import app, db
from app.models import Student

csv_path = 'studentsaiml.csv.txt'  # Update if your file is renamed
DEFAULT_SEMESTER = 1  # Change if needed

def reset_and_add_students():
    with app.app_context():
        # Delete all students
        Student.query.delete()
        db.session.commit()
        print("All students deleted.")
        # Add new students from CSV
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            added = 0
            for row in reader:
                usn = row['USN'].strip()
                name = row['NAME OF THE STUDENT'].strip()
                semester = DEFAULT_SEMESTER
                student = Student(name=name, usn=usn, semester=semester, face_encoding=b'', photo_filename=None)
                db.session.add(student)
                added += 1
            db.session.commit()
        print(f"Added {added} students from CSV.")

if __name__ == '__main__':
    reset_and_add_students()
