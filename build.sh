#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear
echo "Static files collected!"

python manage.py migrate
