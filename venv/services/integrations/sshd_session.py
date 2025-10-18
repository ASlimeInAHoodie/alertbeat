from collections import defaultdict
from datetime import datetime, timezone
import os, json

#region CONSTANTS
LOG_FILE_PATH = '/var/log/auth.log'
DATA_STORAGE_PATH = './integration_data.json'

TITLE = "Your Daily Digest - SSH"

DTFORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

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
        date: datetime,
        hostname: str,
        process_name: str,
        process_id: int,
        message: str
    ):
        self.date: datetime = date
        self.hostname: str = hostname
        self.process_name: str = process_name
        self.process_id: int = process_id
        self.message: str = message

def sort_dict(dictionary: dict) -> dict:
    return {
        k: v for k, v in sorted(
            dictionary.items(),
            key=lambda item: item[1], reverse=True
            )
    }

class SSH_Failure_Count:
    def __init__(self):
        self.size = readSize()

    def process_line(self, line: str) -> Log|None:
        # Split the line on spaces
        _split_by_spaces = line.split()
        # Only process if it matches our logging standard
        if len(_split_by_spaces) < 4: return
        datetime_string = _split_by_spaces[0]
        hostname = _split_by_spaces[1]
        message = ' '.join(_split_by_spaces[3:])


        _process_info = _split_by_spaces[2].split('[')
        # Only process if process is supplied
        if len(_process_info)< 2: return
        process_name = _process_info[0]
        # Only process if a valid PID is supplied
        process_id = _process_info[1][:-2]
        if not process_id.isdigit(): return
        process_id = int(process_id)

        return Log(
            date=datetime.strptime(datetime_string, DTFORMAT),
            hostname=hostname,
            process_name=process_name,
            process_id=process_id,
            message=message
        )


    def query(self) -> dict|Exception|None:
        timenow: datetime = datetime.now(timezone.utc)

        try:
            size = getFileSize()
            if size < self.size: size = 0
            if self.size == size: return None
            # Else ... Return data
        except Exception as e:
            print(f"size: {e}")
            return e

        logs: list[Log] = []
        with open(LOG_FILE_PATH, 'r') as file:
            file.seek(self.size)
            for line in file:
                log: Log = self.process_line(line)
                if not log: continue
                logs.append(log)

        # Update size
        self.size = size

        # Process logs further:
        success_auths: list[str] = []
        failed_auths: list[str] = []
        invalid_accounts: list[str] = []

        for log in logs:
            # Only check logs with the process name sshd-session
            if log.process_name != "sshd-session": continue

            if log.message[:12] == "Invalid user":
                msg = log.message.split()
                # invalid_accounts.append(msg[2]+'@'+msg[4]) # Username@IP
                invalid_accounts.append(msg[2]) # Username (Too verbose otherwise)
                continue

            if log.message[:40] == "Connection closed by authenticating user":
                msg = log.message.split()
                failed_auths.append(msg[5]+'@'+msg[6]) # Username@IP
                continue

            if log.message[:8] == "Accepted":
                msg = log.message.split()
                success_auths.append(msg[3]+'@'+msg[5]) # Username@IP
                continue

        # Create alerts for return array
        alerts = []

        success_count_total = len(success_auths)
        failure_count_total = len(failed_auths)
        invalid_count_total = len(invalid_accounts)

        alerts.append({
            'title': TITLE,
            'description': """
                :warning: Accepted: {success_count}\n
                :x: Failed: {fail_count}\n
                :question: Invalid: {invalid_count}
                """.format(
                    success_count=success_count_total,
                    fail_count=failure_count_total,
                    invalid_count=invalid_count_total
                ),
            'severity': 2,
            'timestamp': timenow
        })


        if success_count_total > 0:
            # Calculate uniques
            unique_rows = defaultdict(int)
            for row in success_auths:
                    unique_rows[row] += 1
            unique_rows = sort_dict(unique_rows)
            alerts.append({
                'title': ':warning: Accepted SSH connections',
                'description': f"Successful connections: {success_count_total}",
                'severity': 3,
                'timestamp': timenow,
                'json': unique_rows
            })

        if failure_count_total > 0:
            # Calculate uniques
            unique_rows = defaultdict(int)
            for row in failed_auths:
                    unique_rows[row] += 1
            unique_rows = sort_dict(unique_rows)
            alerts.append({
                'title': ':x: Failed SSH connections',
                'description': f"Valid accounts failing to connect: {failure_count_total}",
                'severity': 2,
                'timestamp': timenow,
                'json': unique_rows
            })

        if invalid_count_total > 0:
            # Calculate uniques
            unique_rows = defaultdict(int)
            for row in invalid_accounts:
                    unique_rows[row] += 1
            unique_rows = sort_dict(unique_rows)
            alerts.append({
                'title': ':question: Invalid SSH Accounts',
                'description': f"Failed connections due to invalid accounts: {invalid_count_total}",
                'severity': 0,
                'timestamp': timenow,
                'json': unique_rows
            })

        return alerts
