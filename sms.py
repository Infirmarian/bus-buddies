import boto3

# Create an SNS client
client = boto3.client(
    "sns",
    region_name="us-west-2"
)

def send_sms(number, message):
    client.publish(
        PhoneNumber="1"+number,
        Message=message
    )
    print("Sent a message to {}".format(number))
