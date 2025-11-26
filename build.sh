#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Fixing migration conflicts..."
# Prevent "column image already exists" error
python manage.py migrate medicines 0003 --fake || true

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating sample data..."
python manage.py create_sample_data || echo "Sample data already exists"

echo "Build completed successfully!"
