from twilio.rest import Client
import config

client = Client(config.TWILIO_ID, config.TWILIO_ACCOUNT_TOKEN)

def send_sms_twilio(body, to):
    message = client.messages.create(
            body=body,
            from_='+%s' % config.PHONE_NUMBER,
            to=('+1%s' if len(to) <= 10 else '+%s') % to
        )
    print('Sent message to %s' % to)

