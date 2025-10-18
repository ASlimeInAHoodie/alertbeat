# ALERTBEAT
ALERTBEAT's purpose is to read log files at regular interval, read new logs, filter them, then send out alerts. However, this can also be used to run other functions on the schedule too (but cron and systemd exist for a reason). Thanks to importlib, the service automatically updates its config after each   if it senses changes in the `handler.py` file, allowing you to add, remove, or update services & integrations without interrupting the main process.

## Installation
The simplest method is to run the bash script, or follow along with it - it's a very simple script:
```bash
curl "https://raw.githubusercontent.com/ASlimeInAHoodie/alertbeat/refs/heads/main/install.sh" -o /tmp/install_alertbeat.sh && sudo /bin/bash /tmp/install_alertbeat.sh
```
## Alert
An alert defined in ALERTBEAT is a dictionary object with the following properties:
 - **title**: The title of the alert
 - **description**: A description of the alert
 - **severity**: An integer between 0 and 6 inclusive, classified by 0=DEBUG, 1=INFO, 2=LOW, 3=MEDIUM, 4=HIGH, 5=CRITICAL, 6=ERROR
 - **timestamp**: A datetime.datetime object marking when the alert was generated
 - **json** (OPTIONAL): a dictionary of other data

## Services
A service defined in ALERTBEAT is a python script located in the root of the `services` folder. A service has the following minimum requirements:
 - A class that is instantiated in the `services` array in `handler.py` when in use.
 - A `send_message(self, message: dict)` function inside this class that returns a requests. Response object if OK, None if no request was sent and no errors want to be raised, or an Exception if an error occurred - optional as the handler has a catch anyway.
An example `discord.py` service is included. This sends a webhook with alert details.

## Integrations
An integration defined in ALERTBEAT is a python script located in `services/integrations` folder. An integration has the following minimum requirements:
 - A class that is instantiated in the `integrations` array in `handler.py` when in use.
 - A `query(self) -> list[dict]|Exception|None` function which returns either a list of alerts to raise, an Exception if an error occurred (not enforced), or None if no alerts were raised.
Example integrations are included:
 - `nginx.py`: Gathers logs from `access.log` and provides a digest of the statistics.
 - `sshd_session.py`: Gathers sshd-session process logs from `auth.log` and provides a digest of the statistics.
