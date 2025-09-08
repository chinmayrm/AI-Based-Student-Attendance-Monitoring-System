from flask import send_file, Response
import pandas as pd
from fpdf import FPDF
from flask import render_template, request, redirect, url_for, session, flash
from app import app, db
from app.models import Admin, Teacher, Student, Attendance
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import os
import base64
import io
import numpy as np
from datetime import datetime


# Export attendance report in PDF, CSV, or Excel format
@app.route('/export_attendance/<format>')
def export_attendance(format):
    date_str = request.args.get('date')
    query = Attendance.query
    # Filter by teacher if logged in as teacher
    teacher_id = session.get('teacher_id')
    if teacher_id:
        query = query.filter(Attendance.teacher_id == teacher_id)
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Attendance.date) == date_obj)
        except Exception:
            pass
    records = query.all()
    students = {s.id: s for s in Student.query.all()}
    data = []
    for r in records:
        student = students.get(r.student_id)
        data.append({
            'Student Name': student.name if student else 'Unknown',
            'USN': student.usn if student else 'Unknown',
            'Status': r.status,
            'Subject': r.subject,
            'Date': r.date.strftime('%Y-%m-%d')
        })
    df = pd.DataFrame(data)
    if format == 'csv':
        csv_data = df.to_csv(index=False)
        return Response(csv_data, mimetype='text/csv', headers={"Content-disposition":f"attachment; filename=attendance_{date_str or 'all'}.csv"})
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance')
        output.seek(0)
        return send_file(output, download_name=f"attendance_{date_str or 'all'}.xlsx", as_attachment=True)
    elif format == 'pdf':
        # Define the path to the DejaVuSans.ttf font
        font_path = os.path.join(os.path.dirname(__file__), 'static', 'DejaVuSans.ttf')
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        # Add both regular and bold DejaVu fonts
        pdf.add_font("DejaVu", fname=font_path, uni=True)
        pdf.add_font("DejaVu", style='B', fname=font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
        pdf.cell(0, 10, f"Attendance Report {date_str or ''}", ln=True, align='C')
        # Stretch table to fill page width
        total_width = pdf.w - 2 * pdf.l_margin
        col_widths = [0.32, 0.16, 0.10, 0.28, 0.14]  # Proportions for each column
        col_widths = [round(total_width * p, 2) for p in col_widths]
        row_height = pdf.font_size + 4
        columns = list(df.columns)
        # Bold headings for specific columns
        bold_headings = ['Student Name', 'USN', 'Status', 'Subject', 'Date']
        for idx, col in enumerate(columns):
            width = col_widths[idx] if idx < len(col_widths) else 10
            if col in bold_headings:
                pdf.set_font("DejaVu", 'B', 8)
            else:
                pdf.set_font("DejaVu", size=8)
            align = 'L' if col == 'Student Name' else 'C'
            pdf.cell(width, row_height, str(col), border=1, align=align)
        pdf.ln(row_height)
        # Table rows
        for i in range(len(df)):
            for idx, col in enumerate(columns):
                width = col_widths[idx] if idx < len(col_widths) else 10
                pdf.set_font("DejaVu", size=8)
                if col == 'Status':
                    val = str(df.iloc[i][col])
                    val = 'P' if val == 'Present' else ('A' if val == 'Absent' else val)
                elif col == 'USN':
                    usn = str(df.iloc[i][col])
                    val = usn[-3:] if len(usn) >= 3 else usn
                elif col == 'Date':
                    date_str = str(df.iloc[i][col])
                    parts = date_str.split('-')
                    val = f"{parts[1]}-{parts[2]}" if len(parts) == 3 else date_str
                elif col == 'Student Name':
                    val = str(df.iloc[i][col])  # Do not truncate or alter name
                else:
                    val = str(df.iloc[i][col])
                align = 'L' if col == 'Student Name' else 'C'
                pdf.cell(width, row_height, val, border=1, align=align)
            pdf.ln(row_height)
        pdf_bytes = pdf.output(dest='S')
        pdf_output = io.BytesIO(pdf_bytes)
        return send_file(pdf_output, download_name=f"attendance_{date_str or 'all'}.pdf", as_attachment=True)
    else:
        return "Invalid format", 400
from flask import render_template, request, redirect, url_for, session, flash
from app import app, db
from app.models import Admin, Teacher, Student, Attendance
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import os
import base64
import io
import numpy as np
import cv2
from datetime import datetime

@app.route('/admin/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    teacher = Teacher.query.get_or_404(teacher_id)
    if request.method == 'POST':
        teacher.name = request.form['name']
        teacher.username = request.form['username']
        teacher.subject = request.form['subject']
        password = request.form.get('password')
        if password:
            from werkzeug.security import generate_password_hash
            teacher.password = generate_password_hash(password)
        try:
            db.session.commit()
            flash('Teacher updated successfully!', 'success')
            return redirect(url_for('admin_teachers'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists.', 'danger')
    return render_template('edit_teacher.html', teacher=teacher)

# Teacher logout route
@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('teacher_login'))

# Teacher dashboard route
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher = Teacher.query.get(session['teacher_id'])
    students = Student.query.all()
    return render_template('teacher_dashboard.html', teacher=teacher, students=students)

    image_data = request.form.get('image_data')
    if not image_data:
        flash('No image received.', 'danger')
        return redirect(url_for('mark_attendance'))
    # Decode base64 image
    header, encoded = image_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    # Get all students and their encodings
    students = Student.query.all()
    known_encodings = []
    known_ids = []
    for student in students:
        if student.face_encoding:
            try:
                encoding = np.frombuffer(student.face_encoding, dtype=np.float64)
                known_encodings.append(encoding)
                known_ids.append(student.id)
            except Exception:
                continue
    # Detect faces in uploaded image
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Face recognition logic removed for local demo
    # Mark attendance for selected date
    attendance_date_str = request.form.get('attendance_date')
    if attendance_date_str:
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('mark_attendance'))
    else:
        attendance_date = datetime.now().date()
    for student in students:
        status = 'Present' if student.id in present_ids else 'Absent'
        attendance_record = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.teacher_id == teacher.id,
            db.func.date(Attendance.date) == attendance_date,
            Attendance.subject == subject
        ).first()
        if attendance_record:
            attendance_record.status = status
            db.session.commit()
            print(f"[DEBUG] Updated attendance: student_id={student.id}, status={status}, date={attendance_date}, subject={subject}")
        else:
            attendance = Attendance(
                student_id=student.id,
                teacher_id=teacher.id,
                date=attendance_date,
                status=status,
                subject=subject
            )
            db.session.add(attendance)
            db.session.commit()
            print(f"[DEBUG] Added attendance: student_id={student.id}, status={status}, date={attendance_date}, subject={subject}")
    db.session.commit()
    print(f"[DEBUG] Committed attendance for date={attendance_date}, subject={subject}, teacher_id={teacher.id}")
    flash(f'Attendance marked. Present: {len(present_ids)} student(s).', 'success')
    return redirect(url_for('teacher_dashboard'))
# All imports at the top
from flask import render_template, request, redirect, url_for, session, flash
from app import app, db
from app.models import Admin, Teacher, Student, Attendance
from werkzeug.security import check_password_hash
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

# View individual student attendance (for teacher)
@app.route('/teacher/student/<int:student_id>/attendance')
def view_student_attendance(student_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    student = Student.query.get_or_404(student_id)
    attendance = student.attendances
    return render_template('student_attendance.html', student=student, attendance=attendance)

# Student attendance lookup (by USN)
@app.route('/student/attendance', methods=['GET', 'POST'])
def student_attendance_lookup():
    attendance = None
    student = None
    grouped_records = None
    sorted_dates = None
    selected_date = None
    if request.method == 'POST':
        usn = request.form['usn']
        date_str = request.form.get('date')
        student = Student.query.filter_by(usn=usn).first()
        if student:
            records = student.attendances
            from collections import defaultdict
            grouped_records = defaultdict(list)
            for record in records:
                grouped_records[record.date].append(record)
            sorted_dates = sorted(grouped_records.keys(), reverse=True)
            if date_str:
                try:
                    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    # Only show records for selected date
                    sorted_dates = [selected_date] if selected_date in grouped_records else []
                except Exception:
                    selected_date = None
        else:
            flash('No student found with that USN.', 'danger')
    return render_template('student_attendance_lookup.html', student=student, grouped_records=grouped_records, sorted_dates=sorted_dates, selected_date=selected_date)

# Homepage route
@app.route('/')
def home():
    return render_template('index.html')

# Teacher add student
@app.route('/teacher/students/add', methods=['GET', 'POST'])
def teacher_add_student():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        semester = int(request.form['semester'])
        student = Student(name=name, usn=usn, semester=semester)
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('teacher_students'))
    return render_template('add_student.html')

# Attendance reports placeholder
@app.route('/teacher/attendance_reports')
def attendance_reports():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher = Teacher.query.get(session['teacher_id'])
    # Date filter from query param
    date_str = request.args.get('date')
    query = Attendance.query.filter_by(teacher_id=teacher.id)
    selected_date = None
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == selected_date)
        except Exception:
            selected_date = None
    attendance_records = query.all()
    print(f"[DEBUG] Attendance report: teacher_id={teacher.id}, subject={teacher.subject}, date={selected_date}")
    print(f"[DEBUG] Found {len(attendance_records)} attendance records")
    students = {s.id: s for s in Student.query.all()}
    for rec in attendance_records:
        print(f"[DEBUG] Record: student_id={rec.student_id}, usn={students[rec.student_id].usn if rec.student_id in students else 'Unknown'}, status={rec.status}, date={rec.date}, subject={rec.subject}")
    # Group records by date
    from collections import defaultdict
    grouped_records = defaultdict(list)
    for record in attendance_records:
        grouped_records[record.date].append(record)
    # Sort dates descending (latest first)
    sorted_dates = sorted(grouped_records.keys(), reverse=True)
    # Custom sort key for USN order: year, branch, number
    def usn_sort_key(record):
        usn = students[record.student_id].usn if record.student_id in students else ''
        import re
        match = re.match(r"(\d+)([A-Z]+)(\d{2})([A-Z]+)(\d+)", usn)
        if match:
            prefix, branch, year, subbranch, number = match.groups()
            return (branch, year, subbranch, int(number))
        return (usn,)
    for records in grouped_records.values():
        records.sort(key=usn_sort_key)
    return render_template('attendance_reports.html', grouped_records=grouped_records, sorted_dates=sorted_dates, students=students, selected_date=selected_date)


# Mark attendance with mode selection
@app.route('/teacher/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher = Teacher.query.get(session['teacher_id'])
    subject = teacher.subject if teacher else ''
    all_students = Student.query.all()
    def usn_sort_key(student):
        usn = student.usn.upper()
        if usn.startswith('2BA20AI') or usn.startswith('2BA22AI'):
            return (1, usn)
        return (0, usn)
    students = sorted(all_students, key=usn_sort_key)
    if request.method == 'POST':
        attendance_date = request.form.get('attendance_date')
        if not attendance_date:
            flash('Please select a date.', 'danger')
            return render_template('mark_attendance.html', students=students)
        print(f"[DEBUG] Manual attendance: teacher_id={teacher.id}, subject={subject}, date={attendance_date}")
        for student in students:
            status = request.form.get(f'attendance_{student.id}')
            if status not in ['Present', 'Absent']:
                flash(f'Missing status for {student.name} ({student.usn})', 'danger')
                return render_template('mark_attendance.html', students=students)
            already_marked = db.session.query(db.exists().where(
                (db.func.date(Attendance.date) == attendance_date) &
                (Attendance.student_id == student.id) &
                (Attendance.teacher_id == teacher.id) &
                (Attendance.subject == subject)
            )).scalar()
            if not already_marked:
                attendance = Attendance(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    date=attendance_date,
                    status=status,
                    subject=subject
                )
                db.session.add(attendance)
                print(f"[DEBUG] Added attendance: student_id={student.id}, usn={student.usn}, status={status}")
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    return render_template('mark_attendance.html', students=students)

# Teacher students list
@app.route('/teacher/students')
def teacher_students():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher = Teacher.query.get(session['teacher_id'])
    # Custom sort: 20AI and 22AI at the end, rest by USN
    all_students = Student.query.all()
    def usn_sort_key(student):
        usn = student.usn.upper()
        # Place 20AI and 22AI at the end
        if usn.startswith('2BA20AI') or usn.startswith('2BA22AI'):
            return (1, usn)
        return (0, usn)
    students = sorted(all_students, key=usn_sort_key)
    return render_template('teacher_students.html', teacher=teacher, students=students)
# Student management
@app.route('/admin/students')
def admin_students():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    all_students = Student.query.all()
    def usn_sort_key(student):
        usn = student.usn.upper()
        if usn.startswith('2BA20AI') or usn.startswith('2BA22AI'):
            return (1, usn)
        return (0, usn)
    students = sorted(all_students, key=usn_sort_key)
    return render_template('admin_students.html', students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
def add_student():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        semester = int(request.form['semester'])
        photo = request.files['photo']
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join('app', 'static', 'student_photos', filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            import cv2
            import numpy as np
            import face_recognition
            img = face_recognition.load_image_file(photo_path)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
            encodings = face_recognition.face_encodings(rgb_img)
            if encodings:
                face_encoding = np.array(encodings[0]).tobytes()
                student = Student(name=name, usn=usn, semester=semester, face_encoding=face_encoding, photo_filename=filename)
                db.session.add(student)
                db.session.commit()
                flash('Student added successfully!', 'success')
                return redirect(url_for('admin_students'))
            else:
                os.remove(photo_path)
                flash('No face detected in the uploaded photo. Please upload a clear photo with a visible face.', 'danger')
        else:
            flash('Photo is required.', 'danger')
    return render_template('add_student.html')

@app.route('/admin/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'info')
    return redirect(url_for('admin_students'))
@app.route('/admin/teachers')
def admin_teachers():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    teachers = Teacher.query.all()
    return render_template('admin_teachers.html', teachers=teachers)

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and check_password_hash(teacher.password, password):
            session['teacher_id'] = teacher.id
            flash('Login successful!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('teacher_login.html')
@app.route('/admin/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        subject = request.form['subject']
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)
        teacher = Teacher(name=name, username=username, password=hashed_password, subject=subject)
        try:
            db.session.add(teacher)
            db.session.commit()
            flash('Teacher added successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists.', 'danger')
        return redirect(url_for('admin_teachers'))
    return render_template('add_teacher.html')

@app.route('/admin/teachers/delete/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    teacher = Teacher.query.get_or_404(teacher_id)
    # Delete all attendance records for this teacher
    Attendance.query.filter_by(teacher_id=teacher.id).delete()
    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted.', 'info')
    return redirect(url_for('admin_teachers'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and password == admin.password:
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')
@app.route('/admin/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student_admin(student_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.usn = request.form['usn']
        student.semester = int(request.form['semester'])
        photo = request.files.get('photo')
        captured_image = request.form.get('captured_image')
        import cv2
        import numpy as np
        import face_recognition
        filename = student.photo_filename
        face_encoding = student.face_encoding
        if captured_image:
            header, encoded = captured_image.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img_array = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            filename = f"{student.usn}_captured.png"
            photo_path = os.path.join(app.root_path, 'static', 'student_photos', filename)
            cv2.imwrite(photo_path, img)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_img)
            if encodings:
                face_encoding = np.array(encodings[0]).tobytes()
            student.photo_filename = filename
        elif photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.root_path, 'static', 'student_photos', filename)
            photo.save(photo_path)
            img = face_recognition.load_image_file(photo_path)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
            encodings = face_recognition.face_encodings(rgb_img)
            if encodings:
                face_encoding = np.array(encodings[0]).tobytes()
            student.photo_filename = filename
        student.face_encoding = face_encoding
        db.session.commit()
        flash('Student info updated!', 'success')
        return redirect(url_for('admin_students'))
    return render_template('edit_student.html', student=student, role='admin')

@app.route('/teacher/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student_teacher(student_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.usn = request.form['usn']
        student.semester = int(request.form['semester'])
        photo = request.files.get('photo')
        captured_image = request.form.get('captured_image')
        import cv2
        import numpy as np
        import face_recognition
        filename = student.photo_filename
        face_encoding = student.face_encoding
        if captured_image:
            header, encoded = captured_image.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img_array = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            filename = f"{student.usn}_captured.png"
            photo_path = os.path.join(app.root_path, 'static', 'student_photos', filename)
            cv2.imwrite(photo_path, img)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_img)
            if encodings:
                face_encoding = np.array(encodings[0]).tobytes()
            student.photo_filename = filename
        elif photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.root_path, 'static', 'student_photos', filename)
            photo.save(photo_path)
            img = face_recognition.load_image_file(photo_path)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
            encodings = face_recognition.face_encodings(rgb_img)
            if encodings:
                face_encoding = np.array(encodings[0]).tobytes()
            student.photo_filename = filename
        student.face_encoding = face_encoding
        db.session.commit()
        flash('Student info updated!', 'success')
        return redirect(url_for('teacher_students'))
    return render_template('edit_student.html', student=student, role='teacher')
