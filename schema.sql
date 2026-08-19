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
    grade_level VARCHAR(100) NOT NULL, -- Department mapped as Grade Level
    department VARCHAR(80) NOT NULL DEFAULT 'Engineering',
    program_type VARCHAR(20) NOT NULL DEFAULT 'Bachelor',
    faculty VARCHAR(80) NOT NULL DEFAULT 'General',
    academic_period VARCHAR(40) NOT NULL DEFAULT 'Semester 1',
    status VARCHAR(40) DEFAULT 'Undergraduated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects / Courses Table with Department and Semester mapping
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(160) NOT NULL,
    department VARCHAR(80) DEFAULT 'Engineering',
    academic_period VARCHAR(40) DEFAULT 'Semester 1',
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
    term VARCHAR(60) NOT NULL DEFAULT 'Semester Exam 2082',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Sample SNS College Student Seed Data
INSERT INTO students (student_code, first_name, last_name, email, grade_level, department, program_type, faculty, academic_period, status) VALUES
('SNS-809214', 'Bigyata', 'Pradhan', 'bigyata.pradhan@sns.edu.np', 'Engineering', 'Engineering', 'Bachelor', 'Institute of Engineering (IOE)', 'Semester 1', 'Undergraduated'),
('SNS-809218', 'Smarika', 'Gurung', 'smarika.gurung@sns.edu.np', 'Management', 'Management', 'Bachelor', 'Faculty of Management (FOM)', 'Year 1', 'Undergraduated'),
('SNS-5-2-0041', 'Nishita', 'Dev', 'nishita.dev@sns.edu.np', 'Engineering', 'Engineering', 'Bachelor', 'Institute of Engineering (IOE)', 'Semester 3', 'Graduated'),
('SNS-5-2-0089', 'Nischal', 'Maharjan', 'nischal.maharjan@sns.edu.np', 'Medicine', 'Medicine', 'Bachelor', 'Institute of Medicine (IOM)', 'Year 2', 'Undergraduated'),

-- SNS Bachelor subjects 
INSERT INTO subjects (code, name, department, academic_period, faculty, level, credits) VALUES
('ENG-101', 'Engineering Mathematics I', 'Engineering', 'Semester 1', 'Institute of Engineering (IOE)', 'Bachelor', 3),
('CSIT-301', 'Data Structures & Algorithms', 'Engineering', 'Semester 2', 'Institute of Engineering (IOE)', 'Bachelor', 3),
('MED-101', 'Human Anatomy & Physiology', 'Medicine', 'Year 1', 'Institute of Medicine (IOM)', 'Bachelor', 4),
('MED-202', 'Clinical Pathology & Pharmacology', 'Medicine', 'Year 2', 'Institute of Medicine (IOM)', 'Bachelor', 4),
('BBA-305', 'Financial Management & Accounting', 'Management', 'Year 1', 'Faculty of Management (FOM)', 'Bachelor', 3),
('BBA-306', 'Marketing Management & Business Ethics', 'Management', 'Year 2', 'Faculty of Management (FOM)', 'Bachelor', 3),
('SCI-101', 'General Physics & Applied Mathematics', 'Science and Humanities', 'Year 1', 'Institute of Science and Technology (IOST)', 'Bachelor', 3),
('SCI-102', 'Organic Chemistry & Environmental Science', 'Science and Humanities', 'Year 2', 'Faculty of Humanities and Social Sciences (FOHSS)', 'Bachelor', 3);

-- Academic Classes / Sections Table
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    department VARCHAR(80) DEFAULT 'Engineering',
    level VARCHAR(20) DEFAULT 'Bachelor',
    description VARCHAR(255),
    advisor_id INTEGER,
    FOREIGN KEY (advisor_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Seed academic classes
INSERT INTO classes (code, name, department, level, description) VALUES
('SNS-ENG-01', 'Engineering Cohort 1', 'Engineering', 'Bachelor', 'Full-time software and systems engineering section.'),
('SNS-MED-01', 'Medicine Cohort 1', 'Medicine', 'Bachelor', 'Clinical MBBS research cohort.'),
('SNS-MGMT-01', 'Management Cohort 1', 'Management', 'Bachelor', 'Business administration cohort with leadership focus.'),
('SNS-SH-01', 'Science & Humanities Cohort 1', 'Science and Humanities', 'Bachelor', 'Advanced science and humanities cohort.');

-- Sample Grade Records
INSERT INTO grades (student_id, subject_id, score, letter_grade, term) VALUES
(1, 1, 92.5, 'A+', 'Semester Exam 2082'),
(1, 2, 88.0, 'A', 'Semester Exam 2082'),
(2, 5, 84.0, 'A', 'Semester Exam 2082'),
(3, 1, 95.0, 'A+', 'Semester Exam 2082'),
(3, 2, 91.0, 'A+', 'Semester Exam 2082'),
(4, 3, 89.5, 'A', 'Annual Exam 2082'),
(5, 6, 87.0, 'A', 'Annual Exam 2082'),
(6, 7, 93.0, 'A+', 'Annual Exam 2082'),
(7, 8, 88.5, 'A', 'Annual Exam 2082');
