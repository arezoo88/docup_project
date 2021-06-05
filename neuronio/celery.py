from __future__ import absolute_import
import os
from celery import Celery, shared_task
from celery.schedules import crontab
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuronio.settings')
app = Celery('neuronio')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# add periodic task to send event health every day
app.conf.beat_schedule = {
    'send-health-events-every-day': {
        'task': 'follow_up.periodic_tasks.health_event_task',
        'schedule': crontab(hour=5, minute=0),
    },
    'send-drug_reminder-every-day': {
            'task': 'follow_up.periodic_tasks.drug_reminder',
            'schedule': crontab(hour="*", minute=1)
        },
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
