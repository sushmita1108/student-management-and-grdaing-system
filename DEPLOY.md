# Public deployment

This project is prepared for Render's free web-service plan and an external PostgreSQL database. Render's free service has limited resources and may sleep while idle. Use a free PostgreSQL provider such as Neon or Supabase, and review its free-tier quotas, backups, and inactivity policy. The app's local SQLite file is not suitable for hosted persistence.

## Deploy

1. Create a free PostgreSQL database with a provider such as Neon or Supabase and copy its PostgreSQL connection string. Keep it private.
2. In Render, choose **New > Blueprint**, connect the repository, and select `render.yaml`.
3. Set `DATABASE_URL` to the external PostgreSQL connection string, `BOOTSTRAP_ADMIN_EMAIL` to an email you control, and `BOOTSTRAP_ADMIN_PASSWORD` to a unique, strong password. Enter secrets directly in Render; do not send them in chat or commit them.
4. Confirm creation of the free web service. Render builds the app and provides a public `https://...onrender.com` URL when deployment completes.
5. Sign in at `/login` with role **Campus Admin**, the bootstrap email, and bootstrap password. Change the password after first sign-in.

The production database is separate from the local SQLite database. Existing local student, subject, and grade data is not copied automatically; import it only through a deliberate, backed-up migration. Free database plans have storage, compute, backup, and inactivity limits; confirm the provider's current terms before relying on it for real student records.

## Local Windows production run

Install requirements once, then start Waitress from PowerShell in the project directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe wsgi.py
```

The local server listens on `0.0.0.0:5000` by default. `HOST` and `PORT` can override the bind address and port. This makes the app reachable on your local network, not the public internet.
