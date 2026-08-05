-- Database Schema for SNS College Student Grading System

DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- Users Table (Admin, Department, Teacher, Student roles)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'Student',
    department VARCHAR(80) DEFAULT 'General',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students Table (Higher Secondary +2 and University students)
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code VARCHAR(40) UNIQUE NOT NULL, -- Symbol No. / Registration Code
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    grade_level VARCHAR(100) NOT NULL, -- Program Stream (e.g. +2 Science, B.Sc. CSIT, M.Sc. Data Science)
    program_type VARCHAR(20) NOT NULL DEFAULT 'Bachelor',
    faculty VARCHAR(80) NOT NULL DEFAULT 'General',
    academic_period VARCHAR(40) NOT NULL DEFAULT 'Semester 1',
    status VARCHAR(40) DEFAULT 'Active (Passed)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects / Courses Table with Bachelor and Master faculty mapping
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(160) NOT NULL,
    faculty VARCHAR(80) DEFAULT 'General',
    level VARCHAR(20) DEFAULT 'Bachelor',
    credits INTEGER DEFAULT 3,
    assigned_teacher_id INTEGER,
    FOREIGN KEY (assigned_teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Grades & Academic Evaluation Table
CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
    letter_grade VARCHAR(4),
    term VARCHAR(60) NOT NULL DEFAULT 'Board Exam 2082 (2026)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Sample SNS College Student Seed Data
INSERT INTO students (student_code, first_name, last_name, email, grade_level, program_type, faculty, status) VALUES
('SNS-809214', 'Aarav', 'Sharma', 'aarav.sharma@sns.edu.np', '+2 Science (Grade 12)', 'Bachelor', 'Science', 'Active (Distinction List)'),
('SNS-809218', 'Smarika', 'Gurung', 'smarika.gurung@sns.edu.np', '+2 Management (Grade 11)', 'Bachelor', 'Management', 'Active (First Division)'),
('SNS-5-2-0041', 'Pooja', 'Shrestha', 'pooja.shrestha@sns.edu.np', 'B.Sc. CSIT (3rd Year)', 'Bachelor', 'Science & Technology', 'Active (First Division with Distinction)'),
('SNS-5-2-0089', 'Rohan', 'Maharjan', 'rohan.maharjan@sns.edu.np', 'BCA - Bachelor of Computer Application', 'Bachelor', 'Science & Technology', 'Active (First Division)'),
('SNS-5-2-0104', 'Anusha', 'Adhikari', 'anusha.adikari@sns.edu.np', 'BBA - Bachelor of Business Administration', 'Bachelor', 'Management', 'Active (First Division)'),
('SNS-7-1-0123', 'Mina', 'KC', 'mina.kc@sns.edu.np', 'M.Sc. Data Science', 'Master', 'Science & Technology', 'Active (Research Scholar)'),
('SNS-7-1-0145', 'Ritesh', 'Adhikari', 'ritesh.adhikari@sns.edu.np', 'M.Sc. Management', 'Master', 'Management', 'Active (Thesis Track)');

-- SNS College Higher Secondary, Bachelor, and Master Subjects by faculty
INSERT INTO subjects (code, name, faculty, level, credits) VALUES
('ENG-101', 'English Communication & Academic Writing', 'Science & Technology', 'Bachelor', 3),
('NEP-102', 'Nepali Language & Literature', 'Management', 'Bachelor', 3),
('PHY-201', 'Physics - Mechanics & Modern Physics', 'Science & Technology', 'Bachelor', 4),
('CHEM-202', 'Chemistry - Organic & Inorganic Chemistry', 'Science & Technology', 'Bachelor', 4),
('MATH-203', 'Mathematics - Calculus, Statistics & Linear Algebra', 'Science & Technology', 'Bachelor', 4),
('CSIT-301', 'B.Sc. CSIT - Data Structures & Algorithms', 'Science & Technology', 'Bachelor', 3),
('CSIT-302', 'B.Sc. CSIT - Database Systems & Web Technology', 'Science & Technology', 'Bachelor', 3),
('BCA-303', 'BCA - Object Oriented Programming & Software Design', 'Science & Technology', 'Bachelor', 3),
('BBA-305', 'BBA - Financial Management & Accounting', 'Management', 'Bachelor', 3),
('BBA-306', 'BBA - Marketing Management & Ethics', 'Management', 'Bachelor', 3),
('MSC-501', 'M.Sc. Data Science - Statistical Methods & Machine Learning', 'Science & Technology', 'Master', 4),
('MSC-502', 'M.Sc. Management - Strategic Planning & Leadership', 'Management', 'Master', 4),
('MSC-503', 'M.Sc. Information Systems - Cloud & Security Governance', 'Science & Technology', 'Master', 4);

-- Academic Classes / Sections Table
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    department VARCHAR(80) DEFAULT 'General',
    level VARCHAR(20) DEFAULT 'Bachelor',
    description VARCHAR(255),
    advisor_id INTEGER,
    FOREIGN KEY (advisor_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Seed academic classes
INSERT INTO classes (code, name, department, level, description) VALUES
('SNS-CSIT-01', 'B.Sc. CSIT Section 1', 'Science & Technology', 'Bachelor', 'Full-time software development and systems section.'),
('SNS-BBA-01', 'BBA Management Section 1', 'Management', 'Bachelor', 'Business administration cohort with leadership focus.'),
('SNS-MSC-01', 'M.Sc. Data Science Cohort', 'Science & Technology', 'Master', 'Advanced analytics and machine learning research track.');

-- Sample Grade Records
INSERT INTO grades (student_id, subject_id, score, letter_grade, term) VALUES
(1, 3, 92.5, 'A+', 'NEB Board Exam 2082'),
(1, 5, 88.0, 'A', 'NEB Board Exam 2082'),
(2, 2, 84.0, 'A', 'NEB Board Exam 2082'),
(3, 6, 95.0, 'A+', 'TU Final Exam 2082'),
(3, 7, 91.0, 'A+', 'TU Final Exam 2082'),
(4, 9, 89.5, 'A', 'TU Semester Exam 2082'),
(5, 10, 87.0, 'A', 'TU Semester Exam 2082'),
(6, 11, 93.0, 'A+', 'TU Semester Exam 2082'),
(7, 12, 88.5, 'A', 'TU Semester Exam 2082');
