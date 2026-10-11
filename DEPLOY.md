# Public deployment

This project is prepared for Render with a managed PostgreSQL database. The Render blueprint uses paid web-service and database plans so the database persists across deploys and restarts.

## Deploy

1. Push this project to a private GitHub repository. `.gitignore` now excludes `.env`, `.venv`, Python caches, and local instance data. These local `.env` and `instance/school.db` files were previously tracked, so confirm they are removed from the Git index before pushing. Rotate any credentials that have appeared in earlier Git history.
2. In Render, choose **New > Blueprint**, connect the repository, and select `render.yaml`.
3. Set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` when prompted. Use an email you control and a unique, strong password; do not send the password in chat or commit it to the repository.
4. Confirm creation of the web service and PostgreSQL database. Render builds the app and provides the public `https://...onrender.com` URL when deployment completes.
5. Sign in to `/login` with username `admin` and the bootstrap password. Change the password after the first sign-in if the app's account settings support it.

The production database is separate from the local SQLite database. Existing local student, subject, and grade data is not copied automatically; import it only through a deliberate, backed-up migration.

## Local Windows production run

Install requirements once, then start Waitress from PowerShell in the project directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe wsgi.py
```

The local server listens on `0.0.0.0:5000` by default. `HOST` and `PORT` can override the bind address and port. This makes the app reachable on your local network, not the public internet.
