from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Teacher')  # 'Admin', 'Teacher', 'Student'
    department = db.Column(db.String(80), default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    grade_level = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(80), default='General')
    faculty = db.Column(db.String(80), default='General')
    academic_period = db.Column(db.String(40), default='Semester 1')
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    grades = db.relationship('Grade', backref='student', lazy=True, cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def gpa(self):
        if not self.grades:
            return 0.0
        total_points = sum(g.gpa_points for g in self.grades)
        return round(total_points / len(self.grades), 2)


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(80), default='General')
    level = db.Column(db.String(20), default='Bachelor')
    credits = db.Column(db.Integer, default=3)
    assigned_teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    grades = db.relationship('Grade', backref='subject', lazy=True)
    assigned_teacher = db.relationship('User', backref='assigned_subjects', foreign_keys=[assigned_teacher_id])


class AcademicClass(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), default='General')
    level = db.Column(db.String(20), default='Bachelor')
    description = db.Column(db.String(255), nullable=True)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    advisor = db.relationship('User', backref='advised_classes', foreign_keys=[advisor_id])


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    letter_grade = db.Column(db.String(2))
    term = db.Column(db.String(20), default='Fall 2026')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def calculate_letter_grade(score):
        if score >= 97: return 'A+', 4.0
        elif score >= 93: return 'A', 4.0
        elif score >= 90: return 'A-', 3.7
        elif score >= 87: return 'B+', 3.3
        elif score >= 83: return 'B', 3.0
        elif score >= 80: return 'B-', 2.7
        elif score >= 77: return 'C+', 2.3
        elif score >= 73: return 'C', 2.0
        elif score >= 70: return 'C-', 1.7
        elif score >= 60: return 'D', 1.0
        else: return 'F', 0.0

    @property
    def display_letter_grade(self):
        if self.letter_grade == 'D':
            return 'D (Fail)'
        return self.letter_grade

    @property
    def gpa_points(self):
        _, points = self.calculate_letter_grade(self.score)
        return points
