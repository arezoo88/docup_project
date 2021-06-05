from celery.utils.time import timezone
from django.db.models import F
from fcm_django.models import FCMDevice
from datetime import timedelta

from authentication.models import User
from neuronio.celery import app
from follow_up.models import Visit, HealthEvent,Notification,ScreeningSteps
from follow_up.periodic_tasks import send_to_events_participates
from follow_up.serializers import VisitSerializer,NotificationSerializer
from follow_up.utils import refund_transaction
from authentication.models import User

@app.task
def send_async_notification(title, body,user_id ,data,time,type):
    print("sending notification...")
    user = User.objects.get(id=user_id)
    notif = Notification(owner=user,type=type,title=title,body=body,data=data,time=time)
    notif.save()
    devices = FCMDevice.objects.filter(user=user_id)
    data['click_action']= "FLUTTER_NOTIFICATION_CLICK"
    data['notif_id']= notif.pk
    devices.send_message(title=title, body=body,data=data,sound=True)


@app.task
def async_auto_reject_visit(visit_id):
    print("auto rejecting task...")

    visit = Visit.objects.filter(id=visit_id).first()
    if not visit or not visit.panel or not visit.enabled:return
    if not visit.status==0:return

    refund_transaction(visit,False)
    if not visit.panel.enabled:
        if Visit.objects.filter(panel=visit.panel,enabled=True,status=0).count()<=1:
            visit.panel.delete()
    else:
        visit.panel.status = 7
        visit.panel.save(update_fields=['status', ])
    visit.status = 2
    visit.enabled = False
    visit.save(update_fields=['status', 'enabled'],)

@app.task
def async_auto_recall_doctor_to_answer(visit_id):
    print("auto recall task...")

    visit = Visit.objects.filter(id=visit_id).first()
    if not visit or not visit.panel or not visit.enabled:return
    if not visit.status==0:return
    serializer=VisitSerializer(visit)
    devices = FCMDevice.objects.filter(user=visit.doctor.user)
    title = "یادآوری درخواست ویزیت"
    data = {"type": 7, "payload": serializer.data, "click_action": "FLUTTER_NOTIFICATION_CLICK"}
    body_info = f' نام بیمار:{visit.patient.user.first_name} {visit.patient.user.last_name}\n  یادآوری درخواست ویزیت ۱۵ دقیقه قبل از شروع ویزیت '
    user = User.objects.get(id=visit.doctor.user.id)
    notif = Notification(owner=user,type=7,title=title,body=body_info,data=data,time=visit.request_visit_time - timedelta(minutes=15))
    notif.save()
    data['notif_id']= notif.pk
    devices.send_message(title=title,body=body_info, data=data,sound=True)
@app.task
def async_auto_recall_visit(visit_id):
    print("auto recall accepted visit task...")

    visit = Visit.objects.filter(id=visit_id).first()
    if not visit or not visit.panel or not visit.enabled:return
    if not visit.status==1:return
    serializer=VisitSerializer(visit)
    title = "یادآوری ویزیت"
    data = {"type": 8, "payload": serializer.data,"click_action":"FLUTTER_NOTIFICATION_CLICK"}
    body_info = f' نام بیمار:{visit.patient.user.first_name} {visit.patient.user.last_name}\n  یادآوری ویزیت ۵ دقیقه قبل از شروع ویزیت '
    user = User.objects.get(id=visit.doctor.user.id)
    notif = Notification(owner=user,type=8,title=title,body=body_info,data=data,time=visit.request_visit_time-timedelta(minutes=5))
    notif.save()
    devices = FCMDevice.objects.filter(user=visit.doctor.user)
    data['notif_id']= notif.pk
    devices.send_message(title=title,body=body_info, data=data,sound=True)
    body_info = f' نام دکتر:{visit.doctor.user.first_name} {visit.doctor.user.last_name}\n  یادآوری ویزیت ۵ دقیقه قبل از شروع ویزیت '
    user = User.objects.get(id=visit.patient.user.id)
    notif = Notification(owner=user,type=8,title=title,body=body_info,data=data,time=visit.request_visit_time-timedelta(minutes=5))
    notif.save()
    data['notif_id'] = notif.pk
    devices = FCMDevice.objects.filter(user=visit.patient.user)
    devices.send_message(title=title,body=body_info, data=data,sound=True)

@app.task
def auto_disable_screening(screening_step_id):
    ScreeningSteps.objects.filter(pk=screening_step_id).update(visit_status=True)



@app.task
def async_auto_recall_participates(event_id):
    print("auto recall event task...")

    event = HealthEvent.objects.filter(id=event_id).first()
    if not event  or not event.enabled:return
    devices = FCMDevice.objects.all()
    send_to_events_participates(event,devices)

