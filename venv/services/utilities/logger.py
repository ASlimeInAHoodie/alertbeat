from datetime import datetime, timezone
import os

def logger(message: str, level: int = 0):
  severity = "INFO"
  if level > 0:
    severity = "ERROR"
    print('{0} {1} {2}\n'.format(datetime.now(timezone.utc).strftime('%Y/%m/%d %H:%M:%S %Z'), severity, message))

  with open('./alertbeat.log', 'a') as file:
    file.write('{timestamp} {hostname} {app_name}[{pid}]: {sevmessage}\n'.format(
      timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
      hostname=os.uname().nodename,
      app_name="Python",
      pid=str(os.getpid()),
      sevmessage="[{severity}] {message}".format(
        severity=severity,
        message=message.replace('\n', '; ')
      )
    ))