#!/bin/bash
# VPS Deployment Script for Medshop Django Application
# Run as root: bash setup_server.sh

set -e

echo "=========================================="
echo "  Medshop VPS Deployment Script"
echo "=========================================="

# Variables - UPDATE THESE
APP_NAME="medshop"
APP_DIR="/var/www/medshop"
DOMAIN="72.61.238.239"  # Change to your domain later

# Update system
echo "[1/10] Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "[2/10] Installing required packages..."
apt install -y python3 python3-pip python3-venv python3-dev \
    nginx mysql-server libmysqlclient-dev \
    git curl supervisor

# Create application directory
echo "[3/10] Setting up application directory..."
mkdir -p $APP_DIR
mkdir -p /var/log/gunicorn
mkdir -p /run/gunicorn

# Create www-data user directories
chown -R www-data:www-data /var/log/gunicorn
chown -R www-data:www-data /run/gunicorn

echo "[4/10] Application directory ready at $APP_DIR"
echo ""
echo "=========================================="
echo "  NEXT STEPS - Run these manually:"
echo "=========================================="
echo ""
echo "1. Upload your project files to $APP_DIR"
echo "   From your local machine:"
echo "   scp -r ./* root@72.61.238.239:$APP_DIR/"
echo ""
echo "2. Then run the app setup script:"
echo "   bash $APP_DIR/deploy/setup_app.sh"
echo ""
