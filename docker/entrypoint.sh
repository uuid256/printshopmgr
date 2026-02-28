#!/bin/bash
set -e

# Only run Django init steps when starting the web server.
# Celery workers share the same image but must NOT race to migrate.
if echo "$@" | grep -q "runserver"; then
    echo "📦 Running migrations..."
    uv run python manage.py migrate --noinput

    echo "📂 Loading initial fixtures..."
    uv run python manage.py loaddata fixtures/initial_data.json

    echo "👤 Creating default superuser if none exists..."
    uv run python manage.py shell -c "
from accounts.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Created superuser: admin / admin')
else:
    print('Superuser already exists, skipping.')
"
fi

exec "$@"
