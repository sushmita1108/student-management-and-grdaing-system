-- Database Schema for Nepal National University & Higher Secondary System (NEB & TU / KU Nepal)

DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- Users Table (Campus Chiefs, Deans, Lecturers)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'Teacher',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students Table (Higher Secondary +2 and University Students)
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code VARCHAR(30) UNIQUE NOT NULL, -- Symbol No. / Registration Code
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    grade_level VARCHAR(80) NOT NULL, -- Program Stream (e.g. +2 Science, B.Sc. CSIT, BCA, BBA)
    status VARCHAR(30) DEFAULT 'Active (Passed)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects / Courses Table (NEB +2 Curriculum & University Subjects)
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    credits INTEGER DEFAULT 3
);

-- Grades & Academic Evaluation Table
CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
    letter_grade VARCHAR(4),
    term VARCHAR(40) NOT NULL DEFAULT 'Board Exam 2082 (2026)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Authentic Nepalese Higher Secondary (+2) & University Student Seed Data
INSERT INTO students (student_code, first_name, last_name, email, grade_level, status) VALUES
('NEB-809214', 'Aarav', 'Sharma', 'aarav.sharma@tu.edu.np', '+2 Science (Grade 12 - Physics/Math)', 'Active (Distinction List)'),
('TU-5-2-0041', 'Pooja', 'Shrestha', 'pooja.shrestha@tu.edu.np', 'B.Sc. CSIT (3rd Year - TU Affiliated)', 'Active (First Division with Distinction)'),
('KU-2026-081', 'Bibek', 'Thapa', 'bibek.thapa@ku.edu.np', 'B.E. Computer Engineering (KU)', 'Active (Dean''s Honor List)'),
('NEB-809218', 'Smarika', 'Gurung', 'smarika.gurung@neb.edu.np', '+2 Management (Grade 11 - Finance)', 'Active (First Division)'),
('TU-5-2-0089', 'Rohan', 'Maharjan', 'rohan.maharjan@tu.edu.np', 'BCA - Bachelor of Computer Application', 'Active (First Division)'),
('TU-5-2-0104', 'Anusha', 'Adhikari', 'anusha.adhikari@tu.edu.np', 'BBA - Bachelor of Business Administration', 'Active (First Division)');

-- NEB +2 Higher Secondary & University Subjects
INSERT INTO subjects (code, name, credits) VALUES
('COMP-101', 'Compulsory English & Technical Writing (+2 / Undergrad)', 3),
('NEP-102', 'Compulsory Nepali & Literature (अनिवार्य नेपाली)', 3),
('PHY-201', 'Physics - Electromagnetism & Quantum Physics (+2 Science)', 4),
('CHEM-202', 'Chemistry - Organic & Physical Chemistry (+2 Science)', 4),
('MATH-203', 'Mathematics - Calculus & Linear Algebra (+2 / CSIT)', 4),
('CSIT-301', 'B.Sc. CSIT - Data Structures & Algorithms', 3),
('CSIT-302', 'B.Sc. CSIT - Web Technology & Database Management', 3),
('BCA-303', 'BCA - Object Oriented Programming in C++', 3),
('BBA-305', 'BBA - Financial Management & Accounting', 3);

-- Sample Grade Records
INSERT INTO grades (student_id, subject_id, score, letter_grade, term) VALUES
(1, 3, 92.5, 'A+', 'NEB Board Exam 2082'),
(1, 5, 88.0, 'A', 'NEB Board Exam 2082'),
(2, 6, 95.0, 'A+', 'TU Final Exam 2082'),
(2, 7, 91.0, 'A+', 'TU Final Exam 2082'),
(3, 6, 86.5, 'A', 'KU Semester Exam 2082'),
(4, 1, 82.0, 'A', 'NEB Board Exam 2082'),
(5, 8, 89.5, 'A', 'TU Semester Exam 2082'),
(6, 9, 87.0, 'A', 'TU Semester Exam 2082');
