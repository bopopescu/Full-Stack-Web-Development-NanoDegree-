from twilio import TwilioRestException
from twilio.rest import TwilioRestClient

account_sid = "AC3177cbab740d164b9389f6ba63cd8eeb" # Your Account SID from www.twilio.com/console
auth_token  = "958e9149800eb08e464c4020c2631e0e"  # Your Auth Token from www.twilio.com/console

client = TwilioRestClient(account_sid, auth_token)

try:
    message = client.messages.create(body="Privet",
        to="+16477723686",    # Replace with your phone number
        from_="+16474926688") # Replace with your Twilio number
except TwilioRestException as e:
    print(e)

