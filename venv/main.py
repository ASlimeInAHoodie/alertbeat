#region PUBLIC IMPORTS
from datetime import datetime, timedelta, timezone
import os, time, requests, json, importlib
from hashlib import md5
#endregion

#region LOCAL IMPORTS
import services.handler as handler
import services.utilities.GLOBAL as GLOBAL
#endregion

HANDLERPATH = './services/handler.py'

if __name__ == "__main__":
  # Used for updating the handler
  current_version = md5(open(HANDLERPATH,'rb').read()).hexdigest()

  handler.init()

  while True:
    handler.run()
    time.sleep(GLOBAL.SLEEPTIME)
    check_version = md5(open(HANDLERPATH,'rb').read()).hexdigest()
    if current_version != check_version:
      current_version = check_version
      importlib.reload(handler)
      handler.update_config()
