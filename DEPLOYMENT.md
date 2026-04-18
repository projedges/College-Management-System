# EduTrack — Deployment Guide

**Version:** 2.0 (with Celery, Redis, REST API)  
**Date:** April 17, 2026

---

## What's New in 2.0

✅ **CGPA Calculation** — Already implemented  
✅ **Transcript PDF** — Already implemented  
✅ **Unified Marks Entry** — Single page for internal + external marks  
✅ **Bulk Attendance** — "Mark All Present/Absent" buttons (already implemented)  
✅ **Fee Reminders** — Automated daily email reminders via Celery  
✅ **Seating Arrangement** — Auto-assign room + seat number to hall tickets  
✅ **Celery Background Tasks** — Async result generation, bulk emails  
✅ **Redis Caching** — Fast dashboard loads  
✅ **REST API** — JWT-authenticated endpoints for mobile app  

---

## Prerequisites

- Python 3.10+
- Redis 6.0+ (for Celery + caching)
- MySQL 8.0+ or PostgreSQL 13+ (production)
- SMTP server (for email) or Twilio (for SMS)

---

## Installation

### 1. Clone & Setup

```bash
git clone <repo-url>
cd College-Management-System
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create `.env` file:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SITE_URL=https://yourdomain.com

# Database (MySQL example)
DATABASE_URL=mysql://user:password@localhost:3306/edutrack_db

# Redis (required for Celery + caching)
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=EduTrack <your@email.com>

# Razorpay (payment gateway)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx

# Twilio SMS (optional)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 4. Redis Setup

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping  # Should return PONG
```

### 5. Celery Setup

```bash
# Start Celery worker (background tasks)
celery -A studentmanagementsystem worker -l info --detach

# Start Celery beat (scheduler for periodic tasks)
celery -A studentmanagementsystem beat -l info --detach

# Check status
celery -A studentmanagementsystem status
```

### 6. Run Server

```bash
# Development
python manage.py runserver

# Production (use Gunicorn)
gunicorn studentmanagementsystem.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Celery Tasks

### Automated Tasks (via Celery Beat)

1. **Fee Reminders** — Daily at 9 AM IST
   - Sends email 7 days before due date
   - Sends email 3 days before due date
   - Sends overdue reminder

2. **Attendance Alerts** — Daily at 8 AM IST
   - Sends email to students below 75% attendance
   - Calculates classes needed to meet minimum

### Manual Tasks

- `generate_results_bulk(exam_id, student_ids, user_id)` — Async result generation
- `send_bulk_announcement(announcement_id)` — Email announcement to all students

---

## REST API

### Authentication

```bash
# Obtain JWT token
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "password"}'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use access token in subsequent requests
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  http://localhost:8000/api/v1/dashboard/
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/token/` | Obtain JWT token pair |
| POST | `/api/v1/token/refresh/` | Refresh access token |
| GET | `/api/v1/me/` | Current user profile |
| GET | `/api/v1/dashboard/` | Student dashboard summary |
| GET | `/api/v1/attendance/` | Per-subject attendance |
| GET | `/api/v1/results/` | All semester results |
| GET | `/api/v1/timetable/` | Today's timetable |
| GET | `/api/v1/assignments/` | Pending assignments |
| GET | `/api/v1/quizzes/` | Active quizzes |
| GET | `/api/v1/fees/` | Fee status |
| GET | `/api/v1/notifications/` | Unread notifications |
| POST | `/api/v1/notifications/mark-read/` | Mark all as read |
| GET | `/api/v1/announcements/` | College announcements |

---

## New Features Usage

### 1. Unified Marks Entry

**URL:** `/dashboard/faculty/marks-entry/<subject_id>/`

Faculty can now enter both internal marks (IA1, IA2, assignment, attendance) and external marks (per exam) on a single tabbed page.

**Old URLs (still work for backward compatibility):**
- `/dashboard/faculty/internal-marks/<subject_id>/`
- `/dashboard/faculty/marks/<subject_id>/<exam_id>/`

### 2. Seating Arrangement

When exam controller clicks "Generate Hall Tickets", the system now:
1. Checks eligibility (attendance + fees)
2. Auto-assigns room + seat number to eligible students
3. Uses available classrooms in order
4. Assigns seats as A1, A2, ..., A10, B1, B2, etc.

**Hall ticket now shows:**
- Room Number
- Seat Number
- Row Number

### 3. Fee Reminders

Automated emails sent daily at 9 AM IST:
- 7-day advance reminder
- 3-day advance reminder
- Overdue reminder (with late fee warning)

**To disable:** Stop Celery beat process.

### 4. Attendance Alerts

Automated emails sent daily at 8 AM IST to students below 75% attendance.

**To customize threshold:** Update `AttendanceRule` per college/department.

---

## Production Deployment

### Using Gunicorn + Nginx

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create systemd service** (`/etc/systemd/system/edutrack.service`):
   ```ini
   [Unit]
   Description=EduTrack Django App
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/edutrack
   Environment="PATH=/var/www/edutrack/venv/bin"
   ExecStart=/var/www/edutrack/venv/bin/gunicorn \
     --workers 4 \
     --bind unix:/var/www/edutrack/edutrack.sock \
     studentmanagementsystem.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Create Celery worker service** (`/etc/systemd/system/edutrack-celery.service`):
   ```ini
   [Unit]
   Description=EduTrack Celery Worker
   After=network.target redis.service

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/edutrack
   Environment="PATH=/var/www/edutrack/venv/bin"
   ExecStart=/var/www/edutrack/venv/bin/celery -A studentmanagementsystem worker -l info

   [Install]
   WantedBy=multi-user.target
   ```

4. **Create Celery beat service** (`/etc/systemd/system/edutrack-celerybeat.service`):
   ```ini
   [Unit]
   Description=EduTrack Celery Beat
   After=network.target redis.service

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/edutrack
   Environment="PATH=/var/www/edutrack/venv/bin"
   ExecStart=/var/www/edutrack/venv/bin/celery -A studentmanagementsystem beat -l info

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start services:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start edutrack
   sudo systemctl start edutrack-celery
   sudo systemctl start edutrack-celerybeat
   sudo systemctl enable edutrack
   sudo systemctl enable edutrack-celery
   sudo systemctl enable edutrack-celerybeat
   ```

6. **Configure Nginx** (`/etc/nginx/sites-available/edutrack`):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location /static/ {
           alias /var/www/edutrack/staticfiles/;
       }

       location /media/ {
           alias /var/www/edutrack/media/;
       }

       location / {
           proxy_pass http://unix:/var/www/edutrack/edutrack.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

7. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/edutrack /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## Monitoring

### Celery Flower (Web UI)

```bash
pip install flower
celery -A studentmanagementsystem flower --port=5555
```

Access at: `http://localhost:5555`

### Redis Monitor

```bash
redis-cli monitor
```

### Django Logs

```bash
tail -f /var/log/edutrack/django.log
```

---

## Troubleshooting

### Celery tasks not running

```bash
# Check worker status
celery -A studentmanagementsystem status

# Check beat schedule
celery -A studentmanagementsystem beat --loglevel=debug

# Restart services
sudo systemctl restart edutrack-celery
sudo systemctl restart edutrack-celerybeat
```

### Redis connection error

```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli ping

# Check Redis URL in .env
echo $REDIS_URL
```

### Email not sending

```bash
# Test SMTP connection
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
```

### API 401 Unauthorized

```bash
# Check JWT token expiry
# Access tokens expire after 8 hours
# Use refresh token to get new access token

curl -X POST http://localhost:8000/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your-refresh-token"}'
```

---

## Backup & Restore

### Database Backup

```bash
# MySQL
mysqldump -u user -p edutrack_db > backup_$(date +%Y%m%d).sql

# PostgreSQL
pg_dump edutrack_db > backup_$(date +%Y%m%d).sql
```

### Media Files Backup

```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

### Restore

```bash
# MySQL
mysql -u user -p edutrack_db < backup_20260417.sql

# PostgreSQL
psql edutrack_db < backup_20260417.sql

# Media files
tar -xzf media_backup_20260417.tar.gz
```

---

## Performance Tuning

### Redis Memory Limit

Edit `/etc/redis/redis.conf`:
```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Celery Concurrency

```bash
# Increase workers (default: CPU count)
celery -A studentmanagementsystem worker -l info --concurrency=8
```

### Database Connection Pooling

In `settings.py`:
```python
DATABASES = {
    'default': {
        # ... existing config ...
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

---

## Security Checklist

- [ ] `DJANGO_DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (50+ random characters)
- [ ] HTTPS enabled (SSL certificate)
- [ ] `ALLOWED_HOSTS` configured
- [ ] Database password is strong
- [ ] Redis password set (if exposed to internet)
- [ ] Firewall rules configured (only 80/443 open)
- [ ] Regular backups scheduled
- [ ] Celery tasks use `bind=True` and `max_retries`
- [ ] API rate limiting enabled (DRF throttling)
- [ ] CORS headers configured (if needed)

---

## Support

For issues or questions:
- Check `docs/REAL_WORLD_FLOW_AUDIT.md` for known gaps
- Check `docs/IMPLEMENTATION_PLAN.md` for roadmap
- Check logs: `/var/log/edutrack/`

---

**End of Deployment Guide**
