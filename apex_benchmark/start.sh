#!/bin/sh
set -e

echo "Creating database if not exists..."
python -c "
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

url = os.environ['DATABASE_URL']
# Connect to default postgres db to create our db
base_url = url.rsplit('/', 1)[0] + '/postgres'
conn = psycopg2.connect(base_url)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute(\"SELECT 1 FROM pg_database WHERE datname = 'apexbenchmark'\")
if not cur.fetchone():
    cur.execute('CREATE DATABASE apexbenchmark')
    print('Database created.')
else:
    print('Database already exists.')
cur.close()
conn.close()
"

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -m app.db.seed || echo "Seed skipped (data may already exist)"

echo "Starting server..."
exec uvicorn app.main:main --host 0.0.0.0 --port 8000
