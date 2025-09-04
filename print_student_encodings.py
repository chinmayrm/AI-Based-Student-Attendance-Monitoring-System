from app import app, db
from app.models import Student
import numpy as np

def print_student_encodings():
    with app.app_context():
        students = Student.query.all()
        for s in students:
            if s.face_encoding and len(s.face_encoding) > 0:
                try:
                    arr = np.frombuffer(s.face_encoding, dtype=np.float64)
                    print(f"{s.usn}: encoding shape {arr.shape}")
                except Exception as e:
                    print(f"{s.usn}: ERROR decoding encoding: {e}")
            else:
                print(f"{s.usn}: NO ENCODING")

if __name__ == '__main__':
    print_student_encodings()
