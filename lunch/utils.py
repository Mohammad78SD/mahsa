from django.conf import settings
from ippanel import Client, Error, HTTPError, ResponseCode

def send_otp(phone_number, otp):
    
    client = Client("***REMOVED***")
    ptrn = {
        'code': otp
        }

    client.send_pattern('zz9qp2vzfbtairt', "***REMOVED***", str(phone_number), ptrn)
        
    return True

def send_sms(phone_number, ptrn):
    client = Client("***REMOVED***")
    for num in phone_number:
        client.send_pattern('bxzxz3df41xdvfm', "***REMOVED***", str(num), ptrn)