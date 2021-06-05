from kavenegar import KavenegarAPI

from neuronio.celery import app
from utils.utils import generate_digit_code


@app.task
def send_verification_code(phone, verify_code):
    """kavenegar api for sending sms"""
    api = KavenegarAPI('56355033794F535168374F527A726C754D6F59414F6541546C71574C706E48596D333536475959544D4E413D')
    # api.host="79.175.172.10"
    # for OTP account
    params = {'receptor': phone,
              'token': '%d' % verify_code,
              'type': 'sms', 'template': 'verify'}
    api.verify_lookup(params)
