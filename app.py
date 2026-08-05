import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from dotenv import load_dotenv
from models import db, Student, Subject, Grade, User

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-school-mgmt-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

@app.context_processor
def inject_user():
    return dict(current_user=g.user)

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
        if Student.query.count() == 0:
            # Seed from schema.sql if database is empty
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_path):
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                conn.close()

        if User.query.count() == 0:
            # Seed default Nepalese Campus Chief and Department Head users
            admin_user = User(
                username='admin',
                email='admin@tu.edu.np',
                full_name='Prof. Dr. Ramesh Karki, Campus Chief',
                role='Admin'
            )
            admin_user.set_password('admin123')

            teacher_user = User(
                username='teacher',
                email='teacher@tu.edu.np',
                full_name='Assoc. Prof. Sunita Shrestha, HOD CSIT',
                role='Teacher'
            )
            teacher_user.set_password('teacher123')

            db.session.add(admin_user)
            db.session.add(teacher_user)
            db.session.commit()




@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')

        if not login_input or not password:
            flash('Please provide both email/username and password.', 'danger')
            return render_template('login.html')

        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()

        if user and user.check_password(password):
            session.clear()
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
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'Teacher').strip()

        if not all([full_name, username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html')

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
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user automatically
        session.clear()
        session['user_id'] = new_user.id
        flash(f'Account created successfully! Welcome to EduGrade, {full_name}.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    total_students = Student.query.count()
    total_subjects = Subject.query.count()
    total_grades = Grade.query.count()
    total_users = User.query.count()

    students = Student.query.all()
    avg_gpa = round(sum(s.gpa for s in students) / max(len(students), 1), 2)

    recent_grades = Grade.query.order_by(Grade.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_subjects=total_subjects,
        total_grades=total_grades,
        total_users=total_users,
        avg_gpa=avg_gpa,
        recent_grades=recent_grades
    )

@app.route('/students')
@login_required
def students():
    search_query = request.args.get('search', '').strip()
    if search_query:
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
    if request.method == 'POST':
        student_code = request.form.get('student_code', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        grade_level = request.form.get('grade_level', '').strip()

        if not all([student_code, first_name, last_name, email, grade_level]):
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
            grade_level=grade_level
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
    if request.method == 'POST':
        student.first_name = request.form.get('first_name', '').strip()
        student.last_name = request.form.get('last_name', '').strip()
        student.email = request.form.get('email', '').strip()
        student.grade_level = request.form.get('grade_level', '').strip()
        student.status = request.form.get('status', 'Active').strip()

        db.session.commit()
        flash('Student record updated successfully.', 'success')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)

@app.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully.', 'info')
    return redirect(url_for('students'))

@app.route('/grades', methods=['GET', 'POST'])
@login_required
def grades():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        score = float(request.form.get('score', 0))
        term = request.form.get('term', 'Fall 2026').strip()

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

    all_grades = Grade.query.order_by(Grade.created_at.desc()).all()
    all_students = Student.query.all()
    all_subjects = Subject.query.all()

    return render_template('grades.html', grades=all_grades, students=all_students, subjects=all_subjects)

if __name__ == '__main__':
    init_db_if_empty()
    app.run(debug=True, host='0.0.0.0', port=5000)
