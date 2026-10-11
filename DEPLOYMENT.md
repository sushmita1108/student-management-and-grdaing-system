# Deploying to Vercel

## Prepare the database

Create a hosted PostgreSQL database with a provider such as Neon or Supabase. Copy its PostgreSQL connection URL; Vercel's local filesystem is temporary, so do not use SQLite for a deployed database.

## Configure Vercel

Import this repository as a Vercel project and add these environment variables in **Project Settings > Environment Variables** for each environment you plan to deploy:

- `DATABASE_URL`: the hosted PostgreSQL connection URL
- `SECRET_KEY`: a long, random secret used to sign sessions
- `INITIAL_ADMIN_PASSWORD`: a strong password for the first admin account

The first startup creates the database tables and an admin account with username `admin` and email `admin@sns.edu.np`. Its password is the value of `INITIAL_ADMIN_PASSWORD`. Other demo accounts are not created in production. Add staff and students after signing in.

## Deploy

Deploy from the Vercel dashboard, or install the Vercel CLI and run `vercel --prod` from the project directory. Vercel detects the Flask application in `app.py` and installs packages from `requirements.txt`.

The existing SQLite database in `instance/` is not copied into PostgreSQL. Migrate any data you need before using this deployment for real records.