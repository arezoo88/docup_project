from rest_framework_jwt.utils import jwt_payload_handler
def jwt_custom_payload_handler(user):
    payload = jwt_payload_handler(user)
    payload['type'] = user.type
    return payload
