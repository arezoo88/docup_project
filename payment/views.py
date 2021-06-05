from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from authentication.models import User, Doctor, Patient
from neuronio.settings import TRANSACTION_API_CODE
from payment.models import Transaction
from payment.serializers import TransactionSerializer
from follow_up.serializers import ScreeningStepsSerializer
from follow_up.models import Panel, Screening
from synapps.views import save_patient_info_in_synapps
import requests
import logging
import base64
from webpay import WebpayAPI, exceptions
from utils.models import Voucher

webpay = WebpayAPI(TRANSACTION_API_CODE)
from datetime import datetime

log = logging.getLogger(__name__)
docup_app_url = "docup://com.nilva.docup"


@api_view(['GET'])
def transaction_call_back(request, *args, **kwargs):
    try:
        print('---------------------------------------')
        state = request.query_params.get('state')
        if not state: raise NotFound(detail="[state] can not be null ", code=500)
        if state == 'wait_for_confirm':
            reference = request.query_params.get('reference')
            id_ = kwargs.get('id')

            # id_ = "eyJhbW91bnQiOjEwMDAwMCwidHlwZSI6MSwibW9iaWxlIjoiMDkyMTI2NDY5MzgiLCJzY3JlZW5pbmdfaWQiOjF9"
            # false = "false"
            # true = "true"
            null = None
            decoded_id = eval(base64.b64decode(id_).decode())
            amount = decoded_id['amount']
            type = decoded_id['type']
            mobile = decoded_id['mobile']
            percent = 0
            get_obj = None
            get_percent = []
            if 'code' in decoded_id:
                discount_code = decoded_id['code']
                get_percent = Voucher.objects.filter(code=discount_code, enabled=True)

            if len(get_percent) != 0:
                get_obj = get_percent[0]
                percent = get_obj.discount / 100

            amount = int(amount)
            # amount = int(amount) - int(amount * percent)
            # print(amount)
            payment_data = webpay.verify(
                reference=reference,
                amount_irr=amount
            )
            # payment_data = {
            #   "ok": True,
            #   "result": {
            #     "state": "paid",
            #     "total": 1000000,
            #     "wage": 5000,
            #     "gateway": "sep",
            #     "terminal": "11223344",
            #     "pay_ref": "GmshtyjwKSu5lKOLquYrzO9BqjUMb/TPUK0qak/iVs",
            #     "pay_trace": "935041",
            #     "pay_pan": "123456******1234",
            #     "pay_cid": "77CB1B455FB5F60415A7A02E4502134CFD72DBF6D1EC8FA2B48467DFB124AA75A",
            #     "pay_time": "2019-11-12T16:39:57.686436+03:30"
            #   }
            # }
            # payment_data=payment_data['result']
            if payment_data.get('state') == 'paid':
                clinic_credit = get_object_or_404(User, username='Neuronio')
                clinic_credit.credit = clinic_credit.credit+amount
                clinic_credit.save()

                user = get_object_or_404(User, phone_number=mobile)
                if type == 1:

                    if len(get_percent) != 0:
                        get_obj.expire_date = datetime.now()
                        get_obj.enabled = False
                        get_obj.save()
                    transactions_type = 1
                    screening_id = decoded_id['screening_id']
                    screening = get_object_or_404(Screening, pk=screening_id)
                    tests = screening.medical_tests.all().values('id')
                    dict_tests = {}
                    for test in tests:
                        value = test['id']
                        dict_tests[value] = False

                    random_doctor = get_object_or_404(Doctor.objects.filter(enabled=True, clinic_id=4).order_by('?')[:1])
                    # patient = Patient.objects.filter(user=user)
                    patient = get_object_or_404(Patient, user=user)
                    # created_panel = Panel.objects.create(patient=patient, doctor=random_doctor)
                    panel, created = Panel.objects.get_or_create(patient=patient, doctor=random_doctor)

                    serializer = ScreeningStepsSerializer(data={'payment_status': True})
                    serializer.is_valid(raise_exception=True)
                    serializer.save(panel=panel, screening=screening, tests_response_status=dict_tests, discount=get_obj)
                    synapps_info = {'first_name': user.first_name, 'last_name': user.last_name,
                                    # 'birth_location':patient.birth_location,
                                    'username': user.username,
                                    'gender': patient.gender,
                                    'national_id': user.national_id,
                                    # 'city':patient.city

                                    }
                    save_patient_info_in_synapps(synapps_info)

                serializer = TransactionSerializer(data=payment_data)
                serializer.is_valid(raise_exception=True)
                toman_amount = (serializer.validated_data.get('total') / 10)
                log.debug("payment; user:" + str(user.username) + " charge amount: " + str(toman_amount))
                log.debug("payment; credit of user(before): " + str(user.username) + " is: " + str(
                    user.credit))
                if type != 1:
                    transactions_type = 0
                    user.credit += toman_amount
                    user.save(update_fields=["credit", ])
                    log.debug("payment; credit of user(after): " + str(user.username) + " is: " + str(
                        user.credit))
                serializer.save(user=user, total_credit=user.credit, total=toman_amount, transactions_type=transactions_type, discount=percent)
            else:
                return render(request, "payment/payment_result.html", {
                    "result": "پرداخت ناموفق",
                    "app_url": docup_app_url + '?success=false',
                })

            return render(request, "payment/payment_result.html", {"result": "پرداخت موفق",
                                                                   "app_url": docup_app_url + "?success=true&credit=" + str(
                                                                       str(user.credit)), })
        else:
            return render(request, "payment/payment_result.html",
                          {"result": "پرداخت ناموفق", "app_url": docup_app_url + '?success=false', })

    except:
        import traceback
        print(111111, traceback.format_exc())
