import sqlite3
import os

path = os.path.join('instance', 'school.db')
print('db', os.path.abspath(path), 'exists', os.path.exists(path))
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute('PRAGMA table_info(subjects)')
cols = [row[1] for row in cur.fetchall()]
print('cols before', cols)
changed = False
if 'faculty' not in cols:
    cur.execute("ALTER TABLE subjects ADD COLUMN faculty VARCHAR(80) DEFAULT 'General'")
    print('added faculty')
    changed = True
if 'level' not in cols:
    cur.execute("ALTER TABLE subjects ADD COLUMN level VARCHAR(20) DEFAULT 'Bachelor'")
    print('added level')
    changed = True
if 'assigned_teacher_id' not in cols:
    cur.execute("ALTER TABLE subjects ADD COLUMN assigned_teacher_id INTEGER")
    print('added assigned_teacher_id')
    changed = True
if changed:
    conn.commit()
cur.execute('PRAGMA table_info(subjects)')
print('cols after', [row[1] for row in cur.fetchall()])
conn.close()