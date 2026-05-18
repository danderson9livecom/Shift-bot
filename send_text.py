import os
from pathlib import Path
from twilio.rest import Client
from dotenv import load_dotenv

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path)

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
your_number = os.getenv("YOUR_PHONE_NUMBER")

MESSAGING_SERVICE_SID = "MG2305b944a2cf5945c2017991299a05d3"

def send_text(body):
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=body,
        messaging_service_sid=MESSAGING_SERVICE_SID,
        to=your_number
    )

    print("Message sent:", message.sid)
    return message.sid
