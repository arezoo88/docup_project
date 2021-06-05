# ارور های مربوط به ورودی از شماره ۱۰۰شروع میشه
errors = {
    100: '[user_name] field is required.',
    101: '[user_type] field is required.',
    102: '[user_name] must be mobile number.',
    103: '[user_type] must be integer number.',
    104: '[user_type] must be in [0,1,2].',
    105: 'you do not have access for create doctor account.',
    604: 'you are not patient',
    612: 'you are not doctor',
    613: '[test_id] and [patient_id] can not be null',
    615: 'please select correct [user_type] that was selected previous.',  # قبلا با تایپ دیگری ثبت نام کرده اید.
    616: '[patient_id] and [cognitive_test_id] and [questions] can not be null',
    617: '[patient_id] is not correct',
    618: '[test_id] is not correct',
    619: 'you do not have access to see test of panel',
    620: '[panel_id] is not correct',
    621: 'you do not have access to upload file',
    622: 'panel_cognitive_test_id is necessary',
    623: 'code is necessary',
    624: 'your credit is not enough.',
    625: 'you have active screening_plan.',
    626: 'Request a visit six hours in advance',

}
# {'detail':"invalid doctor","error_code":603}
#
# {'detail':"u are not patient","error_code":604}
#
# {'detail':"u are not staff","error_code":605}
#
# {'detail':"not related panel","error_code":606}
#
# {'detail':"not related event","error_code":607}
#
# {'detail':"patient can not create a drug with the name of the doctor","error_code":608}
#
# {'detail': "mention the patient", "error_code": 609}
#
# {'detail': "not related visit", "error_code": 610}
#
# {'detail': "patient can response  visit", "error_code": 611}
#
#
# {'detail': 'u are not doctor', "error_code": 612}
#
# {'detail': '[test_id] and [patient_id] can not be null', "error_code": 613}
#
# {'user_type': '[user_type] field is required;',"status":614}
#
# {'detail': 'please select correct user_type that was selected previous.', "error_code": 615}
#
#
# {'user_name': '[user_name] field is required;',"status":616}
# {'user_name': '[user_name] must be mobile number;', "status": 617}
# {'user_type': '[user_type] must be integer number;', "status": 618}
# {'user_type': '[user_type] must be in [0,1,2];', "status": 619}
