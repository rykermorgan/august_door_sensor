#!/usr/bin/python

import sys
from august.api import Api
from august.authenticator import (Authenticator, AuthenticationState, ValidationResult)
import requests
import time
import polling


previousState = 'true'
doorOpen = "LockDoorStatus.OPEN"
doorClosed = "LockDoorStatus.CLOSED"


user_name = '+18018828444'
password = 'Heatho0113'

use_session = True
combine_status = True

api = Api(timeout=20)
authenticator = Authenticator(api, "phone", user_name, password, access_token_cache_file=".august.conf")

authentication = authenticator.authenticate()

# State can be either REQUIRES_VALIDATION, BAD_PASSWORD or AUTHENTICATED
# You'll need to call different methods to finish authentication process,
# see below
state = authentication.state


# If AuthenticationState is BAD_PASSWORD, that means your login_method,
# username and password do not match

if state == AuthenticationState.BAD_PASSWORD:
    print("Invalid password provided")
    sys.exit


# If AuthenticationState is AUTHENTICATED, that means you're authenticated
# already. If you specify "access_token_cache_file", the authentication is
# cached in a file. Everytime you try to authenticate again, it'll read from
# that file and if you're authenticated already, Authenticator won't call
# August again as you have a valid access_token


# If AuthenticationState is REQUIRES_VALIDATION, then you'll need to go through
# verification process send_verification_code() will send a code to either your
# phone or email depending on login_method
if state == AuthenticationState.REQUIRES_VALIDATION:
    authenticator.send_verification_code()

    code = input("Please provide validation code that was send to your phone.")
    while True:

        # Wait for your code and pass it in to validate_verification_code()
        validation_result = authenticator.validate_verification_code(code)
        if validation_result == ValidationResult.VALIDATED:
            break

        code = input("Code provided was incorrect, please re-enter.")


# If ValidationResult is INVALID_VERIFICATION_CODE, then you'll need to either
# enter correct one or resend by calling send_verification_code() again
# If ValidationResult is VALIDATED, then you'll need to call authenticate()
# again to finish authentication process
authentication = authenticator.authenticate()


def augustBackDoor():

    # Get status August DoorSense (contact sensor) status
    # returns enum
    backDoor = api.get_lock_door_status(authentication.access_token,'41C161F1D5DB4C30948CE8184C8438F1')

    # set string boolean for webhook 'state' value
    def backDoorState():
        if str(backDoor) == doorOpen:
            return 'false'
        elif str(backDoor) == doorClosed:
            return 'true'

    # set current state variable for dynamic webhook 'state'
    currentState = backDoorState()

    global previousState

    if previousState != currentState:
        # set webhook url to local ip for local run
        homebridge_hook = 'http://ryker:foetus-buoy-astound-scoop@192.168.86.231:51830'

        d_homebridge = {'accessoryId': 'back-door', 'state': currentState}

        #postToWebhook
        # response = requests.post(url = webhook_url, params = d)
        homebridge_response = requests.post(url = homebridge_hook, params = d_homebridge)

        # console print out for troubleshooting
        # print('homebridge response: ' + str(homebridge_response))
        # print('ifttt response: ' + str(ifttt_response))
        # print('previousState: ' + previousState)
        # print('currentState: ' + currentState)

    previousState = currentState
    # print(currentState)

# polling function to 'listen' or poll for changes on the endpoint
polling.poll(
    lambda: augustBackDoor(),
    step=1,
    poll_forever=True)