from datetime import timedelta, datetime
from django.db.models import Q, F
# from django.utils.datetime_safe import datetime
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from django.db import models
from rest_framework.utils import representation

from authentication.models import Patient, Doctor, User,VisitType
from follow_up.models import HealthEvent, Drug, Panel, Visit

# here I provided some useful utils to avoid duplicates
from utils.models import ImageList
import logging
log = logging.getLogger(__name__)

def get_relevant_health_events_queryset(user):
    if user.type == 0:
        events = HealthEvent.objects.filter(
            Q(owner=user) | Q(invited_patients=get_object_or_404(Patient, user=user))).order_by('-time')
    else:
        events = HealthEvent.objects.filter(
            Q(owner=user) | Q(invited_doctors=get_object_or_404(Doctor, user=user))).order_by('-time')
    return events


def get_relevant_visit_queryset(user):
    if user.type == 0:
        return Visit.objects.filter(patient__user=user).order_by('-request_visit_time')
    else:
        return Visit.objects.filter(doctor__user=user).order_by('-request_visit_time')


def get_relevant_visit_queryset_pending(user, visit_type,query, status=0):
    if visit_type == None:
        visit_type = [0, 1]
    if status == None:
        status = [0, 1, 2]

    if user.type == 0:
        docs = Visit.objects.filter(patient__user=user, enabled=True, status__in=status,
                                    visit_type__in=visit_type,request_visit_time__gte=timezone.now()).order_by(
            '-request_visit_time')
    else:
        docs = Visit.objects.filter(doctor__user=user, enabled=True, status__in=status,
                                    visit_type__in=visit_type,request_visit_time__gte=timezone.now()).order_by(
            '-request_visit_time')
    # if status == '0' :
    #
    #     docs = docs.filter(request_visit_time__gte=timezone.now())
    if query:
        docs = docs.filter(
            Q(patient__user__first_name__contains=query) | Q(patient__user__last_name__contains=query))
    return docs


def get_patient_drugs(user):
    return Drug.objects.filter(patient__user=user).order_by('-consuming_day')


def search_my_relevant_patient_panels(user, query=None, from_date=None, to_date=None, status=None):
    panels = Panel.objects.filter(doctor__user=user)
    if query:
        panels = panels.filter(Q(patient__user__first_name__contains=query) |
                               Q(patient__user__last_name__contains=query))
    if from_date:
        panels = panels.filter(Q(modified_date__gt=from_date))
    if to_date:
        panels = panels.filter(Q(modified_date__lte=to_date))
    if status:
        panels = panels.filter(Q(status__in=status))
    return panels.order_by("-modified_date")


def get_my_partner_panel(user, contact_id):
    if user.type == 0:  # use is patient
        return get_object_or_404(Panel.objects.all(), doctor__pk=contact_id, patient__user=user)
    else:  # user is doctor
        return get_object_or_404(Panel.objects.all(), patient__pk=contact_id, doctor__user=user)

def see_panel_status(instance,visit_type):

    query = Visit.objects.filter(panel=instance, enabled=True, status=1, visit_type=visit_type).filter(
        request_visit_time__lte=timezone.now(),
        request_visit_time__gte=(timezone.now() - timedelta(
            minutes=1) * ((1 + F("visit_duration_plan")) * 15)))

    if query.count():
        instance.status = query.order_by("request_visit_time").first().visit_type + 4
        # print(query.order_by("request_visit_time").first().visit_type)
        instance.save(update_fields=['status', ])
        return True
    last_modified_visit = Visit.objects.filter(panel=instance, enabled=True, visit_type=visit_type, status=1,
                                               request_visit_time__gte=timezone.now(), ).order_by(
        'request_visit_time').first()

    if last_modified_visit:
        instance.status = last_modified_visit.visit_type + 2
        instance.save(update_fields=['status', ])
        return True

    last_modified_visit = Visit.objects.filter(panel=instance, enabled=True, visit_type=visit_type,status=0,
                                               request_visit_time__gte=timezone.now(), ).order_by(
        'request_visit_time').first()
    if last_modified_visit:
        instance.status = last_modified_visit.visit_type
        instance.save(update_fields=['status', ])
        return True

    return False
def update_panel_status(instance):
    if see_panel_status(instance,1):return
    elif see_panel_status(instance,0):return
    else:
        instance.status = 6
        instance.save(update_fields=['status', ])


def check_transaction_possibility(visit, patient_user, doctor,visit_type, perform=False, target="patient"):
    doctor_support = doctor.plan
    plan = VisitType.objects.filter(Doctor_supports=doctor_support.id,visit_type=visit_type)[0]
    base_price = 0
    if visit.validated_data["visit_type"] == 1:
        print("visit_type")
        if visit.validated_data["visit_method"] == 0:
            base_price = plan.base_text_price
        elif visit.validated_data["visit_method"] == 1:
            base_price = plan.base_voice_price
        else:
            base_price = plan.base_video_price

    else:
        base_price = plan.base_physical_visit_price

    final_price = base_price * (visit.validated_data["visit_duration_plan"] + 1)
    if patient_user.credit >= final_price:
        if perform:
            print(final_price)
            log.debug("visit request; visit price: " + str(final_price))
            if target == "patient":
                log.debug("visit request;credit of patient user(before): "+str(patient_user.username)+" is: "+str(patient_user.credit))
                patient_user.credit -= final_price
                patient_user.save(update_fields=["credit", ])
                # User.objects.filter(id=patient_user.id).update(credit=F('credit') - final_price)
                log.debug("visit request;credit of patient user(after): "+str(patient_user.username)+" is: "+str(patient_user.credit))
            elif target == "doctor":
                log.debug("visit request;credit of doctor user(before): "+str(doctor.user.username)+" is: "+str(doctor.user.credit))
                doctor.user.credit += final_price
                doctor.user.save(update_fields=["credit", ])
                # User.objects.filter(id=doctor.user.id).update(credit=F('credit') + final_price)
                log.debug("visit request;credit of doctor user(after): "+str(doctor.user.username)+" is: "+str(doctor.user.credit))

        return True
    else:
        return False

def check_transaction_possibility_plan(plan,patient_user,doctor, perform=False):
    plan_price =plan.validated_data["plan"].price
    if patient_user.credit >= plan_price:
        if perform:
            log.debug("visit plan request; plan price: " + str(plan_price))
            log.debug("visit plan request;credit of patient user(before): "+str(patient_user.username)+" is: "+str(patient_user.credit))
            patient_user.credit -= plan_price
            patient_user.save(update_fields=["credit", ])
            # User.objects.filter(id=patient_user.id).update(credit=F('credit') - final_price)
            log.debug("visit plan request;credit of patient user(after): "+str(patient_user.username)+" is: "+str(patient_user.credit))
            log.debug("visit request;credit of doctor user(before): "+str(doctor.user.username)+" is: "+str(doctor.user.credit))
            doctor.user.credit += plan_price
            doctor.user.save(update_fields=["credit", ])
            # User.objects.filter(id=doctor.user.id).update(credit=F('credit') + final_price)
            log.debug("visit plan request;credit of doctor user(after): "+str(doctor.user.username)+" is: "+str(doctor.user.credit))

        return True
    else:
        return False


def charge_doctor(visit, patient_user, doctor,visit_type ):
    doctor_support = doctor.plan
    plan = VisitType.objects.filter(Doctor_supports=doctor_support.id,visit_type=visit_type)[0]
    base_price = 0
    if visit.visit_type == 1:
        if visit.visit_method == 0:
            base_price = plan.base_text_price
        elif visit.visit_method == 1:
            base_price = plan.base_voice_price
        else:
            base_price = plan.base_video_price
    else:
        base_price = plan.base_physical_visit_price

    final_price = base_price * (visit.visit_duration_plan + 1)
    log.debug("accepted visit; visit price: " + str(final_price))
    # if patient_user.credit >= final_price:
    log.debug("accepted visit;credit of doctor user(before): " + str(doctor.user.username) + " is: " + str(
        doctor.user.credit))
    doctor.user.credit += final_price
    doctor.user.save(update_fields=["credit", ])
    # User.objects.filter(id=doctor.user.id).update(credit=F('credit') + final_price)
    log.debug(
        "accepted visit;credit of doctor user(after): " + str(doctor.user.username) + " is: " + str(doctor.user.credit))

    return True


def refund_transaction(visit, accepted_before):
    doctor_support = visit.doctor.plan
    plan = VisitType.objects.filter(Doctor_supports=doctor_support.id,visit_type=visit.visit_type)[0]
    base_price = None
    patient_user = visit.patient.user

    if visit.visit_type == 1:
        if visit.visit_method == 0:
            base_price = plan.base_text_price
        elif visit.visit_method == 1:
            base_price = plan.base_voice_price
        else:
            base_price = plan.base_video_price
    else:
        base_price = plan.base_physical_visit_price

    final_price = base_price * (visit.visit_duration_plan + 1)
    log.debug("refund_transaction; visit price: " + str(final_price))
    log.debug(
        "refund_transaction;credit of patient user(before): " + str(patient_user.username) + " is: " + str(patient_user.credit))

    patient_user.credit += final_price
    patient_user.save(update_fields=["credit", ])
    # User.objects.filter(id=patient_user.id).update(credit=F('credit') + final_price)
    log.debug(
        "refund_transaction;credit of patient user(after): " + str(patient_user.username) + " is: " + str(patient_user.credit))

    if accepted_before and visit.doctor.user.credit >= final_price:
        log.debug("refund_transaction;credit of doctor user(before): " + str(visit.doctor.user.username) + " is: " + str(
            visit.doctor.user.credit))
        visit.doctor.user.credit -= final_price
        visit.doctor.user.save(update_fields=["credit", ])
        # User.objects.filter(id=visit.doctor.user.id).update(credit=F('credit') - final_price)
        log.debug("refund_transaction;credit of doctor user(after): " + str(visit.doctor.user.username) + " is: " + str(
            visit.doctor.user.credit))


def change_panel_representation(instance, representation):
    update_panel_status(instance)
    representation['status'] = instance.status
    old = representation['panel_image_sets']
    representation['panel_image_sets'] = {image_list["title"]: image_list["files"] for image_list in old}
    representation['panel_image_list_name_id'] = {image_list["title"]: image_list["id"] for image_list in old}

    return representation


def change_drug_representation(drug, represent):
    if not drug.usage_period: return represent
    use = 0
    while True:
        date_time = datetime.combine(drug.consuming_day, drug.consuming_time) + use * timedelta(
            hours=drug.usage_period)
        if timezone.make_aware(date_time) > timezone.now():
            break

        if use > 50: break
        use += 1

    represent['consuming_day'] = date_time.date()
    represent['consuming_time'] = date_time.time()
    return represent


def check_interference(doctor, request_visit_time, visit_duration_plan):
    start_time = request_visit_time
    end_time = request_visit_time + timedelta(minutes=((1 + visit_duration_plan) * 15))

    count = Visit.objects.filter(doctor=doctor, enabled=True).filter(
        Q(request_visit_time__lt=end_time)&
        Q(request_visit_time__gt=(start_time - timedelta(
            minutes=1) * ((1 + F("visit_duration_plan")) * 15)))).count()

    print("*******")
    if count > 0:
        return False

    return True
