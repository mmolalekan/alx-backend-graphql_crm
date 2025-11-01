# CRM Setup Guide

### Step 1: Install Redis
Install Redis on your local machine:

- **Linux**: `sudo apt-get install redis-server`
- **macOS**: `brew install redis`
- **Windows**: Use **WSL** or Docker to run Redis.

Start the Redis server:

```bash
    redis-server

In a separate terminal, run the Celery worker:
    celery -A crm worker -l info

In another terminal, run Celery Beat:
    celery -A crm beat -l info

Run the migrations:
    python manage.py migrate

Step 2: Install Python dependencies
Install required packages:
    pip install -r requirements.txt

Step 3: Configure Django
- Add 'django_celery_beat' and 'django_crontab' to INSTALLED_APPS in crm/settings.py
- Add Celery and CRONJOBS configuration in crm/settings.py:
    from celery.schedules import crontab
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_BEAT_SCHEDULE = {
        'generate-crm-report': {
            'task': 'crm.tasks.generate_crm_report',
            'schedule': crontab(day_of_week='mon', hour=6, minute=0),
        },
    }
    CRONJOBS = [
        ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
        ('0 */12 * * *', 'crm.cron.update_low_stock'),
    ]

Step 4: Run cron jobs
Add cron jobs:
    python manage.py crontab add

Step 5: Verify logs
Check the following log files:
- /tmp/crm_report_log.txt for weekly reports
- /tmp/crm_heartbeat_log.txt for heartbeat logs
- /tmp/low_stock_updates_log.txt for stock updates
- /tmp/customer_cleanup_log.txt for customer cleanup
- /tmp/order_reminders_log.txt for order reminders