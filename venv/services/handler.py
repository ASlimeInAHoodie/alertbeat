"""
    ___ HANDLER ___
    After creating an integration or service, return to here for adding it to ALERTBEAT
    Once you save this file, the main script will automatically update the imported handler to match the saved file.
    Warning: This is checked when sleep finishes. If you save this file before it's working the service will break!
    [version] 1.0.0 (If you don't know what to change to update the script, update this version)

    __ ALERT RETURN/ARGUMENT DICTIONARY __
    An alert is a dictionary, which *must* have the following values
     - "title": The title of the alert
     - "description": The contents of the alert
     - "severity": The severity of the alert, ranging from 0 DEBUG, 1 INFO, 2 LOW, 3 MEDIUM, 4 HIGH, 5 CRITICAL, 6 ERROR
     - "timestamp": The datetime object of datetime.now(timezone.utc)
    The alert dictionary can also have the following, optional values
     - "json": JSON data

    __ SERVICES __
    When creating an integration, it *must* have the following:
     - Have a class object that can be initialised in this file's `init(self)`
     - The class object has a send_message(self, dict) function that:
        - Handles a dictionary 
     - The class object has a send_message(self, dict) function that returns a Response for OK or a string for an error

    __ INTEGRATIONS __
    When creating an integration, it *must* do the following:
     - Have a class object that can be initialised in this file's `init(self)`
     - The class object has a query() function that either returns None for no alerts, a list of alerts for OK, or an error
"""
#region DONT EDIT THIS
# We can make updates via importlib
import importlib

services = [] # DONT EDIT
integrations = [] # DONT EDIT

from requests import Response
def send_messages(message: dict):
    for service in services:
        response: Exception|Response|None = service.send_message(message)
        if type(response) is Exception: raise Exception(response)
        elif response == None: logger(f"Severity too low for service. Skipping", 0)
        else: logger(f"Request successfully sent to {response.url}", 0)
#endregion

#region EDIT THIS
"""In this region, configure anything you would like"""
# import your services here
from . import discord
# import your integrations here
from .integrations import nginx
from .integrations import sshd_session

def update_config(initial: bool = False):
    global services # DO NOT EDIT
    global integrations # DO NOT EDIT
    # update your services here
    importlib.reload(discord)
    
    # Append an initialised object of each service to use here:
    services = [
        discord.Discord_Webhook()
    ]

    # reload your integration classes here: 
    importlib.reload(nginx)
    importlib.reload(sshd_session)

    # Append an initialised object of each integration to use here:
    integrations = [
        nginx.Nginx_Url_Count(),
        sshd_session.SSH_Failure_Count()
    ]

    # Dont say config has been reloaded if initial update
    if initial: return
    message = {
    'title': 'Handler Updated',
    'description': 'ALERTBEAT has been updated to the latest config.',
    'severity': 1,
    'timestamp': datetime.now(timezone.utc)
    }
    send_messages(message)
#endregion

#region DONT EDIT THIS
# PUBLIC IMPORTS
from datetime import datetime, timezone
import traceback
# LOCAL IMPORTS
from .utilities.logger import logger

def init():
    # Update config initially
    update_config(initial=True)
    # SERVICE TEST
    message = {
        'title': 'Handler Initialised',
        'description': 'ALERTBEAT has been initialised.',
        'severity': 1,
        'timestamp': datetime.now(timezone.utc)
    }
    send_messages(message)

def run():
    alerts = []
    # Get all alerts from integrations
    for integration in integrations:
        try:
            # Get alert dictionary, or raise an error if integration fails
            additional_alerts: Exception|list[dict]|None = integration.query()
            if additional_alerts == None: continue
            elif isinstance(additional_alerts, BaseException): raise additional_alerts
            # Add alert to list for sending
            else: alerts += additional_alerts
        except Exception as e:
            logger(f"Integration query failed: {e}", 1)
            logger("Full trace: {}".format(traceback.format_exc()), 1)
    # Send out alerts to services
    for alert in alerts:
        try: send_messages(alert)
        except Exception as e:
            logger(f"Service Send Message failed: {e}", 1)
            logger("Full trace: {}".format(traceback.format_exc()), 1)
#endregion