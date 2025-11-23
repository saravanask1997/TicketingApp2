# Deployment Guide

## Production Deployment Setup

This guide covers deploying the Django Ticketing System to production.

### Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Python 3.11+
- PostgreSQL 12+
- Redis server
- Nginx
- Domain name with SSL certificate

## Step 1: Server Setup

### Install System Dependencies
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx
```

### Create Application User
```bash
sudo adduser ticketing
sudo usermod -aG sudo ticketing
```

## Step 2: Application Setup

### Clone Repository
```bash
sudo -u ticketing git clone <repository-url> /home/ticketing/app
cd /home/ticketing/app/backend
```

### Create Virtual Environment
```bash
sudo -u ticketing python3.11 -m venv venv
sudo -u ticketing /home/ticketing/app/backend/venv/bin/pip install -r requirements.txt
```

### Environment Configuration
```bash
sudo -u ticketing cp .env.example .env
sudo -u ticketing nano .env
```

Configure production settings:
```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=ticketing_system
DB_USER=ticketing_user
DB_PASSWORD=secure_password
EMAIL_HOST=smtp.yourprovider.com
SECRET_KEY=your-production-secret-key
```

## Step 3: Database Setup

### Create Database and User
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE ticketing_system;
CREATE USER ticketing_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ticketing_system TO ticketing_user;
\q
```

### Run Migrations
```bash
sudo -u ticketing /home/ticketing/app/backend/venv/bin/python manage.py makemigrations
sudo -u ticketing /home/ticketing/app/backend/venv/bin/python manage.py migrate
```

### Create Superuser
```bash
sudo -u ticketing /home/ticketing/app/backend/venv/bin/python manage.py createsuperuser
```

### Collect Static Files
```bash
sudo -u ticketing /home/ticketing/app/backend/venv/bin/python manage.py collectstatic --noinput
```

## Step 4: Gunicorn Setup

### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/ticketing.service
```

```ini
[Unit]
Description=ticketing system daemon
After=network.target

[Service]
User=ticketing
Group=www-data
WorkingDirectory=/home/ticketing/app/backend
ExecStart=/home/ticketing/app/backend/venv/bin/gunicorn --workers 3 --bind unix:/run/ticketing.sock ticketing_system.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start and Enable Service
```bash
sudo systemctl start ticketing
sudo systemctl enable ticketing
```

## Step 5: Celery Setup

### Create Celery Worker Service
```bash
sudo nano /etc/systemd/system/celery.service
```

```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
User=ticketing
Group=www-data
WorkingDirectory=/home/ticketing/app/backend
ExecStart=/home/ticketing/app/backend/venv/bin/celery -A ticketing_system worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

### Create Celery Beat Service
```bash
sudo nano /etc/systemd/system/celerybeat.service
```

```ini
[Unit]
Description=Celery Beat
After=network.target

[Service]
User=ticketing
Group=www-data
WorkingDirectory=/home/ticketing/app/backend
ExecStart=/home/ticketing/app/backend/venv/bin/celery -A ticketing_system beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

### Start and Enable Celery Services
```bash
sudo systemctl start celery celerybeat
sudo systemctl enable celery celerybeat
```

## Step 6: Nginx Setup

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/ticketing
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/ssl/fullchain.pem;
    ssl_certificate_key /path/to/ssl/privkey.pem;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ticketing/app/backend;
        expires 30d;
    }

    location /media/ {
        root /home/ticketing/app/backend;
        expires 30d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/ticketing.sock;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/ticketing /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: SSL Certificate

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtain Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Auto-renewal
```bash
sudo crontab -e
```

Add line:
```
0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 8: Security Hardening

### Firewall Configuration
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### File Permissions
```bash
sudo chown -R ticketing:www-data /home/ticketing/app
sudo chmod -R 755 /home/ticketing/app
```

### Security Headers (Django settings)
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Step 9: Monitoring and Logging

### Application Logging
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/ticketing/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Create Log Directory
```bash
sudo mkdir -p /home/ticketing/logs
sudo chown ticketing:www-data /home/ticketing/logs
```

### Health Check Script
```bash
sudo nano /home/ticketing/health_check.sh
```

```bash
#!/bin/bash
# Health check for ticketing system

# Check if Gunicorn is running
if ! systemctl is-active --quiet ticketing; then
    echo "Gunicorn service is not running"
    systemctl restart ticketing
fi

# Check if Celery is running
if ! systemctl is-active --quiet celery; then
    echo "Celery service is not running"
    systemctl restart celery
fi

# Check database connectivity
cd /home/ticketing/app/backend
./venv/bin/python manage.py check --deploy
```

Make executable and set up cron job:
```bash
sudo chmod +x /home/ticketing/health_check.sh
sudo crontab -e
```

Add line:
```
*/5 * * * * /home/ticketing/health_check.sh
```

## Step 10: Backup Strategy

### Database Backup Script
```bash
sudo nano /home/ticketing/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/ticketing/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U ticketing_user ticketing_system > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/ticketing/app/backend/media/

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Set up cron job for daily backups:
```bash
sudo chmod +x /home/ticketing/backup.sh
sudo crontab -e
```

Add line:
```
0 2 * * * /home/ticketing/backup.sh
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Check if Gunicorn is running
   ```bash
   sudo systemctl status ticketing
   ```

2. **Database Connection Errors**: Verify database credentials and connectivity
   ```bash
   sudo -u ticketing ./venv/bin/python manage.py dbshell
   ```

3. **Static Files Not Loading**: Check Nginx configuration and file permissions
   ```bash
   sudo nginx -t
   ls -la /home/ticketing/app/backend/static/
   ```

4. **Email Not Working**: Verify SMTP configuration
   ```bash
   sudo -u ticketing ./venv/bin/python manage.py shell
   # Test email sending
   ```

### Log Locations
- **Application logs**: `/home/ticketing/logs/django.log`
- **Nginx logs**: `/var/log/nginx/`
- **System logs**: `journalctl -u ticketing`
- **Celery logs**: `journalctl -u celery`

## Performance Tuning

### Database Optimization
```sql
-- Add indexes for frequently queried fields
CREATE INDEX CONCURRENTLY idx_tickets_status ON tickets(status);
CREATE INDEX CONCURRENTLY idx_tickets_priority ON tickets(priority);
CREATE INDEX CONCURRENTLY idx_tickets_created_by ON tickets(created_by);
```

### Gunicorn Optimization
```ini
# Increase workers based on CPU cores
workers = 4
worker_class = gevent
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
```

### Redis Configuration
```bash
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Maintenance

### Regular Updates
1. Update system packages
2. Update Python dependencies
3. Update Nginx and SSL certificates
4. Monitor disk space and performance metrics

### Scaling Considerations
- Load balancer for multiple application servers
- Database read replicas for high traffic
- CDN for static file delivery
- Separate Redis server for better performance