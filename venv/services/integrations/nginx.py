from collections import defaultdict
from datetime import datetime, timezone
import os, json

#region CONSTANTS
LOG_FILE_PATH = '/var/log/nginx/access.log'
DATA_STORAGE_PATH = './integration_data.json'

TITLE = "Your Daily Digest - Nginx"

DTFORMAT = "%d/%b/%Y:%H:%M:%S %z"

# Deprecated title
# days = SLEEPTIME // 86400
# hours = (SLEEPTIME % 86400) // 3600
# minutes = (SLEEPTIME % 3600) // 60

# title_middle = ""
# if days > 1: title_middle += f"{days} Day"
# elif days == 1: title_middle += "Daily"
# elif hours > 1: title_middle += f"{hours} Hour"
# elif hours == 1: title_middle += "Hourly"
# else: title_middle += f"{minutes} Minute"

# TITLE = f"Your {title_middle} Digest"
#endregion

def getFileSize() -> int:
    """Return size of file whilst saving to file too"""
    size = os.path.getsize(LOG_FILE_PATH)
    # Save to file
    try:
        with open(DATA_STORAGE_PATH, 'r') as file:
            data = json.load(file)
    except: data = {}
    data[LOG_FILE_PATH] = size
    with open(DATA_STORAGE_PATH, 'w') as file:
        json.dump(data, file)
    return size

def readSize() -> int:
    try:
        with open(DATA_STORAGE_PATH, 'r') as file:
            data = json.load(file)
            if LOG_FILE_PATH not in data.keys(): return getFileSize()
            return data[LOG_FILE_PATH]
    except: return 0

class Log:
    def __init__(self,
        ip: str,
        status_code: int,
        content_length: int,
        date: datetime,
        method: str,
        url: str,
        protocol: str,
        user_agent: str
    ):
        self.ip: str = ip
        self.status_code: int = status_code
        self.content_length: int = content_length
        self.date: datetime = date
        self.method: str = method
        self.url: str = url
        self.protocol: str = protocol
        self.user_agent: str = user_agent

class Nginx_Url_Count:
    def __init__(self):
        self.size = readSize()

    def query(self) -> list[dict]|Exception|None:
        try:
            size = getFileSize()
            if size < self.size: size = 0
            if self.size == size: return None
            # Else ... Return data
        except Exception as e:
            print(f"size: {e}")
            return e

        logs = []
        with open(LOG_FILE_PATH, 'r') as file:
            file.seek(self.size)
            for line in file:
                split_by_quotes = line.split('"')
                if len(split_by_quotes) < 2: continue
                request_split_by_spaces = split_by_quotes[1].split()
                if len(request_split_by_spaces) < 3: continue
                if request_split_by_spaces[0] not in ["GET", "POST"]: continue
                split_by_spaces = line.split()
                datetime_string = line.split('[')[1].split(']')[0]
                logs.append(Log(
                    ip=split_by_spaces[0],
                    status_code=split_by_spaces[8],
                    content_length=split_by_spaces[9],
                    date=datetime.strptime(datetime_string, DTFORMAT),
                    method=request_split_by_spaces[0],
                    url=request_split_by_spaces[1],
                    protocol=request_split_by_spaces[2],
                    user_agent=split_by_quotes[5]
                ))
        self.size = size
        count_total = len(logs)
        count_per_endpoint = defaultdict(int)
        for log in logs:
            count_per_endpoint[log.url] += 1
        # Sort counts from largest to smallest
        count_per_endpoint = {
            k: v for k, v in sorted(
                count_per_endpoint.items(),
                key=lambda item: item[1], reverse=True
                )
        }
        return [{
            'title': TITLE,
            'description': f"Unique requests: {count_total}",
            'severity': 2,
            'timestamp': datetime.now(timezone.utc),
            'json': count_per_endpoint
        }]
