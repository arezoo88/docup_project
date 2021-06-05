import requests


def login(username, password):
    url = "https://clinic.synappsgroup.com/core/api/v1/user/auth/login"

    payload = f'{"username": {username},"password": {password}}'
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def refresh_token():
    url = "https://clinic.synappsgroup.com/core/api/v1/user/auth/refresh"
    tk = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY0Mzc1MDA2NSwianRpIjoiZTM1NmNlMzNmZDAzNDQ3OWE2YTQyMDVmM2I3NzQ1ZmIiLCJ1aWQiOjE3fQ.Vr98KmFr7V6nXsy9aBOYTB2Eq_UTFHQI5K5liGa450A"

    payload = '{\"refresh\":\"' + tk + '\"}'
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=str(payload))
    return response.text


def save_patient_info_in_synapps(info):
    try:
        gender = {
            0:"M",
            1:"F",
        }
        url = "https://clinic.synappsgroup.com/core/api/v1/patient"
        first_name = info['first_name']
        last_name = info['last_name']
        # father_name = info['father_name']
        gender = gender[info['gender']]
        # dob = info['dob']
        # nationality = info['nationality']
        # birth_location = 742
        national_id = info['national_id']
        # marital_status = info['marital_status']
        # note = info['note']
        # street = info['street']
        # city = 742
        phone_number_1 = info['username']
        payload = '{\n  \"namespace\": 1,\n  \"first_name\": \"' + first_name + '\",\n  \"last_name\": \"' + last_name + '\",\n  \"gender\": \"' + gender + '\",\n  \"has_national_id\": true,\n  \"phone_number_1\": \"' + phone_number_1 + '\",\n  \"national_id\": \"' + national_id + '\"}'
        token = "Bearer " + str(eval(refresh_token())['access'])
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))

        return response.text
    except:
        import traceback
        print(traceback.format_exc())
