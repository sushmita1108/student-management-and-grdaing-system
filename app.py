import os
import sqlite3
from datetime import timedelta
from functools import wraps
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
# pyrefly: ignore [missing-import]
from flask_wtf import CSRFProtect
# pyrefly: ignore [missing-import]
from flask_wtf.csrf import generate_csrf, CSRFError
# pyrefly: ignore [missing-import]
from sqlalchemy import func
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from models import db, Student, Subject, Grade, User, AcademicClass

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-school-mgmt-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] =  os.getenv("FLASK_ENV") == "production"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
csrf = CSRFProtect()
csrf.init_app(app)
db.init_app(app)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security token refreshed. Please try signing in again.', 'info')
    return redirect(url_for('login'))

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

ROLE_CHOICES = ['Admin', 'Department', 'Teacher', 'Student']

@app.context_processor
def inject_user():
    return dict(current_user=getattr(g, 'user', None), can_manage_grade=user_can_manage_grade, csrf_token=generate_csrf)

def user_can_manage_grade(grade):
    if g.user is None:
        return False
    if g.user.role == 'Admin':
        return True
    if g.user.role == 'Department':
        return grade.student and grade.student.department == g.user.department
    if g.user.role == 'Teacher' and grade.subject and grade.subject.assigned_teacher_id == g.user.id:
        return True
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def init_db_if_empty():
    with app.app_context():
        db.create_all()

        # Repair schema for the actual SQLite database used by SQLAlchemy.
        db_path = None
        if getattr(db.engine.url, 'database', None):
            db_path = db.engine.url.database
        elif app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        need_schema_load = False
        if db_path:
            if not os.path.isabs(db_path):
                db_path = os.path.join(app.instance_path, db_path)
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                if 'department' not in existing_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR(80) DEFAULT 'Engineering'")
                    conn.commit()

                cursor.execute("PRAGMA table_info(students)")
                student_columns = [column[1] for column in cursor.fetchall()]
                if student_columns and 'faculty' not in student_columns:
                    cursor.execute("ALTER TABLE students ADD COLUMN faculty VARCHAR(80) DEFAULT 'General'")
                    conn.commit()
                if student_columns and 'academic_period' not in student_columns:
                    cursor.execute("ALTER TABLE students ADD COLUMN academic_period VARCHAR(40) DEFAULT 'Semester 1'")
                    conn.commit()
                if student_columns and 'department' not in student_columns:
                    cursor.execute("ALTER TABLE students ADD COLUMN department VARCHAR(80) DEFAULT 'Engineering'")
                    conn.commit()

                cursor.execute("PRAGMA table_info(subjects)")
                subject_columns = [column[1] for column in cursor.fetchall()]
                if subject_columns:
                    if 'faculty' not in subject_columns:
                        cursor.execute("ALTER TABLE subjects ADD COLUMN faculty VARCHAR(80) DEFAULT 'General'")
                        conn.commit()
                    if 'level' not in subject_columns:
                        cursor.execute("ALTER TABLE subjects ADD COLUMN level VARCHAR(20) DEFAULT 'Bachelor'")
                        conn.commit()
                    if 'assigned_teacher_id' not in subject_columns:
                        cursor.execute("ALTER TABLE subjects ADD COLUMN assigned_teacher_id INTEGER")
                        conn.commit()
                    if 'department' not in subject_columns:
                        cursor.execute("ALTER TABLE subjects ADD COLUMN department VARCHAR(80) DEFAULT 'Engineering'")
                        conn.commit()
                    if 'academic_period' not in subject_columns:
                        cursor.execute("ALTER TABLE subjects ADD COLUMN academic_period VARCHAR(40) DEFAULT 'Semester 1'")
                        conn.commit()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                if not all(name in existing_tables for name in ['users', 'students', 'subjects', 'grades', 'classes']):
                    need_schema_load = True
                conn.close()
            else:
                need_schema_load = True

        if need_schema_load:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if not os.path.exists(schema_path):
                schema_path = os.path.join(os.path.dirname(__file__), 'schema_utf8.sql')
            if os.path.exists(schema_path):
                db_path = None
                uri = app.config['SQLALCHEMY_DATABASE_URI']
                if uri.startswith('sqlite:///'):
                    db_path = uri.replace('sqlite:///', '')
                elif uri.startswith('sqlite:'):
                    db_path = uri.split(':', 1)[1]
                if db_path and not os.path.isabs(db_path):
                    db_path = os.path.join(app.instance_path, db_path)
                conn = sqlite3.connect(db_path)
                with open(schema_path, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                conn.close()

        # Check admin user name
        admin_acc = User.query.filter_by(username='admin').first()
        if admin_acc and admin_acc.full_name != 'Er. Sushmita Marasini':
            admin_acc.full_name = 'Er. Sushmita Marasini'
            db.session.commit()

        if User.query.count() == 0:
            # Seed default SNS College admin, department heads, teacher, and student users
            admin_user = User(
                username='admin',
                email='admin@sns.edu.np',
                full_name='Er. Sushmita Marasini',
                role='Admin'
            )
            admin_user.set_password('admin123')

            dept_eng = User(
                username='eng_head',
                email='dept_eng@sns.edu.np',
                full_name='Er. Subash Rajkarnikar, Dean - Institute of Engineering (IOE)',
                role='Department',
                department='Engineering'
            )
            dept_eng.set_password('dept123')

            dept_med = User(
                username='med_head',
                email='dept_med@sns.edu.np',
                full_name='Dr. Anjali Sharma, Dean - Institute of Medicine (IOM)',
                role='Department',
                department='Medicine'
            )
            dept_med.set_password('dept123')

            dept_mgmt = User(
                username='mgmt_head',
                email='dept_mgmt@sns.edu.np',
                full_name='Prof. Bikram Thapa, Dean - Faculty of Management (FOM)',
                role='Department',
                department='Management'
            )
            dept_mgmt.set_password('dept123')

            dept_sh = User(
                username='sh_head',
                email='dept_sh@sns.edu.np',
                full_name='Assoc. Prof. Sunita Shrestha, Dean - Institute of Science & Technology (IOST)',
                role='Department',
                department='Science and Humanities'
            )
            dept_sh.set_password('dept123')

            teacher_user = User(
                username='teacher',
                email='teacher@sns.edu.np',
                full_name='Assoc. Prof. Sunita Shrestha',
                role='Teacher',
                department='Engineering'
            )
            teacher_user.set_password('teacher123')

            student_user = User(
                username='student',
                email='student@sns.edu.np',
                full_name='Aarav Sharma',
                role='Student',
                department='Engineering'
            )
            student_user.set_password('student123')

            db.session.add_all([admin_user, dept_eng, dept_med, dept_mgmt, dept_sh, teacher_user, student_user])
            db.session.commit()

        # Assign a default set of subjects to the SNS College teacher account.
        teacher_user = User.query.filter_by(username='teacher').first()
        if teacher_user:
            assigned_codes = ['CSIT-301', 'CSIT-302', 'MSC-501', 'MSC-503']
            subjects = Subject.query.filter(Subject.code.in_(assigned_codes)).all()
            for subject in subjects:
                if subject.assigned_teacher_id != teacher_user.id:
                    subject.assigned_teacher_id = teacher_user.id
            db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        role = request.form.get('role', 'Student').strip().title()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')

        login_input_lower = login_input.lower()

        if '@' in login_input_lower and not login_input_lower.endswith('@sns.edu.np'):
            flash('Please sign in with an SNS College email ending in @sns.edu.np, or use your username.', 'danger')
            return render_template('login.html')

        if not login_input or not password:
            flash('Please provide both college email/username and password.', 'danger')
            return render_template('login.html')

        if role not in ROLE_CHOICES:
            flash('Please select a valid role for login.', 'danger')
            return render_template('login.html')

        if role == 'Department' and not department:
            flash('Please choose your department when logging in as Department Head.', 'danger')
            return render_template('login.html')

        user = User.query.filter(
            (func.lower(User.email) == login_input_lower) |
            (func.lower(User.username) == login_input_lower)
        ).first()

        if user and user.check_password(password):
            if user.role != role:
                flash('The selected role does not match your account role.', 'danger')
                return render_template('login.html')

            if role == 'Department' and user.department and department and user.department != department:
                flash('Selected department does not match your account department.', 'danger')
                return render_template('login.html')

            csrf_val = session.get('_csrf_token')
            session.clear()
            if csrf_val:
                session['_csrf_token'] = csrf_val
            session['user_id'] = user.id
            if remember:
                session.permanent = True
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))

        flash('Invalid email/username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        department = request.form.get('department', '').strip() or 'General'
        faculty = request.form.get('faculty', '').strip() or 'General'
        academic_period = request.form.get('academic_period', '').strip() or ''
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'Student').strip().title()
        if role not in ROLE_CHOICES:
            role = 'Student'

        required_fields = [email, password, confirm_password]
        if role == 'Student':
            required_fields += [full_name, username, department, faculty, academic_period]
        elif role == 'Teacher':
            required_fields += [full_name, username]
        elif role == 'Department':
            required_fields += [department]

        if not all(required_fields):
            if role == 'Department':
                flash('Department heads must provide a college email, password, and department.', 'danger')
            elif role == 'Admin':
                flash('Campus admins must provide a college email and password.', 'danger')
            else:
                flash('All fields are required.', 'danger')
            return render_template('register.html')

        if role == 'Student' and (not department or not faculty or not academic_period):
            flash('Please select department, faculty, and academic period for your student profile.', 'danger')
            return render_template('register.html')

        if not email.endswith('@sns.edu.np'):
            flash('Please register with an SNS College email ending in @sns.edu.np.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html')

        if not username:
            base_username = email.split('@')[0].replace('.', '_')
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

        if not full_name:
            if role == 'Department':
                full_name = f"{department} Head"
            elif role == 'Admin':
                full_name = 'SNS Admin'
            else:
                full_name = username

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash('Username or Email is already registered.', 'warning')
            return render_template('register.html')

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            role=role,
            department=department if role in ['Student', 'Department', 'Teacher'] else 'General'
        )
        new_user.set_password(password)
        db.session.add(new_user)

        if role == 'Student':
            parts = full_name.split()
            first_name = parts[0]
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else 'Student'
            student_code = f"SNS-{new_user.username.upper()}"
            new_student = Student(
                student_code=student_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                grade_level=department,
                faculty=faculty,
                academic_period=academic_period,
                department=department,
                status='Undergraduated'
            )
            db.session.add(new_student)

        db.session.commit()

        flash('Account created successfully! Please sign in to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    csrf_val = session.get('_csrf_token')
    session.clear()
    if csrf_val:
        session['_csrf_token'] = csrf_val
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    dept_registrations = []
    if g.user.role == 'Department':
        dept = g.user.department
        students = Student.query.filter_by(department=dept).all()
        total_students = len(students)
        total_subjects = Subject.query.filter_by(department=dept).count()
        total_grades = Grade.query.join(Student).filter(Student.department == dept).count()
        total_users = User.query.filter_by(department=dept).count()
        avg_gpa = round(sum(s.gpa for s in students) / max(len(students), 1), 2)
        recent_grades = Grade.query.join(Student).filter(Student.department == dept).order_by(Grade.created_at.desc()).limit(5).all()
        dept_registrations = Student.query.filter_by(department=dept).order_by(Student.created_at.desc()).limit(5).all()
        student_profile = None
        student_grade_count = 0
    elif g.user.role == 'Student':
        total_students = Student.query.count()
        total_subjects = Subject.query.count()
        total_grades = Grade.query.count()
        total_users = User.query.count()
        students = Student.query.all()
        avg_gpa = round(sum(s.gpa for s in students) / max(len(students), 1), 2)
        student_profile = Student.query.filter_by(email=g.user.email).first()
        recent_grades = Grade.query.filter_by(student_id=student_profile.id).order_by(Grade.created_at.desc()).limit(5).all() if student_profile else []
        student_grade_count = Grade.query.filter_by(student_id=student_profile.id).count() if student_profile else 0
    else:
        total_students = Student.query.count()
        total_subjects = Subject.query.count()
        total_grades = Grade.query.count()
        total_users = User.query.count()
        students = Student.query.all()
        avg_gpa = round(sum(s.gpa for s in students) / max(len(students), 1), 2)
        recent_grades = Grade.query.order_by(Grade.created_at.desc()).limit(5).all()
        student_profile = None
        student_grade_count = 0

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_subjects=total_subjects,
        total_grades=total_grades,
        total_users=total_users,
        avg_gpa=avg_gpa,
        recent_grades=recent_grades,
        dept_registrations=dept_registrations,
        student_profile=student_profile,
        student_grade_count=student_grade_count
    )

@app.route('/assigned-subjects')
@login_required
def assigned_subjects():
    if g.user.role not in ['Teacher', 'Admin']:
        flash('Only teachers and administrators can view assigned subjects.', 'warning')
        return redirect(url_for('dashboard'))

    if g.user.role == 'Teacher':
        subjects = Subject.query.filter_by(assigned_teacher_id=g.user.id).all()
    else:
        subjects = Subject.query.filter(Subject.assigned_teacher_id.isnot(None)).all()

    return render_template('assigned_subjects.html', subjects=subjects)

@app.route('/admin/assign-subjects', methods=['GET', 'POST'])
@login_required
def admin_assign_subjects():
    if g.user.role != 'Admin':
        flash('Only administrators can manage subject assignments.', 'warning')
        return redirect(url_for('dashboard'))

    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    subjects = Subject.query.order_by(Subject.code).all()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        teacher_id = request.form.get('teacher_id')

        subject = Subject.query.get(subject_id)
        if not subject:
            flash('Selected subject was not found.', 'danger')
            return redirect(url_for('admin_assign_subjects'))

        if teacher_id:
            teacher = User.query.filter_by(id=teacher_id, role='Teacher').first()
            if not teacher:
                flash('Selected teacher is not valid.', 'danger')
                return redirect(url_for('admin_assign_subjects'))
            subject.assigned_teacher_id = teacher.id
            flash(f'Subject {subject.code} is now assigned to {teacher.full_name}.', 'success')
        else:
            subject.assigned_teacher_id = None
            flash(f'Subject {subject.code} is now unassigned.', 'success')

        db.session.commit()
        return redirect(url_for('admin_assign_subjects'))

    return render_template('admin_assign_subjects.html', subjects=subjects, teachers=teachers)

@app.route('/admin/manage-users')
@login_required
def admin_manage_users():
    if g.user.role != 'Admin':
        flash('Only administrators can manage user accounts.', 'warning')
        return redirect(url_for('dashboard'))

    users = User.query.filter(User.role != 'Admin').order_by(User.role, User.full_name).all()
    return render_template('admin_manage_users.html', users=users)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    if g.user.role != 'Admin':
        flash('Only administrators can create user accounts.', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Student').strip().title()
        department = request.form.get('department', '').strip()

        if role not in ROLE_CHOICES:
            role = 'Student'

        if not all([full_name, username, email, password]):
            flash('All fields are required to create an account.', 'danger')
            return render_template('admin_edit_user.html', user=None, ROLE_CHOICES=ROLE_CHOICES)

        if not email.endswith('@sns.edu.np'):
            flash('User email must end with @sns.edu.np.', 'danger')
            return render_template('admin_edit_user.html', user=None, ROLE_CHOICES=ROLE_CHOICES)

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Username or email is already registered.', 'warning')
            return render_template('admin_edit_user.html', user=None, ROLE_CHOICES=ROLE_CHOICES)

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            role=role,
            department=department if role in ['Department', 'Teacher'] else 'General'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {full_name} has been created successfully.', 'success')
        return redirect(url_for('admin_manage_users'))

    return render_template('admin_edit_user.html', user=None, ROLE_CHOICES=ROLE_CHOICES)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if g.user.role != 'Admin':
        flash('Only administrators can edit user accounts.', 'warning')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.username = request.form.get('username', '').strip().lower()
        user.email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'Student').strip().title()
        user.department = request.form.get('department', '').strip() if role in ['Department', 'Teacher'] else 'General'
        password = request.form.get('password', '').strip()

        if role not in ROLE_CHOICES:
            role = 'Student'
        user.role = role

        if not all([user.full_name, user.username, user.email]):
            flash('Full name, username, and email are required.', 'danger')
            return render_template('admin_edit_user.html', user=user, ROLE_CHOICES=ROLE_CHOICES)

        if not user.email.endswith('@sns.edu.np'):
            flash('User email must end with @sns.edu.np.', 'danger')
            return render_template('admin_edit_user.html', user=user, ROLE_CHOICES=ROLE_CHOICES)

        existing_account = User.query.filter((User.email == user.email) | (User.username == user.username)).filter(User.id != user.id).first()
        if existing_account:
            flash('Another account already uses that username or email.', 'warning')
            return render_template('admin_edit_user.html', user=user, ROLE_CHOICES=ROLE_CHOICES)

        if password:
            user.set_password(password)

        db.session.commit()
        flash('User details updated successfully.', 'success')
        return redirect(url_for('admin_manage_users'))

    return render_template('admin_edit_user.html', user=user, ROLE_CHOICES=ROLE_CHOICES)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if g.user.role != 'Admin':
        flash('Only administrators can delete user accounts.', 'warning')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'Admin':
        flash('Cannot delete another admin account from this panel.', 'warning')
        return redirect(url_for('admin_manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash('User account has been deleted.', 'info')
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/manage-subjects')
@login_required
def admin_manage_subjects():
    if g.user.role != 'Admin':
        flash('Only administrators can manage subjects.', 'warning')
        return redirect(url_for('dashboard'))

    subjects = Subject.query.order_by(Subject.code).all()
    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    return render_template('admin_manage_subjects.html', subjects=subjects, teachers=teachers)

@app.route('/admin/subjects/create', methods=['GET', 'POST'])
@login_required
def admin_create_subject():
    if g.user.role != 'Admin':
        flash('Only administrators can create subjects.', 'warning')
        return redirect(url_for('dashboard'))

    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip() or 'Engineering'
        academic_period = request.form.get('academic_period', '').strip() or 'Semester 1'
        faculty = request.form.get('faculty', '').strip() or 'General'
        level = request.form.get('level', '').strip() or 'Bachelor'
        credits = request.form.get('credits', 3)
        assigned_teacher_id = request.form.get('assigned_teacher_id')

        if not all([code, name]):
            flash('Subject code and name are required.', 'danger')
            return render_template('admin_edit_subject.html', subject=None, teachers=teachers)

        if Subject.query.filter_by(code=code).first():
            flash('A subject with that code already exists.', 'warning')
            return render_template('admin_edit_subject.html', subject=None, teachers=teachers)

        subject = Subject(code=code, name=name, department=department, academic_period=academic_period, faculty=faculty, level=level, credits=int(credits))
        subject.assigned_teacher_id = int(assigned_teacher_id) if assigned_teacher_id else None
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully.', 'success')
        return redirect(url_for('admin_manage_subjects'))

    return render_template('admin_edit_subject.html', subject=None, teachers=teachers)

@app.route('/admin/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_subject(subject_id):
    if g.user.role != 'Admin':
        flash('Only administrators can edit subjects.', 'warning')
        return redirect(url_for('dashboard'))

    subject = Subject.query.get_or_404(subject_id)
    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    if request.method == 'POST':
        subject.code = request.form.get('code', '').strip().upper()
        subject.name = request.form.get('name', '').strip()
        subject.department = request.form.get('department', '').strip() or 'Engineering'
        subject.academic_period = request.form.get('academic_period', '').strip() or 'Semester 1'
        subject.faculty = request.form.get('faculty', '').strip() or 'General'
        subject.level = request.form.get('level', '').strip() or 'Bachelor'
        subject.credits = int(request.form.get('credits', subject.credits))
        assigned_teacher_id = request.form.get('assigned_teacher_id')
        subject.assigned_teacher_id = int(assigned_teacher_id) if assigned_teacher_id else None

        if not all([subject.code, subject.name]):
            flash('Subject code and name are required.', 'danger')
            return render_template('admin_edit_subject.html', subject=subject, teachers=teachers)

        existing_subject = Subject.query.filter(Subject.code == subject.code, Subject.id != subject.id).first()
        if existing_subject:
            flash('Another subject with that code already exists.', 'warning')
            return render_template('admin_edit_subject.html', subject=subject, teachers=teachers)

        db.session.commit()
        flash('Subject updated successfully.', 'success')
        return redirect(url_for('admin_manage_subjects'))

    return render_template('admin_edit_subject.html', subject=subject, teachers=teachers)

@app.route('/admin/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def admin_delete_subject(subject_id):
    if g.user.role != 'Admin':
        flash('Only administrators can delete subjects.', 'warning')
        return redirect(url_for('dashboard'))

    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully.', 'info')
    return redirect(url_for('admin_manage_subjects'))

@app.route('/admin/manage-classes')
@login_required
def admin_manage_classes():
    if g.user.role != 'Admin':
        flash('Only administrators can manage classes.', 'warning')
        return redirect(url_for('dashboard'))

    classes = AcademicClass.query.order_by(AcademicClass.code).all()
    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    return render_template('admin_manage_classes.html', classes=classes, teachers=teachers)

@app.route('/admin/classes/create', methods=['GET', 'POST'])
@login_required
def admin_create_class():
    if g.user.role != 'Admin':
        flash('Only administrators can create classes.', 'warning')
        return redirect(url_for('dashboard'))

    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip() or 'General'
        level = request.form.get('level', '').strip() or 'Bachelor'
        advisor_id = request.form.get('advisor_id')
        description = request.form.get('description', '').strip()

        if not all([code, name]):
            flash('Class code and name are required.', 'danger')
            return render_template('admin_edit_class.html', academic_class=None, teachers=teachers)

        if AcademicClass.query.filter_by(code=code).first():
            flash('A class with that code already exists.', 'warning')
            return render_template('admin_edit_class.html', academic_class=None, teachers=teachers)

        new_class = AcademicClass(
            code=code,
            name=name,
            department=department,
            level=level,
            description=description,
            advisor_id=int(advisor_id) if advisor_id else None
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully.', 'success')
        return redirect(url_for('admin_manage_classes'))

    return render_template('admin_edit_class.html', academic_class=None, teachers=teachers)

@app.route('/admin/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_class(class_id):
    if g.user.role != 'Admin':
        flash('Only administrators can edit classes.', 'warning')
        return redirect(url_for('dashboard'))

    academic_class = AcademicClass.query.get_or_404(class_id)
    teachers = User.query.filter_by(role='Teacher').order_by(User.full_name).all()
    if request.method == 'POST':
        academic_class.code = request.form.get('code', '').strip().upper()
        academic_class.name = request.form.get('name', '').strip()
        academic_class.department = request.form.get('department', '').strip() or 'General'
        academic_class.level = request.form.get('level', '').strip() or 'Bachelor'
        academic_class.description = request.form.get('description', '').strip()
        advisor_id = request.form.get('advisor_id')
        academic_class.advisor_id = int(advisor_id) if advisor_id else None

        if not all([academic_class.code, academic_class.name]):
            flash('Class code and name are required.', 'danger')
            return render_template('admin_edit_class.html', academic_class=academic_class, teachers=teachers)

        if AcademicClass.query.filter(AcademicClass.code == academic_class.code, AcademicClass.id != academic_class.id).first():
            flash('Another class with that code already exists.', 'warning')
            return render_template('admin_edit_class.html', academic_class=academic_class, teachers=teachers)

        db.session.commit()
        flash('Class updated successfully.', 'success')
        return redirect(url_for('admin_manage_classes'))

    return render_template('admin_edit_class.html', academic_class=academic_class, teachers=teachers)

@app.route('/admin/classes/delete/<int:class_id>', methods=['POST'])
@login_required
def admin_delete_class(class_id):
    if g.user.role != 'Admin':
        flash('Only administrators can delete classes.', 'warning')
        return redirect(url_for('dashboard'))

    academic_class = AcademicClass.query.get_or_404(class_id)
    db.session.delete(academic_class)
    db.session.commit()
    flash('Class deleted successfully.', 'info')
    return redirect(url_for('admin_manage_classes'))

@app.route('/students')
@login_required
def students():
    search_query = request.args.get('search', '').strip()
    if g.user.role == 'Student':
        student_list = Student.query.filter_by(email=g.user.email).all()
    elif g.user.role == 'Department':
        dept = g.user.department
        if search_query:
            student_list = Student.query.filter(
                Student.department == dept,
                (Student.first_name.ilike(f"%{search_query}%")) |
                (Student.last_name.ilike(f"%{search_query}%")) |
                (Student.student_code.ilike(f"%{search_query}%")) |
                (Student.email.ilike(f"%{search_query}%"))
            ).all()
        else:
            student_list = Student.query.filter_by(department=dept).all()
    elif search_query:
        student_list = Student.query.filter(
            (Student.first_name.ilike(f"%{search_query}%")) |
            (Student.last_name.ilike(f"%{search_query}%")) |
            (Student.student_code.ilike(f"%{search_query}%")) |
            (Student.email.ilike(f"%{search_query}%"))
        ).all()
    else:
        student_list = Student.query.all()
    return render_template('students.html', students=student_list, search_query=search_query)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if g.user.role == 'Student':
        flash('Student accounts cannot enroll new scholars.', 'warning')
        return redirect(url_for('students'))

    if request.method == 'POST':
        student_code = request.form.get('student_code', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip() or 'Engineering'
        if g.user.role == 'Department':
            department = g.user.department
        grade_level = department
        faculty = request.form.get('faculty', '').strip() or 'General'
        academic_period = request.form.get('academic_period', '').strip() or 'Semester 1'
        status = request.form.get('status', 'Undergraduated').strip()
        if status not in ['Graduated', 'Undergraduated']:
            status = 'Undergraduated'

        if not all([student_code, first_name, last_name, email, grade_level, department, faculty, academic_period]):
            flash('All fields are required.', 'danger')
            return render_template('add_student.html')

        existing = Student.query.filter((Student.student_code == student_code) | (Student.email == email)).first()
        if existing:
            flash('Student code or Email already exists.', 'warning')
            return render_template('add_student.html')

        new_student = Student(
            student_code=student_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            grade_level=grade_level,
            department=department,
            faculty=faculty,
            academic_period=academic_period,
            status=status
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Student {first_name} {last_name} enrolled successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html')

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if g.user.role == 'Department' and student.department != g.user.department:
        flash('You are only authorized to manage students in your department.', 'danger')
        return redirect(url_for('students'))

    if request.method == 'POST':
        student.first_name = request.form.get('first_name', '').strip()
        student.last_name = request.form.get('last_name', '').strip()
        student.email = request.form.get('email', '').strip()
        if g.user.role != 'Department':
            student.department = request.form.get('department', student.department).strip() or 'Engineering'
        student.grade_level = student.department
        student.faculty = request.form.get('faculty', '').strip() or 'General'
        student.academic_period = request.form.get('academic_period', 'Semester 1').strip() or 'Semester 1'
        status = request.form.get('status', 'Undergraduated').strip()
        student.status = status if status in ['Graduated', 'Undergraduated'] else 'Undergraduated'

        db.session.commit()
        flash('Student record updated successfully.', 'success')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)

@app.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    if g.user.role == 'Department' and student.department != g.user.department:
        flash('You are only authorized to manage students in your department.', 'danger')
        return redirect(url_for('students'))

    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully.', 'info')
    return redirect(url_for('students'))

@app.route('/grades', methods=['GET', 'POST'])
@login_required
def grades():
    if request.method == 'POST':
        if g.user.role == 'Student':
            flash('Students cannot submit grade evaluations.', 'warning')
            return redirect(url_for('grades'))

        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        score = float(request.form.get('score', 0))
        term = request.form.get('term', 'Semester Exam 2082').strip()

        target_student = Student.query.get(student_id)
        if not target_student:
            flash('Selected student not found.', 'danger')
            return redirect(url_for('grades'))

        if g.user.role == 'Department' and target_student.department != g.user.department:
            flash('You may only submit grades for students in your department.', 'danger')
            return redirect(url_for('grades'))

        if g.user.role == 'Teacher':
            subject = Subject.query.filter_by(id=subject_id, assigned_teacher_id=g.user.id).first()
            if not subject:
                flash('You may only submit grades for your assigned subjects.', 'danger')
                return redirect(url_for('grades'))

        letter_grade, _ = Grade.calculate_letter_grade(score)

        new_grade = Grade(
            student_id=student_id,
            subject_id=subject_id,
            score=score,
            letter_grade=letter_grade,
            term=term
        )
        db.session.add(new_grade)
        db.session.commit()
        flash('Grade recorded successfully!', 'success')
        return redirect(url_for('grades'))

    if g.user.role == 'Student':
        student_record = Student.query.filter_by(email=g.user.email).first()
        all_grades = Grade.query.filter_by(student_id=student_record.id).order_by(Grade.created_at.desc()).all() if student_record else []
        all_students = [student_record] if student_record else []
        all_subjects = Subject.query.all()
    elif g.user.role == 'Department':
        dept = g.user.department
        all_grades = Grade.query.join(Student).filter(Student.department == dept).order_by(Grade.created_at.desc()).all()
        all_students = Student.query.filter_by(department=dept).order_by(Student.first_name).all()
        all_subjects = Subject.query.filter_by(department=dept).order_by(Subject.code).all()
        if not all_subjects:
            all_subjects = Subject.query.order_by(Subject.code).all()
    elif g.user.role == 'Teacher':
        all_grades = Grade.query.join(Subject).filter(Subject.assigned_teacher_id == g.user.id).order_by(Grade.created_at.desc()).all()
        all_students = Student.query.all()
        all_subjects = Subject.query.filter_by(assigned_teacher_id=g.user.id).all()
    else:
        all_grades = Grade.query.order_by(Grade.created_at.desc()).all()
        all_students = Student.query.all()
        all_subjects = Subject.query.all()

    return render_template('grades.html', grades=all_grades, students=all_students, subjects=all_subjects)

@app.route('/profile')
@login_required
def profile():
    if g.user.role != 'Student':
        flash('Only student accounts can access the student profile page.', 'warning')
        return redirect(url_for('dashboard'))

    student_profile = Student.query.filter_by(email=g.user.email).first()
    if not student_profile:
        flash('Student profile not found for your account.', 'danger')
        return redirect(url_for('dashboard'))

    grades = Grade.query.filter_by(student_id=student_profile.id).join(Subject).order_by(Subject.code).all()
    report_cards = [
        {
            'subject': grade.subject,
            'score': grade.score,
            'letter_grade': grade.letter_grade,
            'credits': grade.subject.credits,
            'term': grade.term,
            'gpa_points': grade.gpa_points,
        }
        for grade in grades
    ]
    total_credits = sum(item['credits'] for item in report_cards)
    return render_template('student_profile.html', student=student_profile, grades=grades, report_cards=report_cards, total_credits=total_credits)

@app.route('/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@login_required
def edit_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if not user_can_manage_grade(grade):
        flash('You are not authorized to modify this grade.', 'danger')
        return redirect(url_for('grades'))

    if request.method == 'POST':
        score = float(request.form.get('score', grade.score))
        term = request.form.get('term', grade.term).strip()
        grade.score = score
        grade.letter_grade, _ = Grade.calculate_letter_grade(score)
        grade.term = term
        db.session.commit()
        flash('Grade updated successfully.', 'success')
        return redirect(url_for('grades'))

    return render_template('edit_grade.html', grade=grade)

@app.route('/grades/delete/<int:grade_id>', methods=['POST'])
@login_required
def delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if not user_can_manage_grade(grade):
        flash('You are not authorized to delete this grade.', 'danger')
        return redirect(url_for('grades'))

    db.session.delete(grade)
    db.session.commit()
    flash('Grade deleted successfully.', 'info')
    return redirect(url_for('grades'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_db_if_empty()
    app.run(host="0.0.0.0", port=5000)