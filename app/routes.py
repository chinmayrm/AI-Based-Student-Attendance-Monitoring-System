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
    if request.method == 'POST':
        usn = request.form['usn']
        student = Student.query.filter_by(usn=usn).first()
        if student:
            attendance = student.attendances  # This will be a list of Attendance objects
        else:
            flash('No student found with that USN.', 'danger')
    return render_template('student_attendance_lookup.html', student=student, attendance=attendance)

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
        photo = request.files['photo']
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join('app', 'static', 'student_photos', filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            student = Student(name=name, usn=usn, semester=semester, face_encoding=b'', photo_filename=filename)
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('teacher_students'))
        else:
            flash('Photo is required.', 'danger')
    return render_template('add_student.html')

# Attendance reports placeholder
@app.route('/teacher/attendance_reports')
def attendance_reports():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    return render_template('attendance_reports.html')


# Mark attendance with mode selection
@app.route('/teacher/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    mode = request.args.get('mode', 'facerecognition')
    teacher = Teacher.query.get(session['teacher_id'])
    subject = teacher.subject if teacher else ''
    today = db.func.current_date()
    if mode == 'manual':
        all_students = Student.query.all()
        def usn_sort_key(student):
            usn = student.usn.upper()
            if usn.startswith('2BA20AI') or usn.startswith('2BA22AI'):
                return (1, usn)
            return (0, usn)
        students = sorted(all_students, key=usn_sort_key)
        if request.method == 'POST':
            mark_mode = request.form.get('mark_mode', 'present')
            present_ids = request.form.getlist('present')
            absent_ids = request.form.getlist('absent')
            present_ids = set(map(int, present_ids))
            absent_ids = set(map(int, absent_ids))
            all_ids = set(s.id for s in students)
            # Get selected date from form
            attendance_date = request.form.get('attendance_date')
            if not attendance_date:
                flash('Please select a date.', 'danger')
                return render_template('mark_attendance_manual.html', students=students)
            # Determine present/absent based on mode
            if mark_mode == 'present':
                present_set = present_ids
                absent_set = all_ids - present_set
            else:
                absent_set = absent_ids
                present_set = all_ids - absent_set
            # Save attendance for each student
            for student in students:
                status = 'Present' if student.id in present_set else 'Absent'
                # Prevent duplicate attendance for same date, teacher, subject
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
            db.session.commit()
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('teacher_dashboard'))
        return render_template('mark_attendance_manual.html', students=students)
    else:
        return render_template('mark_attendance.html')

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
            # For now, store empty encoding (face encoding logic can be added later)
            student = Student(name=name, usn=usn, semester=semester, face_encoding=b'', photo_filename=filename)
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin_students'))
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

# Teacher login
@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and password == teacher.password:
            session['teacher_id'] = teacher.id
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('teacher_login.html')

# Teacher logout
@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher_id', None)
    return redirect(url_for('teacher_login'))

# Teacher dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher = Teacher.query.get(session['teacher_id'])
    return render_template('teacher_dashboard.html', teacher=teacher)

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        subject = request.form['subject']
        teacher = Teacher(name=name, username=username, password=password, subject=subject)
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
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join('app', 'static', 'student_photos', filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            student.photo_filename = filename
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
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join('app', 'static', 'student_photos', filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            student.photo_filename = filename
        db.session.commit()
        flash('Student info updated!', 'success')
        return redirect(url_for('teacher_students'))
    return render_template('edit_student.html', student=student, role='teacher')
