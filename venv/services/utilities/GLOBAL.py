from dotenv import load_dotenv
import json, os

load_dotenv()
HOSTNAME = os.getenv('HOSTNAME')
HOSTURL = os.getenv('HOST_URL')
SLEEPTIME = int(os.getenv('SLEEP_TIME'))
SIZEDATAFILENAME = os.getenv('SIZE_DATA_FILENAME')
CONFIGNAME = os.getenv('CONFIG_FILENAME')
WEBHOOKS = json.loads(os.getenv('WEBHOOKS'))