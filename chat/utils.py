from email.mime import multipart
from email.mime import nonmultipart
import email.parser

"""

this funcs are depricated

"""
# this functions let me to encode and decode form-data
class MIMEFormdata(nonmultipart.MIMENonMultipart):
    def __init__(self, keyname, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_header(
            "Content-Disposition", "form-data; name=\"%s\"" % keyname)


def encode_multipart_formdata(fields):
    m = multipart.MIMEMultipart("form-data")

    for field, value in fields.items():
        data = MIMEFormdata(field, "text", "plain")
        data.set_payload(value)
        m.attach(data)

    return m


def load_form_data_from_string(input_data):
    msg = email.parser.Parser().parsestr(input_data)
    return {
        part.get_param('name', header='content-disposition'): part.get_payload(decode=True)
        for part in msg.get_payload()
    }


def load_form_data_from_bytes(input_data):
    msg = email.parser.BytesParser().parsebytes(input_data)
    return {
        part.get_param('name', header='content-disposition'): part.get_payload(decode=True)
        for part in msg.get_payload()
    }


encode_multipart_formdata({"sa": str(4)}).as_string()