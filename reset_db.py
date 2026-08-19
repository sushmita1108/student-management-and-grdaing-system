import os
from app import app, init_db_if_empty

db_paths = [
    os.path.join(app.instance_path, 'school.db'),
    os.path.join(os.path.dirname(__file__), 'school.db'),
    os.path.join(os.path.dirname(__file__), 'instance', 'school.db')
]

for p in db_paths:
    if os.path.exists(p):
        try:
            os.remove(p)
            print(f"Removed {p}")
        except Exception as e:
            print(f"Could not remove {p}: {e}")

init_db_if_empty()
print("Database initialized successfully.")
