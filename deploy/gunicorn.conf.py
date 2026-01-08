# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = "medshop"

# Server mechanics
daemon = False
pidfile = "/run/gunicorn/medshop.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if needed, uncomment)
# keyfile = "/etc/ssl/private/your-key.pem"
# certfile = "/etc/ssl/certs/your-cert.pem"
