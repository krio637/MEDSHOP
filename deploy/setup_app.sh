#!/bin/bash
# Application Setup Script - Run after uploading files
# Run as root: bash /var/www/medshop/deploy/setup_app.sh

set -e

APP_DIR="/var/www/medshop"
cd $APP_DIR

echo "=========================================="
echo "  Setting up Medshop Application"
echo "=========================================="

# Create virtual environment
echo "[1/8] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[2/8] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "[3/8] Creating .env file..."
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=72.61.238.239,localhost,127.0.0.1

# SQLite (default) - change to MySQL if needed
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=medshop
# DB_USER=medshop_user
# DB_PASSWORD=your_secure_password
# DB_HOST=localhost
# DB_PORT=3306
EOF
    echo "   .env file created with new SECRET_KEY"
else
    echo "[3/8] .env file already exists, skipping..."
fi

# Collect static files
echo "[4/8] Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "[5/8] Running database migrations..."
python manage.py migrate --no-input

# Set permissions
echo "[6/8] Setting file permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Setup Nginx
echo "[7/8] Configuring Nginx..."
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/medshop
ln -sf /etc/nginx/sites-available/medshop /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Setup Gunicorn systemd service
echo "[8/8] Setting up Gunicorn service..."
cp $APP_DIR/deploy/medshop.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable medshop
systemctl start medshop

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Your app should be running at: http://72.61.238.239"
echo ""
echo "Useful commands:"
echo "  - Check status:  systemctl status medshop"
echo "  - View logs:     journalctl -u medshop -f"
echo "  - Restart app:   systemctl restart medshop"
echo "  - Nginx logs:    tail -f /var/log/nginx/error.log"
echo ""
echo "To create admin user:"
echo "  cd $APP_DIR && source venv/bin/activate"
echo "  python manage.py createsuperuser"
echo ""
