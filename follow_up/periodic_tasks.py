from datetime import timedelta
from django.utils.datetime_safe import datetime
from neuronio.celery import app
from fcm_django.models import FCMDevice
from follow_up.models import HealthEvent, Drug
from django.utils import timezone

notification_types = {"video_call": 1, "health_event": 3, "drug_reminder": 2,'on_call_visit':4,'visit_request':5,'visit_response':6,
                      "recall_pending_visit":7,"recall_accepted_visit":8,'added_health_event':9}
# send events to participates using FCM-django send message function
from follow_up.serializers import HealthEventSerializerWithoutPatientsDocs, DrugSerializer

def update_drug_time(drug):
    if not drug.usage_period: return
    use=0
    while True:
        date_time = datetime.combine(drug.consuming_day, drug.consuming_time) + use * timedelta(
            hours=drug.usage_period)
        if timezone.make_aware(date_time)> timezone.now():
            break

        if use>50:break
        use+=1

    drug.consuming_day =date_time.date()
    drug.consuming_time =date_time.time()
    drug.save(update_fields=['consuming_day','consuming_time' ])


def send_to_events_participates(event, devices):
    targets = [event.owner]
    targets += [e.user for e in event.invited_patients]
    targets += [e.user for e in event.invited_doctors]
    devices = devices.filter(user__in=targets)
    serializer = HealthEventSerializerWithoutPatientsDocs(event)
    devices.send_message(title=event.title,
                         body={"type": notification_types['health_event'], "payload": serializer.data})


# define which event is related to today, so that we send notifications to participates then.
@app.task
def health_event_task():
    print("notify health events...")
    devices = FCMDevice.objects.all()
    # find day relayed events to be notified
    events = HealthEvent.objects.filter(time__date=datetime.today())
    # for each event that is for today we have to send notifications to participating users
    for event in events:
        send_to_events_participates(event, devices)


# every hour this task finds next hour drug should be taken, so that we send notification patient.
@app.task
def drug_reminder():
    print("notify drug...")
    devices = FCMDevice.objects.all()
    enabled_drugs=Drug.objects.filter(enabled=True)
    update_drug_time(enabled_drugs)
    # find day drugs to be notified
    drugs = enabled_drugs.filter(consuming_day=datetime.today(), consuming_time__gte=datetime.now().time(),
                                consuming_time__lt=(datetime.now() + timedelta(hours=1)).time())
    # for each drug we have to send notifications to  patient
    for drug in drugs:
        serializer = DrugSerializer(drug)
        devices.filter(user=drug.patient.user).send_message(title="یاداوری داروی" + drug.drug_name,
                                                            body={"type": notification_types['drug_reminder'],
                                                                  "payload": serializer.data})
