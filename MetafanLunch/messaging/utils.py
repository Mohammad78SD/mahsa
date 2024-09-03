from pywebpush import webpush, WebPushException
from django.conf import settings

def send_web_push(subscription_info, message_body):
    print(f"Sending web push with message: {message_body}")
    vapid_private_key = settings.VAPID_PRIVATE_KEY
    if isinstance(vapid_private_key, (list, tuple)):
        vapid_private_key = vapid_private_key[0]
    try:
        response = webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"}
        )
        print(f"Web push response: {response.status_code}")
        return response
    except WebPushException as ex:
        print("Web Push failed", repr(ex))
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                  extra.get('code', 'Unknown'),
                  extra.get('errno', 'Unknown'),
                  extra.get('message', 'Unknown')
                 )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise